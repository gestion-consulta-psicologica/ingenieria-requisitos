from __future__ import annotations

import sqlite3
from datetime import datetime

from app.tiempo import desde_iso_utc, iso_utc

TIPO_AVISO_RESERVA = "aviso_reserva"
TIPO_SOLICITUD = "solicitud_confirmacion"
TIPO_AVISO_CARGO = "aviso_cargo"

ESTADO_PENDIENTE = "pendiente"
ESTADO_ENVIANDO = "enviando"
ESTADO_ENVIADO = "enviado"
ESTADO_FALLIDO = "fallido"
ESTADO_OMITIDO = "omitido"
ESTADO_CANCELADO = "cancelado"


def encolar(
    conexion: sqlite3.Connection,
    *,
    clave: str,
    tipo: str,
    asunto: str,
    cuerpo_texto: str,
    cuerpo_html: str | None,
    destinatario: str | None,
    reserva_id: int | None,
    solicitud_id: int | None,
    creado_en: datetime,
    max_intentos: int,
) -> sqlite3.Row:
    """Encola un correo de forma idempotente dentro de la transacción actual."""
    creado = iso_utc(creado_en)
    estado = ESTADO_PENDIENTE if destinatario else ESTADO_OMITIDO
    error = None if destinatario else "El paciente no tiene correo electrónico registrado."
    conexion.execute(
        """
        INSERT OR IGNORE INTO correo_pendiente (
            clave_idempotencia, tipo, reserva_id, solicitud_id, destinatario,
            asunto, cuerpo_texto, cuerpo_html, estado, intentos, max_intentos,
            proximo_intento, ultimo_error, creado_en, actualizado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
        """,
        (
            clave,
            tipo,
            reserva_id,
            solicitud_id,
            destinatario,
            asunto,
            cuerpo_texto,
            cuerpo_html,
            estado,
            max_intentos,
            creado,
            error,
            creado,
            creado,
        ),
    )
    return conexion.execute(
        "SELECT * FROM correo_pendiente WHERE clave_idempotencia = ?", (clave,)
    ).fetchone()


def solicitud_enviada(conexion: sqlite3.Connection, solicitud_id: int) -> bool:
    return conexion.execute(
        "SELECT 1 FROM correo_pendiente WHERE solicitud_id = ? AND estado = ?",
        (solicitud_id, ESTADO_ENVIADO),
    ).fetchone() is not None


def cancelar_pendientes_de_solicitud(
    conexion: sqlite3.Connection, solicitud_id: int, ahora: datetime,
    *, motivo: str = "Reemplazado por el recordatorio.",
) -> int:
    cursor = conexion.execute(
        """
        UPDATE correo_pendiente
        SET estado = ?, actualizado_en = ?,
            ultimo_error = ?
        WHERE solicitud_id = ? AND estado = ?
        """,
        (ESTADO_CANCELADO, iso_utc(ahora), motivo, solicitud_id, ESTADO_PENDIENTE),
    )
    return cursor.rowcount


def recuperar_enviando(
    conexion: sqlite3.Connection, ahora: datetime, timeout_segundos: int
) -> int:
    limite = iso_utc(
        datetime.fromtimestamp(
            ahora.timestamp() - timeout_segundos, tz=ahora.tzinfo
        )
    )
    cursor = conexion.execute(
        """
        UPDATE correo_pendiente
        SET estado = ?, actualizado_en = ?,
            ultimo_error = 'Recuperado tras reinicio del planificador.'
        WHERE estado = ? AND actualizado_en <= ?
        """,
        (ESTADO_PENDIENTE, iso_utc(ahora), ESTADO_ENVIANDO, limite),
    )
    conexion.commit()
    return cursor.rowcount


def reclamar_siguiente(
    conexion: sqlite3.Connection, ahora: datetime
) -> sqlite3.Row | None:
    conexion.execute("BEGIN IMMEDIATE")
    try:
        fila = conexion.execute(
            """
            SELECT *
            FROM correo_pendiente
            WHERE estado = ? AND proximo_intento <= ?
            ORDER BY proximo_intento, id
            LIMIT 1
            """,
            (ESTADO_PENDIENTE, iso_utc(ahora)),
        ).fetchone()
        if fila is None:
            conexion.rollback()
            return None
        cursor = conexion.execute(
            """
            UPDATE correo_pendiente
            SET estado = ?, actualizado_en = ?
            WHERE id = ? AND estado = ?
            """,
            (ESTADO_ENVIANDO, iso_utc(ahora), fila["id"], ESTADO_PENDIENTE),
        )
        if cursor.rowcount != 1:
            conexion.rollback()
            return None
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    return conexion.execute(
        "SELECT * FROM correo_pendiente WHERE id = ?", (fila["id"],)
    ).fetchone()


def marcar_enviado(
    conexion: sqlite3.Connection,
    correo_id: int,
    id_mensaje: str,
    ahora: datetime,
) -> None:
    conexion.execute(
        """
        UPDATE correo_pendiente
        SET estado = ?, enviado_en = ?, actualizado_en = ?,
            id_mensaje = ?, ultimo_error = NULL
        WHERE id = ?
        """,
        (ESTADO_ENVIADO, iso_utc(ahora), iso_utc(ahora), id_mensaje, correo_id),
    )
    conexion.commit()


def marcar_reintento(
    conexion: sqlite3.Connection,
    correo_id: int,
    error: str,
    proximo_intento: datetime,
    ahora: datetime,
) -> None:
    conexion.execute(
        """
        UPDATE correo_pendiente
        SET estado = ?, intentos = intentos + 1, proximo_intento = ?,
            ultimo_error = ?, actualizado_en = ?
        WHERE id = ?
        """,
        (
            ESTADO_PENDIENTE,
            iso_utc(proximo_intento),
            error,
            iso_utc(ahora),
            correo_id,
        ),
    )
    conexion.commit()


def marcar_fallido(
    conexion: sqlite3.Connection, correo_id: int, error: str, ahora: datetime
) -> None:
    conexion.execute(
        """
        UPDATE correo_pendiente
        SET estado = ?, intentos = intentos + 1, ultimo_error = ?,
            actualizado_en = ?
        WHERE id = ?
        """,
        (ESTADO_FALLIDO, error, iso_utc(ahora), correo_id),
    )
    conexion.commit()


def listar_por_reserva(
    conexion: sqlite3.Connection, reserva_id: int
) -> list[sqlite3.Row]:
    return list(
        conexion.execute(
            """
            SELECT *
            FROM correo_pendiente
            WHERE reserva_id = ?
            ORDER BY id
            """,
            (reserva_id,),
        )
    )


def contar_por_estado(conexion: sqlite3.Connection, estado: str) -> int:
    return conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE estado = ?", (estado,)
    ).fetchone()[0]


def proximo_intento_texto(fila: sqlite3.Row) -> str:
    return desde_iso_utc(fila["proximo_intento"]).isoformat(timespec="seconds")
