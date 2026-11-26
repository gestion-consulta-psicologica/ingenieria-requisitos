from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable
from datetime import datetime

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.servicios.disponibilidad import consultar_bloques_reservables
from app.servicios.notificaciones import encolar_aviso_reserva
from app.tiempo import ZONA_POR_DEFECTO, ahora_utc, zona

ESTADO_PENDIENTE = "Pendiente de confirmación"


class PacienteNoRegistrado(Exception):
    """El RUT ingresado no corresponde a un paciente registrado."""


class BloqueNoEncontrado(Exception):
    """El bloque horario no existe."""


class BloqueNoDisponible(Exception):
    """El bloque ya tiene una reserva vigente o fue tomado por otro paciente."""


def normalizar_rut(rut: str) -> str:
    normalizado = re.sub(r"[.\- ]", "", rut).upper()
    return normalizado if re.fullmatch(r"[0-9]+[0-9K]", normalizado) else ""


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


def bloque_esta_disponible(
    conexion: sqlite3.Connection, bloque_id: int, *,
    ahora: datetime | None = None, zona_horaria: str = ZONA_POR_DEFECTO,
) -> bool:
    return bool(consultar_bloques_reservables(
        conexion, "b.id = ?", (bloque_id,), ahora=ahora, zona_horaria=zona_horaria,
    ))


def registrar_reserva(
    conexion: sqlite3.Connection, bloque_id: int, rut: str, *,
    ahora: datetime | None = None, configuracion: ConfiguracionCorreo | None = None,
    autorizar_paciente: Callable[[int], None] | None = None,
) -> dict:
    configuracion = configuracion or cargar_configuracion()
    conexion.execute("BEGIN IMMEDIATE")
    try:
        bloque = obtener_bloque(conexion, bloque_id)
        if bloque is None:
            raise BloqueNoEncontrado()
        if not bloque_esta_disponible(
            conexion, bloque_id, ahora=ahora, zona_horaria=configuracion.zona_horaria,
        ):
            raise BloqueNoDisponible()
        paciente = buscar_paciente_por_rut(conexion, rut)
        if paciente is None:
            raise PacienteNoRegistrado()
        if autorizar_paciente is not None:
            autorizar_paciente(paciente["id"])
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
                # Hora local con desfase, como fecha_respuesta y el historial.
                (ahora or ahora_utc()).astimezone(
                    zona(configuracion.zona_horaria)
                ).isoformat(timespec="seconds"),
                ESTADO_PENDIENTE,
            ),
        )
        reserva = conexion.execute(
            "SELECT * FROM reserva WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        encolar_aviso_reserva(
            conexion, dict(paciente), dict(bloque), dict(reserva),
            configuracion, ahora=ahora, confirmar_transaccion=False,
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise

    return {"reserva": reserva, "paciente": paciente, "bloque": bloque}


def obtener_reserva(
    conexion: sqlite3.Connection, reserva_id: int
) -> sqlite3.Row | None:
    return conexion.execute(
        """
        SELECT r.id AS reserva_id, r.fecha_registro, r.estado, r.version,
               p.nombre_completo AS paciente_nombre, p.rut AS paciente_rut,
               p.telefono AS paciente_telefono, p.correo AS paciente_correo,
               b.fecha, b.hora_inicio, b.hora_termino, b.modalidad,
               psi.nombre_psiquiatra
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        LEFT JOIN cuenta psi ON psi.id = b.psiquiatra_cuenta_id
        WHERE r.id = ?
        """,
        (reserva_id,),
    ).fetchone()
