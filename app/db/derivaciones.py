"""Consultas y escrituras de derivaciones y del directorio de psiquiatras."""

import sqlite3

from app.servicios.disponibilidad import ESTADOS_QUE_OCUPAN_BLOQUE
# El directorio y el INSERT usan la misma definición de disponibilidad.
PSIQUIATRA_DISPONIBLE = """
    rol = 'psiquiatra' AND activo = 1
    AND correo_verificado_en IS NOT NULL AND identidad_verificada_en IS NOT NULL
"""


def psiquiatras(conexion: sqlite3.Connection, *, solo_disponibles: bool):
    filtro = PSIQUIATRA_DISPONIBLE if solo_disponibles else "rol = 'psiquiatra'"
    return conexion.execute(
        f"""
        SELECT id, nombre_psiquiatra, correo, activo FROM cuenta
        WHERE {filtro} ORDER BY nombre_psiquiatra COLLATE NOCASE, id
        """
    ).fetchall()


def solicitud(conexion: sqlite3.Connection, reserva_id: int, psicologa_cuenta_id: int):
    return conexion.execute(
        """
        SELECT r.id, r.paciente_id, r.version, r.bloque_horario_id, p.nombre_completo,
               p.correo AS paciente_correo, b.fecha, b.hora_inicio, b.hora_termino, b.modalidad
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        JOIN cuenta c ON c.psicologa_id = b.psicologa_id
        WHERE r.id = ? AND c.id = ? AND c.rol = 'psicologa' AND c.activo = 1
          AND r.estado = 'Pendiente de confirmación'
        """,
        (reserva_id, psicologa_cuenta_id),
    ).fetchone()


def destino_disponible(conexion: sqlite3.Connection, cuenta_id: int) -> bool:
    return conexion.execute(
        f"SELECT 1 FROM cuenta WHERE id = ? AND {PSIQUIATRA_DISPONIBLE}", (cuenta_id,),
    ).fetchone() is not None


def destinos_para_solicitud(conexion: sqlite3.Connection, reserva, receptor_id: int | None = None):
    estados = ", ".join("?" for _ in ESTADOS_QUE_OCUPAN_BLOQUE)
    return conexion.execute(
        f"""
        SELECT c.id, c.nombre_psiquiatra, c.correo, b.id AS bloque_id
        FROM cuenta c JOIN bloque_horario b ON b.psiquiatra_cuenta_id = c.id
        WHERE {PSIQUIATRA_DISPONIBLE}
          AND (? IS NULL OR c.id = ?)
          AND b.fecha = ? AND b.hora_inicio = ? AND b.hora_termino = ? AND b.modalidad = ?
          AND NOT EXISTS (
              SELECT 1 FROM reserva r
              WHERE r.bloque_horario_id = b.id AND r.estado IN ({estados})
          )
        ORDER BY c.nombre_psiquiatra COLLATE NOCASE, c.id
        """,
        (receptor_id, receptor_id, reserva["fecha"], reserva["hora_inicio"],
         reserva["hora_termino"], reserva["modalidad"], *ESTADOS_QUE_OCUPAN_BLOQUE),
    ).fetchall()


def insertar(conexion: sqlite3.Connection, reserva, emisora_id: int, receptor_id: int) -> bool:
    resultado = conexion.execute(
        """
        INSERT INTO derivacion (
            reserva_id, paciente_id, psicologa_cuenta_id, psiquiatra_cuenta_id,
            version_origen, bloque_origen_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
        """,
        (reserva["id"], reserva["paciente_id"], emisora_id, receptor_id,
         reserva["version"], reserva["bloque_horario_id"]),
    )
    return bool(resultado.rowcount)


def historial(conexion: sqlite3.Connection, cuenta_id: int, *, recibidas: bool):
    columna = "psiquiatra_cuenta_id" if recibidas else "psicologa_cuenta_id"
    return conexion.execute(
        f"""
        SELECT d.id, d.reserva_id, d.creada_en, d.aceptada_en, d.rechazada_en,
               bo.fecha, bo.hora_inicio, bo.modalidad,
               CASE
                 WHEN d.version_origen IS NULL THEN d.estado || ' (histórica)'
                 WHEN d.estado = 'Pendiente' AND (
                    r.estado != 'Pendiente de confirmación'
                    OR r.version != d.version_origen
                    OR r.bloque_horario_id != d.bloque_origen_id
                 ) THEN 'Cerrada'
                 ELSE d.estado
               END AS estado,
               p.nombre_completo AS paciente, psi.nombre_psiquiatra AS psiquiatra,
               em.nombre_completo AS psicologa
        FROM derivacion d
        JOIN reserva r ON r.id = d.reserva_id
        LEFT JOIN bloque_horario bo ON bo.id = d.bloque_origen_id
        JOIN paciente p ON p.id = d.paciente_id
        JOIN cuenta psi ON psi.id = d.psiquiatra_cuenta_id
        JOIN cuenta c ON c.id = d.psicologa_cuenta_id
        JOIN psicologa em ON em.id = c.psicologa_id
        WHERE d.{columna} = ? ORDER BY d.id DESC
        """,
        (cuenta_id,),
    ).fetchall()


def bloques_de_psiquiatra(conexion: sqlite3.Connection, cuenta_id: int):
    return conexion.execute(
        """
        SELECT b.fecha, b.hora_inicio, b.hora_termino, b.modalidad,
               r.id AS reserva_id, r.estado, p.nombre_completo AS paciente
        FROM bloque_horario b
        LEFT JOIN reserva r ON r.bloque_horario_id = b.id
          AND r.estado IN ('Pendiente de confirmación', 'Confirmada', 'Finalizada')
        LEFT JOIN paciente p ON p.id = r.paciente_id
        WHERE b.psiquiatra_cuenta_id = ?
        ORDER BY b.fecha DESC, b.hora_inicio
        """, (cuenta_id,),
    ).fetchall()


def recibida(conexion: sqlite3.Connection, derivacion_id: int, cuenta_id: int):
    return conexion.execute(
        "SELECT * FROM derivacion WHERE id = ? AND psiquiatra_cuenta_id = ?",
        (derivacion_id, cuenta_id),
    ).fetchone()
