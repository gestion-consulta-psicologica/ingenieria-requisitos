from __future__ import annotations

import sqlite3

from app.servicios.atenciones import (
    ESTADO_PAGO_INCOMPLETO,
    ESTADO_PAGO_PAGADO,
    ESTADO_PAGO_PENDIENTE,
    PagoNoEncontrado,
    permite_registrar_comprobante,
)


class VerificacionPagoInvalida(ValueError):
    """Los comprobantes no corresponden a una transición de EST-02."""

_CONSULTA_ATENCION = """
    SELECT a.id AS atencion_id, a.reserva_id, a.tipo_atencion, a.monto,
           a.estado AS atencion_estado,
           p.nombre_completo AS paciente_nombre, p.rut AS paciente_rut,
           b.fecha, b.hora_inicio, b.hora_termino,
           pg.id AS pago_id, pg.monto_atencion, pg.monto_pagado,
           pg.estado AS pago_estado
    FROM atencion a
    JOIN pago pg ON pg.atencion_id = a.id
    JOIN reserva r ON r.id = a.reserva_id
    JOIN paciente p ON p.id = r.paciente_id
    JOIN bloque_horario b ON b.id = r.bloque_horario_id
"""


def _fila_a_detalle(fila: sqlite3.Row) -> dict:
    return {
        "reserva_id": fila["reserva_id"],
        "atencion": {
            "id": fila["atencion_id"],
            "tipo_atencion": fila["tipo_atencion"],
            "monto": fila["monto"],
            "estado": fila["atencion_estado"],
        },
        "paciente": {
            "nombre_completo": fila["paciente_nombre"],
            "rut": fila["paciente_rut"],
        },
        "bloque": {
            "fecha": fila["fecha"],
            "hora_inicio": fila["hora_inicio"],
            "hora_termino": fila["hora_termino"],
        },
        "pago": {
            "id": fila["pago_id"],
            "monto_atencion": fila["monto_atencion"],
            "monto_pagado": fila["monto_pagado"],
            "estado": fila["pago_estado"],
        },
        "comprobantes": [],
    }


def listar_atenciones_con_pago_pendiente(
    conexion: sqlite3.Connection, *, incluir_incompletos: bool = False,
) -> list[dict]:
    filas = conexion.execute(
        _CONSULTA_ATENCION
        + """
        WHERE pg.estado = ? OR (? AND pg.estado = ?)
        ORDER BY b.fecha, b.hora_inicio, a.id
        """,
        (ESTADO_PAGO_PENDIENTE, incluir_incompletos, ESTADO_PAGO_INCOMPLETO),
    ).fetchall()
    return [_fila_a_detalle(fila) for fila in filas]


def obtener_pago_de_atencion(
    conexion: sqlite3.Connection, atencion_id: int, *,
    incluir_verificacion: bool = False,
) -> dict | None:
    fila = conexion.execute(
        _CONSULTA_ATENCION + " WHERE a.id = ?",
        (atencion_id,),
    ).fetchone()
    if fila is None:
        return None

    detalle = _fila_a_detalle(fila)
    detalle["comprobantes"] = [
        dict(comprobante)
        for comprobante in conexion.execute(
            """
            SELECT id, monto, fecha_transferencia, cuenta_destino, verificado
            FROM comprobante_transferencia
            WHERE pago_id = ?
            ORDER BY fecha_transferencia, id
            """,
            (fila["pago_id"],),
        )
    ]
    if not incluir_verificacion:
        for comprobante in detalle["comprobantes"]:
            del comprobante["verificado"]
    return detalle


def verificar_pago(
    conexion: sqlite3.Connection, atencion_id: int, comprobantes: list[int],
    *, estado_elegido: str,
) -> None:
    seleccion = set(comprobantes)
    conexion.execute("BEGIN IMMEDIATE")
    try:
        detalle = obtener_pago_de_atencion(
            conexion, atencion_id, incluir_verificacion=True,
        )
        if detalle is None:
            raise PagoNoEncontrado("No se encontró la atención o su pago.")
        pago = detalle["pago"]
        if not permite_registrar_comprobante(pago["estado"]):
            raise VerificacionPagoInvalida("El estado actual no permite registrar otra verificación.")

        disponibles = {
            c["id"]: c["monto"] for c in detalle["comprobantes"] if not c["verificado"]
        }
        if not seleccion or not seleccion <= disponibles.keys():
            raise VerificacionPagoInvalida("Selecciona comprobantes de este pago que aún no estén verificados.")
        total = pago["monto_pagado"] + sum(disponibles[id_] for id_ in seleccion)
        if total > pago["monto_atencion"]:
            raise VerificacionPagoInvalida("El total seleccionado supera el monto de la atención.")
        estado = ESTADO_PAGO_PAGADO if total == pago["monto_atencion"] else ESTADO_PAGO_INCOMPLETO
        if estado_elegido != estado:
            raise VerificacionPagoInvalida(
                f"El monto comprobado corresponde al estado «{estado}»."
            )
        conexion.executemany(
            "UPDATE comprobante_transferencia SET verificado = 1 WHERE id = ?",
            [(id_,) for id_ in seleccion],
        )
        conexion.execute(
            "UPDATE pago SET monto_pagado = ?, estado = ? WHERE id = ?",
            (total, estado, pago["id"]),
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
