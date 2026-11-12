from __future__ import annotations

import sqlite3
from datetime import date, timedelta

# Regla de vigencia de EST-01, confirmada en la ficha de HU-01.
ESTADOS_VIGENTES = ("Pendiente de confirmación", "Confirmada")


def rango_semana(fecha: date) -> tuple[date, date]:
    inicio = fecha - timedelta(days=fecha.weekday())
    return inicio, inicio + timedelta(days=6)


def _marcadores(cantidad: int) -> str:
    return ", ".join("?" for _ in range(cantidad))


def _consulta_bloques_libres(condicion_fecha: str) -> str:
    return f"""
        SELECT b.id, b.fecha, b.hora_inicio, b.hora_termino, b.modalidad
        FROM bloque_horario b
        WHERE {condicion_fecha}
          AND NOT EXISTS (
              SELECT 1
              FROM reserva r
              WHERE r.bloque_horario_id = b.id
                AND r.estado IN ({_marcadores(len(ESTADOS_VIGENTES))})
          )
    """


def obtener_disponibilidad_semana(
    conexion: sqlite3.Connection, fecha_semana: date
) -> list[dict]:
    inicio, fin = rango_semana(fecha_semana)
    filas = conexion.execute(
        _consulta_bloques_libres("b.fecha BETWEEN ? AND ?")
        + " ORDER BY b.fecha, b.hora_inicio",
        (inicio.isoformat(), fin.isoformat(), *ESTADOS_VIGENTES),
    ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_proximo_bloque(
    conexion: sqlite3.Connection, fecha_semana: date
) -> date | None:
    _, fin = rango_semana(fecha_semana)
    fila = conexion.execute(
        _consulta_bloques_libres("b.fecha > ?")
        + " ORDER BY b.fecha, b.hora_inicio LIMIT 1",
        (fin.isoformat(), *ESTADOS_VIGENTES),
    ).fetchone()
    if fila is None:
        return None
    return date.fromisoformat(fila["fecha"])
