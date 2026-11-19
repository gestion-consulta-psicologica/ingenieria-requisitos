from __future__ import annotations

import re
import sqlite3
from datetime import datetime

from app.servicios.disponibilidad import ESTADOS_VIGENTES

ESTADO_PENDIENTE = "Pendiente de confirmación"


class PacienteNoRegistrado(Exception):
    """El RUT ingresado no corresponde a un paciente registrado."""


class BloqueNoEncontrado(Exception):
    """El bloque horario no existe."""


class BloqueNoDisponible(Exception):
    """El bloque ya tiene una reserva vigente o fue tomado por otro paciente."""


def normalizar_rut(rut: str) -> str:
    return re.sub(r"[^0-9Kk]", "", rut).upper()


def buscar_paciente_por_rut(
    conexion: sqlite3.Connection, rut: str
) -> sqlite3.Row | None:
    normalizado = normalizar_rut(rut)
    if not normalizado:
        return None
    return conexion.execute(
        """
        SELECT *
        FROM paciente
        WHERE UPPER(
            REPLACE(REPLACE(REPLACE(rut, '.', ''), '-', ''), ' ', '')
        ) = ?
        """,
        (normalizado,),
    ).fetchone()


def obtener_bloque(
    conexion: sqlite3.Connection, bloque_id: int
) -> sqlite3.Row | None:
    return conexion.execute(
        "SELECT * FROM bloque_horario WHERE id = ?", (bloque_id,)
    ).fetchone()


def bloque_esta_disponible(conexion: sqlite3.Connection, bloque_id: int) -> bool:
    marcadores = ", ".join("?" for _ in ESTADOS_VIGENTES)
    fila = conexion.execute(
        f"""
        SELECT 1
        FROM reserva
        WHERE bloque_horario_id = ?
          AND estado IN ({marcadores})
        """,
        (bloque_id, *ESTADOS_VIGENTES),
    ).fetchone()
    return fila is None


def registrar_reserva(
    conexion: sqlite3.Connection, bloque_id: int, rut: str
) -> dict:
    paciente = buscar_paciente_por_rut(conexion, rut)
    if paciente is None:
        raise PacienteNoRegistrado()

    bloque = obtener_bloque(conexion, bloque_id)
    if bloque is None:
        raise BloqueNoEncontrado()

    if not bloque_esta_disponible(conexion, bloque_id):
        raise BloqueNoDisponible()

    try:
        cursor = conexion.execute(
            """
            INSERT INTO reserva (
                paciente_id, bloque_horario_id, fecha_registro, estado
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                paciente["id"],
                bloque_id,
                datetime.now().isoformat(timespec="seconds"),
                ESTADO_PENDIENTE,
            ),
        )
        conexion.commit()
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        raise BloqueNoDisponible() from error

    reserva = conexion.execute(
        "SELECT * FROM reserva WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return {"reserva": reserva, "paciente": paciente, "bloque": bloque}


def obtener_reserva(
    conexion: sqlite3.Connection, reserva_id: int
) -> sqlite3.Row | None:
    return conexion.execute(
        """
        SELECT r.id AS reserva_id, r.fecha_registro, r.estado, r.version,
               p.nombre_completo AS paciente_nombre, p.rut AS paciente_rut,
               p.telefono AS paciente_telefono, p.correo AS paciente_correo,
               b.fecha, b.hora_inicio, b.hora_termino, b.modalidad
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        WHERE r.id = ?
        """,
        (reserva_id,),
    ).fetchone()
