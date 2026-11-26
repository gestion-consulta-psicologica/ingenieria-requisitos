from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime

from app.configuracion import monto_atencion_clp
from app.servicios.notificaciones import MONTO_CARGO
from app.tiempo import ZONA_POR_DEFECTO, ahora_utc, programado

logger = logging.getLogger(__name__)

ESTADO_RESERVA_CONFIRMADA = "Confirmada"
ESTADO_RESERVA_FINALIZADA = "Finalizada"
ESTADO_PAGO_PENDIENTE = "Pendiente"
ESTADO_PAGO_INCOMPLETO = "Pago incompleto"
ESTADO_PAGO_PAGADO = "Pagado"
ESTADOS_PAGO_CON_REGISTRO = {
    ESTADO_PAGO_PENDIENTE,
    ESTADO_PAGO_INCOMPLETO,
}


class AtencionNoEncontrada(Exception):
    """La atención indicada no existe."""


class PagoNoEncontrado(Exception):
    """La atención no tiene un pago registrado (datos inconsistentes)."""


class PagoYaPagado(Exception):
    """El pago ya fue registrado como pagado."""


class EstadoPagoNoPermiteRegistro(Exception):
    """El estado actual del pago no admite nuevos comprobantes."""


class AsistenciaInvalida(ValueError):
    """La atención no admite el resultado de asistencia solicitado."""


