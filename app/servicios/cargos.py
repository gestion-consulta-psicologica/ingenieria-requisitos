"""HU-06 (extensión del 2026-11-25) — Pagar un cargo de $5.000.

Un Cargo nace en HU-03 (no confirmar / responder «no asistiré»), HU-04
(cancelación del paciente) o HU-08 (inasistencia sin justificación). Se paga
igual que la atención: el paciente registra comprobantes de transferencia
(como HU-05A) y la psicóloga los verifica (como HU-06, siguiendo EST-02).
"""

from __future__ import annotations

import sqlite3

from app.servicios.atenciones import (
    DatosComprobanteInvalidos,
    ESTADO_PAGO_INCOMPLETO,
    ESTADO_PAGO_PAGADO,
    ESTADO_PAGO_PENDIENTE,
    _normalizar_fecha,
    _normalizar_monto,
)

ESTADOS_CON_SALDO = (ESTADO_PAGO_PENDIENTE, ESTADO_PAGO_INCOMPLETO)
MOTIVOS = {
    "sin confirmar": "No confirmó la hora",
    "cancelación": "Cancelación de la hora",
    "inasistencia": "Inasistencia sin justificación",
}


class CargoNoEncontrado(LookupError):
    """El cargo indicado no existe."""


class CargoYaPagado(ValueError):
    """El cargo ya está pagado y no admite comprobantes ni verificaciones."""


class VerificacionCargoInvalida(ValueError):
    """Los comprobantes seleccionados no corresponden a una transición válida."""


_CONSULTA = """
    SELECT c.id, c.paciente_id, c.reserva_id, c.atencion_id, c.monto, c.monto_pagado,
           c.motivo, c.fecha, c.estado,
           p.nombre_completo AS paciente_nombre, p.rut AS paciente_rut,
           COALESCE(c.reserva_id, a.reserva_id) AS reserva_origen,
           b.fecha AS bloque_fecha, b.hora_inicio AS bloque_hora_inicio
    FROM cargo c
    JOIN paciente p ON p.id = c.paciente_id
    LEFT JOIN atencion a ON a.id = c.atencion_id
    LEFT JOIN reserva r ON r.id = COALESCE(c.reserva_id, a.reserva_id)
    LEFT JOIN bloque_horario b ON b.id = r.bloque_horario_id
"""


def _a_dict(fila: sqlite3.Row) -> dict:
    cargo = dict(fila)
    cargo["motivo_texto"] = MOTIVOS.get(cargo["motivo"], cargo["motivo"])
    cargo["saldo"] = cargo["monto"] - cargo["monto_pagado"]
    cargo["admite_pago"] = cargo["estado"] in ESTADOS_CON_SALDO
    return cargo


def obtener_cargo(conexion: sqlite3.Connection, cargo_id: int) -> dict | None:
    fila = conexion.execute(_CONSULTA + " WHERE c.id = ?", (cargo_id,)).fetchone()
    if fila is None:
        return None
    cargo = _a_dict(fila)
    cargo["comprobantes"] = [
        dict(comprobante)
        for comprobante in conexion.execute(
            """
            SELECT id, monto, fecha_transferencia, cuenta_destino, verificado
            FROM comprobante_cargo WHERE cargo_id = ?
            ORDER BY fecha_transferencia, id
            """,
            (cargo_id,),
        )
    ]
    return cargo


def listar_cargos_de_pacientes(
    conexion: sqlite3.Connection, pacientes: set[int],
) -> list[dict]:
    if not pacientes:
        return []
    marcas = ", ".join("?" for _ in pacientes)
    filas = conexion.execute(
        _CONSULTA + f" WHERE c.paciente_id IN ({marcas}) ORDER BY c.fecha DESC, c.id DESC",
        tuple(pacientes),
    ).fetchall()
    return [_a_dict(fila) for fila in filas]


