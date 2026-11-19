from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.servicios.reserva import buscar_paciente_por_rut, normalizar_rut


@dataclass(frozen=True)
class DatosPaciente:
    nombre_completo: str
    rut: str
    telefono: str | None
    correo: str | None


class DatosPacienteInvalidos(Exception):
    """Faltan datos obligatorios para registrar al Paciente."""

    def __init__(self, faltantes: list[str]):
        self.faltantes = faltantes
        super().__init__("Falta completar: " + ", ".join(faltantes))


def _limpiar(valor: str | None) -> str:
    return (valor or "").strip()


def preparar_datos(
    nombre_completo: str | None,
    rut: str | None,
    telefono: str | None,
    correo: str | None,
) -> DatosPaciente:
    return DatosPaciente(
        nombre_completo=_limpiar(nombre_completo),
        rut=_limpiar(rut),
        telefono=_limpiar(telefono) or None,
        correo=_limpiar(correo) or None,
    )


def validar_datos(datos: DatosPaciente) -> list[str]:
    faltantes: list[str] = []
    if not datos.nombre_completo:
        faltantes.append("nombre completo")
    if not normalizar_rut(datos.rut):
        faltantes.append("RUT")
    if datos.telefono is None and datos.correo is None:
        faltantes.append("un medio de contacto (teléfono o correo)")
    return faltantes


def registrar_paciente(
    conexion: sqlite3.Connection,
    nombre_completo: str | None,
    rut: str | None,
    telefono: str | None = "",
    correo: str | None = "",
) -> dict:
    datos = preparar_datos(nombre_completo, rut, telefono, correo)

    existente = buscar_paciente_por_rut(conexion, datos.rut)
    if existente is not None:
        return {"paciente": existente, "creado": False}

    faltantes = validar_datos(datos)
    if faltantes:
        raise DatosPacienteInvalidos(faltantes)

    try:
        cursor = conexion.execute(
            """
            INSERT INTO paciente (nombre_completo, rut, telefono, correo)
            VALUES (?, ?, ?, ?)
            """,
            (datos.nombre_completo, datos.rut, datos.telefono, datos.correo),
        )
        conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback()
        existente = buscar_paciente_por_rut(conexion, datos.rut)
        if existente is None:
            raise
        return {"paciente": existente, "creado": False}

    paciente = conexion.execute(
        "SELECT * FROM paciente WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return {"paciente": paciente, "creado": True}
