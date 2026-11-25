from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime

from app.tiempo import desde_iso_utc, iso_utc
from app.servicios.cola_correo import solicitud_enviada

ACCION_CONFIRMAR = "confirmar"
ACCION_CANCELAR = "cancelar"
ACCIONES = (ACCION_CONFIRMAR, ACCION_CANCELAR)


class TokenInvalido(Exception):
    """El token no existe."""


class TokenUsado(Exception):
    """El token ya fue utilizado."""


class TokenVencido(Exception):
    """El token superó su fecha de expiración."""


class TokenAccionInvalida(Exception):
    """El token no corresponde a la acción solicitada."""


class TokenSolicitudInvalida(Exception):
    """La solicitud asociada al token ya no admite respuesta."""


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_tokens(
    conexion: sqlite3.Connection,
    solicitud_id: int,
    expira_en: datetime,
    creado_en: datetime | None = None,
) -> dict[str, str]:
    """Crea un token por acción. Devuelve los tokens en claro una sola vez.

    Se llama dentro de la transacción que registra la solicitud; la base de
    datos guarda únicamente el hash.
    """
    creado = iso_utc(creado_en)
    expira = iso_utc(expira_en)
    tokens: dict[str, str] = {}
    for accion in ACCIONES:
        token = generar_token()
        conexion.execute(
            """
            INSERT INTO token_confirmacion (
                solicitud_id, accion, token_hash, creado_en, expira_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (solicitud_id, accion, hash_token(token), creado, expira),
        )
        tokens[accion] = token
    return tokens


def buscar_token(
    conexion: sqlite3.Connection, token: str, ahora: datetime
) -> sqlite3.Row:
    fila = conexion.execute(
        """
        SELECT t.*, s.reserva_id, s.estado AS solicitud_estado,
               s.tipo AS solicitud_tipo, r.estado AS reserva_estado
        FROM token_confirmacion t
        JOIN solicitud_confirmacion s ON s.id = t.solicitud_id
        JOIN reserva r ON r.id = s.reserva_id
        WHERE t.token_hash = ?
        """,
        (hash_token(token),),
    ).fetchone()
    if fila is None:
        raise TokenInvalido("El enlace de confirmación no es válido.")
    if fila["usado_en"] is not None:
        raise TokenUsado("Este enlace ya fue utilizado.")
    if desde_iso_utc(fila["expira_en"]) <= ahora:
        raise TokenVencido("Este enlace venció.")
    if (
        fila["solicitud_estado"] != "pendiente"
        or fila["reserva_estado"] != "Pendiente de confirmación"
        or not solicitud_enviada(conexion, fila["solicitud_id"])
    ):
        raise TokenSolicitudInvalida(
            "La solicitud de confirmación ya no admite respuesta."
        )
    return fila
