from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timedelta

from app.tiempo import ZONA_POR_DEFECTO, ahora_utc, zona

# Regla de vigencia de EST-01, confirmada en la ficha de HU-01.
ESTADOS_VIGENTES = ("Pendiente de confirmación", "Confirmada")
# Un bloque cuya reserva se finalizó ya se consumió y no vuelve a ofrecerse
# (11-diagramas-estado.md), aunque Finalizada no sea un estado vigente.
ESTADOS_QUE_OCUPAN_BLOQUE = (*ESTADOS_VIGENTES, "Finalizada")
APERTURA = time(9)
CIERRE = time(19)
DURACION_ATENCION = timedelta(minutes=50)


def horario_dentro_de_jornada(fecha: date, inicio: time, termino: time) -> bool:
    return fecha.weekday() < 6 and APERTURA <= inicio < termino <= CIERRE


def rango_semana(fecha: date) -> tuple[date, date]:
    inicio = fecha - timedelta(days=fecha.weekday())
    return inicio, inicio + timedelta(days=6)


def insertar_bloque_libre(
    conexion: sqlite3.Connection,
    psicologa_id: int,
    inicio: datetime,
    termino: datetime,
    modalidad: str,
    *,
    psiquiatra: bool = False,
) -> int:
    columna = "psiquiatra_cuenta_id" if psiquiatra else "psicologa_id"
    fecha = inicio.date().isoformat()
    hora_inicio = inicio.time().isoformat(timespec="minutes")
    hora_termino = termino.time().isoformat(timespec="minutes")
    cursor = conexion.execute(
        f"""
        INSERT INTO bloque_horario ({columna}, fecha, hora_inicio, hora_termino, modalidad)
        SELECT ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM bloque_horario
            WHERE {columna} = ? AND fecha = ?
              AND (hora_inicio = ? OR (
                  time(hora_inicio) < time(?) AND time(hora_termino) > time(?)
              ))
        )
        """,
        (
            psicologa_id, fecha, hora_inicio, hora_termino, modalidad,
            psicologa_id, fecha, hora_inicio, hora_termino, hora_inicio,
        ),
    )
    return cursor.rowcount


def crear_bloques_por_hora(
    conexion: sqlite3.Connection,
    psicologa_id: int,
    semana: date,
    modalidad: str,
    ahora: datetime,
    zona_horaria: str,
) -> int:
    lunes, _ = rango_semana(semana)
    zona_local = zona(zona_horaria)
    local = ahora.astimezone(zona_local)
    creados = 0
    for dia in range(6):
        fecha = lunes + timedelta(days=dia)
        for hora in range(APERTURA.hour, CIERRE.hour):
            inicio = datetime.combine(fecha, time(hora), zona_local)
            if inicio > local:
                creados += insertar_bloque_libre(
                    conexion, psicologa_id, inicio, inicio + DURACION_ATENCION, modalidad,
                )
    return creados


def _marcadores(cantidad: int) -> str:
    return ", ".join("?" for _ in range(cantidad))


def consultar_bloques_reservables(
    conexion: sqlite3.Connection,
    condicion: str,
    parametros: tuple,
    *,
    ahora: datetime | None = None,
    zona_horaria: str = ZONA_POR_DEFECTO,
    limite: int = -1,
    psiquiatra_id: int | None = None,
) -> list[dict]:
    local = (ahora or ahora_utc()).astimezone(zona(zona_horaria))
    filas = conexion.execute(
        f"""
        SELECT b.id, b.fecha, b.hora_inicio, b.hora_termino, b.modalidad
        FROM bloque_horario b
        WHERE ({condicion})
          AND b.psiquiatra_cuenta_id IS ?
          AND b.fecha >= ?
          AND strftime('%w', b.fecha) <> '0'
          AND time(b.hora_inicio) >= ?
          AND time(b.hora_termino) <= ?
          AND time(b.hora_inicio) < time(b.hora_termino)
          AND (b.fecha > ? OR time(b.hora_inicio) > ?)
          AND NOT EXISTS (
              SELECT 1
              FROM reserva r
              WHERE r.bloque_horario_id = b.id
                AND r.estado IN ({_marcadores(len(ESTADOS_QUE_OCUPAN_BLOQUE))})
          )
        ORDER BY b.fecha, b.hora_inicio, b.id
        LIMIT ?
        """,
        (*parametros, psiquiatra_id, local.date().isoformat(), APERTURA.isoformat(),
         CIERRE.isoformat(), local.date().isoformat(),
         local.strftime("%H:%M:%S"), *ESTADOS_QUE_OCUPAN_BLOQUE, limite),
    )
    return [dict(fila) for fila in filas]


def obtener_disponibilidad_semana(
    conexion: sqlite3.Connection, fecha_semana: date, *,
    ahora: datetime | None = None, zona_horaria: str = ZONA_POR_DEFECTO,
) -> list[dict]:
    inicio, fin = rango_semana(fecha_semana)
    return consultar_bloques_reservables(
        conexion, "b.fecha BETWEEN ? AND ?", (inicio.isoformat(), fin.isoformat()),
        ahora=ahora, zona_horaria=zona_horaria,
    )


def obtener_bloques_cercanos(
    conexion: sqlite3.Connection, fecha_referencia: date, limite: int = 3, *,
    ahora: datetime | None = None, zona_horaria: str = ZONA_POR_DEFECTO,
) -> list[dict]:
    return consultar_bloques_reservables(
        conexion, "b.fecha >= ?", (fecha_referencia.isoformat(),),
        ahora=ahora, zona_horaria=zona_horaria, limite=limite,
    )


def obtener_proximo_bloque(
    conexion: sqlite3.Connection, fecha_semana: date, *,
    ahora: datetime | None = None, zona_horaria: str = ZONA_POR_DEFECTO,
) -> date | None:
    _, fin = rango_semana(fecha_semana)
    filas = consultar_bloques_reservables(
        conexion, "b.fecha > ?", (fin.isoformat(),),
        ahora=ahora, zona_horaria=zona_horaria, limite=1,
    )
    return date.fromisoformat(filas[0]["fecha"]) if filas else None