def listar_cargos_con_saldo(conexion: sqlite3.Connection) -> list[dict]:
    marcas = ", ".join("?" for _ in ESTADOS_CON_SALDO)
    filas = conexion.execute(
        _CONSULTA + f" WHERE c.estado IN ({marcas}) ORDER BY c.fecha, c.id",
        ESTADOS_CON_SALDO,
    ).fetchall()
    return [_a_dict(fila) for fila in filas]


def registrar_comprobante_cargo(
    conexion: sqlite3.Connection, cargo_id: int, monto, fecha_transferencia, cuenta_destino: str,
) -> dict:
    """El paciente registra un comprobante; el estado del cargo no cambia (como HU-05A)."""
    cargo = conexion.execute("SELECT estado FROM cargo WHERE id = ?", (cargo_id,)).fetchone()
    if cargo is None:
        raise CargoNoEncontrado("No se encontró el cargo.")
    if cargo["estado"] == ESTADO_PAGO_PAGADO:
        raise CargoYaPagado("El cargo ya está pagado; no se puede registrar otro comprobante.")

    monto_normalizado = _normalizar_monto(monto)
    fecha_normalizada = _normalizar_fecha(fecha_transferencia)
    cuenta = (cuenta_destino or "").strip()
    errores: dict[str, str] = {}
    if monto_normalizado is None:
        errores["monto"] = "Ingresa un monto válido mayor que cero."
    if fecha_normalizada is None:
        errores["fecha_transferencia"] = "Ingresa una fecha de transferencia válida."
    if not cuenta:
        errores["cuenta_destino"] = "Ingresa la cuenta de destino."
    if errores:
        raise DatosComprobanteInvalidos("Revisa los datos del comprobante.", errores)

    marcas = ", ".join("?" for _ in ESTADOS_CON_SALDO)
    cursor = conexion.execute(
        f"""
        INSERT INTO comprobante_cargo (cargo_id, monto, fecha_transferencia, cuenta_destino)
        SELECT id, ?, ?, ? FROM cargo WHERE id = ? AND estado IN ({marcas})
        """,
        (monto_normalizado, fecha_normalizada.isoformat(), cuenta, cargo_id, *ESTADOS_CON_SALDO),
    )
    if cursor.rowcount != 1:
        conexion.rollback()
        raise CargoYaPagado("El estado del cargo cambió antes de registrar el comprobante.")
    conexion.commit()
    return {"id": int(cursor.lastrowid), "monto": monto_normalizado}


def verificar_pago_cargo(
    conexion: sqlite3.Connection, cargo_id: int, comprobantes: list[int], *, estado_elegido: str,
) -> dict:
    """La psicóloga verifica comprobantes y registra el estado (mismas reglas que HU-06)."""
    seleccion = set(comprobantes)
    conexion.execute("BEGIN IMMEDIATE")
    try:
        cargo = obtener_cargo(conexion, cargo_id)
        if cargo is None:
            raise CargoNoEncontrado("No se encontró el cargo.")
        if not cargo["admite_pago"]:
            raise VerificacionCargoInvalida("El cargo ya está pagado.")
        disponibles = {c["id"]: c["monto"] for c in cargo["comprobantes"] if not c["verificado"]}
        if not seleccion or not seleccion <= disponibles.keys():
            raise VerificacionCargoInvalida(
                "Selecciona comprobantes de este cargo que aún no estén verificados."
            )
        total = cargo["monto_pagado"] + sum(disponibles[i] for i in seleccion)
        if total > cargo["monto"]:
            raise VerificacionCargoInvalida("El total seleccionado supera el monto del cargo.")
        estado = ESTADO_PAGO_PAGADO if total == cargo["monto"] else ESTADO_PAGO_INCOMPLETO
        if estado_elegido != estado:
            raise VerificacionCargoInvalida(f"El monto comprobado corresponde al estado «{estado}».")
        conexion.executemany(
            "UPDATE comprobante_cargo SET verificado = 1 WHERE id = ?", [(i,) for i in seleccion],
        )
        conexion.execute(
            "UPDATE cargo SET monto_pagado = ?, estado = ? WHERE id = ?", (total, estado, cargo_id),
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    return {"estado": estado, "monto_pagado": total}