class DatosComprobanteInvalidos(ValueError):
    """Los datos ingresados para el comprobante no son válidos."""

    def __init__(self, mensaje: str, errores: dict[str, str] | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or {}


def permite_registrar_comprobante(estado: str | None) -> bool:
    return estado in ESTADOS_PAGO_CON_REGISTRO


def crear_atenciones_vencidas(
    conexion: sqlite3.Connection,
    ahora: datetime | None = None,
    zona_horaria: str = ZONA_POR_DEFECTO,
    *,
    monto_clp: int | None = None,
) -> list[int]:
    """Origina atención y pago para reservas confirmadas ya comenzadas.

    La restricción UNIQUE de ``atencion.reserva_id`` y la transacción por
    reserva hacen que la operación sea idempotente.
    """

    ahora = ahora or ahora_utc()
    monto = monto_atencion_clp() if monto_clp is None else monto_clp
    filas = list(
        conexion.execute(
            """
            SELECT r.id AS reserva_id, r.version, r.bloque_horario_id,
                   b.fecha, b.hora_inicio, b.modalidad
            FROM reserva r
            JOIN bloque_horario b ON b.id = r.bloque_horario_id
            WHERE r.estado = ? AND b.psiquiatra_cuenta_id IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM atencion a WHERE a.reserva_id = r.id
              )
            ORDER BY b.fecha, b.hora_inicio, r.id
            """,
            (ESTADO_RESERVA_CONFIRMADA,),
        )
    )

    creadas: list[int] = []
    for fila in filas:
        inicio = programado(fila["fecha"], fila["hora_inicio"], zona_horaria)
        if ahora < inicio:
            continue
        conexion.execute("BEGIN IMMEDIATE")
        try:
            transicion = conexion.execute(
                """
                UPDATE reserva
                SET estado = ?
                WHERE id = ? AND estado = ? AND version = ?
                  AND bloque_horario_id = ?
                  AND NOT EXISTS (
                      SELECT 1 FROM atencion a WHERE a.reserva_id = reserva.id
                  )
                  AND EXISTS (
                      SELECT 1 FROM bloque_horario b
                      WHERE b.id = reserva.bloque_horario_id
                        AND b.fecha = ? AND b.hora_inicio = ? AND b.modalidad = ?
                  )
                """,
                (
                    ESTADO_RESERVA_FINALIZADA, fila["reserva_id"],
                    ESTADO_RESERVA_CONFIRMADA, fila["version"],
                    fila["bloque_horario_id"], fila["fecha"],
                    fila["hora_inicio"], fila["modalidad"],
                ),
            )
            if transicion.rowcount != 1:
                conexion.rollback()
                continue
            cursor = conexion.execute(
                """
                INSERT INTO atencion (
                    reserva_id, tipo_atencion, monto, estado
                )
                VALUES (?, ?, ?, 'programada')
                """,
                (fila["reserva_id"], fila["modalidad"], monto),
            )
            atencion_id = int(cursor.lastrowid)
            conexion.execute(
                """
                INSERT INTO pago (
                    atencion_id, monto_atencion, monto_pagado, estado
                )
                VALUES (?, ?, 0, ?)
                """,
                (atencion_id, monto, ESTADO_PAGO_PENDIENTE),
            )
            conexion.commit()
        except sqlite3.IntegrityError:
            conexion.rollback()
            logger.exception("No se pudo originar la atención de la reserva %s.", fila["reserva_id"])
            continue
        except Exception:
            conexion.rollback()
            raise
        creadas.append(atencion_id)
    return creadas


def obtener_atencion_de_reserva(
    conexion: sqlite3.Connection, reserva_id: int
) -> dict | None:
    fila = conexion.execute(
        """
        SELECT a.id AS atencion_id, a.estado AS atencion_estado,
               p.id AS pago_id, p.estado AS pago_estado
        FROM atencion a
        JOIN pago p ON p.atencion_id = a.id
        WHERE a.reserva_id = ?
        """,
        (reserva_id,),
    ).fetchone()
    if fila is None:
        return None
    return {
        "atencion_id": fila["atencion_id"],
        "atencion_estado": fila["atencion_estado"],
        "pago_id": fila["pago_id"],
        "pago_estado": fila["pago_estado"],
    }


def registrar_asistencia(
    conexion: sqlite3.Connection, atencion_id: int, estado: str, justificacion: str,
    *, cifrador=None,
) -> None:
    justificacion = justificacion.strip()
    if estado not in ("realizada", "inasistencia", "inasistencia justificada"):
        raise AsistenciaInvalida("Selecciona un resultado de asistencia válido.")
    if estado == "inasistencia justificada" and not justificacion:
        raise AsistenciaInvalida("Ingresa la justificación de la inasistencia.")

    conexion.execute("BEGIN IMMEDIATE")
    try:
        atencion = conexion.execute(
            """
            SELECT a.estado, r.paciente_id, b.fecha
            FROM atencion a
            JOIN reserva r ON r.id = a.reserva_id
            JOIN bloque_horario b ON b.id = r.bloque_horario_id
            WHERE a.id = ?
            """,
            (atencion_id,),
        ).fetchone()
        if atencion is None:
            raise AtencionNoEncontrada("No se encontró la atención.")
        if atencion["estado"] != "programada":
            raise AsistenciaInvalida("La atención ya tiene un resultado registrado.")
        conexion.execute(
            "UPDATE atencion SET estado = ?, justificacion_inasistencia = ? WHERE id = ?",
            (
                estado,
                (cifrador.cifrar(justificacion) if cifrador else justificacion)
                if estado == "inasistencia justificada" else None,
                atencion_id,
            ),
        )
        if estado == "inasistencia":
            conexion.execute(
                """
                INSERT INTO cargo (paciente_id, atencion_id, monto, motivo, fecha)
                VALUES (?, ?, ?, 'inasistencia', ?)
                """,
                (atencion["paciente_id"], atencion_id, MONTO_CARGO, atencion["fecha"]),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise


def registrar_comprobante(
    conexion: sqlite3.Connection,
    atencion_id: int,
    monto: int | str,
    fecha_transferencia: str | date,
    cuenta_destino: str,
) -> dict:
    fila = conexion.execute(
        """
        SELECT a.id AS atencion_id, p.id AS pago_id, p.estado AS pago_estado
        FROM atencion a
        LEFT JOIN pago p ON p.atencion_id = a.id
        WHERE a.id = ?
        """,
        (atencion_id,),
    ).fetchone()
    if fila is None:
        raise AtencionNoEncontrada("No se encontró la atención.")
    if fila["pago_id"] is None:
        raise PagoNoEncontrado("La atención no tiene un pago asociado.")
    if fila["pago_estado"] == ESTADO_PAGO_PAGADO:
        raise PagoYaPagado(
            "El pago ya está pagado; no se puede registrar otro comprobante."
        )
    if not permite_registrar_comprobante(fila["pago_estado"]):
        raise EstadoPagoNoPermiteRegistro(
            "El estado actual del pago no permite registrar comprobantes."
        )

    monto_normalizado = _normalizar_monto(monto)
    fecha_normalizada = _normalizar_fecha(fecha_transferencia)
    cuenta_normalizada = (cuenta_destino or "").strip()

    errores: dict[str, str] = {}
    if monto_normalizado is None:
        errores["monto"] = "Ingresa un monto válido mayor que cero."
    if fecha_normalizada is None:
        errores["fecha_transferencia"] = (
            "Ingresa una fecha de transferencia válida."
        )
    if not cuenta_normalizada:
        errores["cuenta_destino"] = "Ingresa la cuenta de destino."
    if errores:
        raise DatosComprobanteInvalidos(
            "Revisa los datos del comprobante.",
            errores,
        )

    cursor = conexion.execute(
        """
        INSERT INTO comprobante_transferencia (
            pago_id, monto, fecha_transferencia, cuenta_destino
        )
        SELECT id, ?, ?, ? FROM pago
        WHERE id = ? AND estado IN (?, ?)
        """,
        (
            monto_normalizado,
            fecha_normalizada.isoformat(),
            cuenta_normalizada,
            fila["pago_id"],
            ESTADO_PAGO_PENDIENTE,
            ESTADO_PAGO_INCOMPLETO,
        ),
    )
    if cursor.rowcount != 1:
        conexion.rollback()
        raise EstadoPagoNoPermiteRegistro("El estado del pago cambió antes de registrar el comprobante.")
    conexion.commit()
    return {
        "id": int(cursor.lastrowid),
        "pago_id": fila["pago_id"],
        "monto": monto_normalizado,
        "fecha_transferencia": fecha_normalizada.isoformat(),
        "cuenta_destino": cuenta_normalizada,
    }


def _normalizar_monto(valor: int | str) -> int | None:
    if isinstance(valor, bool):
        return None
    # Acepta el formato chileno escrito por el paciente: 30000, 30.000, $30.000.
    texto = str(valor).strip().removeprefix("$").replace(".", "").replace(" ", "")
    if not texto or not texto.isdigit():
        return None
    monto = int(texto)
    return monto if monto > 0 else None


def _normalizar_fecha(valor: str | date) -> date | None:
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor).strip())
    except ValueError:
        return None
