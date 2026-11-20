from __future__ import annotations

import sqlite3

ESTADO_PAGO_PENDIENTE = "Pendiente"

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
    conexion: sqlite3.Connection,
) -> list[dict]:
    filas = conexion.execute(
        _CONSULTA_ATENCION
        + """
        WHERE pg.estado = ?
        ORDER BY b.fecha, b.hora_inicio, a.id
        """,
        (ESTADO_PAGO_PENDIENTE,),
    ).fetchall()
    return [_fila_a_detalle(fila) for fila in filas]


def obtener_pago_de_atencion(
    conexion: sqlite3.Connection, atencion_id: int
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
            SELECT id, monto, fecha_transferencia, cuenta_destino
            FROM comprobante_transferencia
            WHERE pago_id = ?
            ORDER BY fecha_transferencia, id
            """,
            (fila["pago_id"],),
        )
    ]
    return detalle
