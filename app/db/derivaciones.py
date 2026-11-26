"""Consultas y escrituras de derivaciones y del directorio de psiquiatras."""

import sqlite3

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
        SELECT r.id, r.paciente_id, p.nombre_completo, b.fecha, b.hora_inicio
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        JOIN cuenta c ON c.psicologa_id = b.psicologa_id
        WHERE r.id = ? AND c.id = ? AND c.rol = 'psicologa' AND c.activo = 1
          AND r.estado != 'Cancelada'
        """,
        (reserva_id, psicologa_cuenta_id),
    ).fetchone()


def destino_disponible(conexion: sqlite3.Connection, cuenta_id: int) -> bool:
    return conexion.execute(
        f"SELECT 1 FROM cuenta WHERE id = ? AND {PSIQUIATRA_DISPONIBLE}", (cuenta_id,),
    ).fetchone() is not None


def insertar(conexion: sqlite3.Connection, reserva, emisora_id: int, receptor_id: int) -> bool:
    resultado = conexion.execute(
        """
        INSERT INTO derivacion (reserva_id, paciente_id, psicologa_cuenta_id, psiquiatra_cuenta_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (reserva_id, psiquiatra_cuenta_id) DO NOTHING
        """,
        (reserva["id"], reserva["paciente_id"], emisora_id, receptor_id),
    )
    return bool(resultado.rowcount)


def historial(conexion: sqlite3.Connection, cuenta_id: int, *, recibidas: bool):
    columna = "psiquiatra_cuenta_id" if recibidas else "psicologa_cuenta_id"
    return conexion.execute(
        f"""
        SELECT d.id, d.reserva_id, d.estado, d.creada_en, d.aceptada_en,
               p.nombre_completo AS paciente, psi.nombre_psiquiatra AS psiquiatra,
               em.nombre_completo AS psicologa
        FROM derivacion d
        JOIN paciente p ON p.id = d.paciente_id
        JOIN cuenta psi ON psi.id = d.psiquiatra_cuenta_id
        JOIN cuenta c ON c.id = d.psicologa_cuenta_id
        JOIN psicologa em ON em.id = c.psicologa_id
        WHERE d.{columna} = ? ORDER BY d.id DESC
        """,
        (cuenta_id,),
    ).fetchall()


def aceptar(conexion: sqlite3.Connection, derivacion_id: int, cuenta_id: int):
    return conexion.execute(
        """
        UPDATE derivacion SET aceptada_en = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
        WHERE id = ? AND psiquiatra_cuenta_id = ? AND aceptada_en IS NULL
        """, (derivacion_id, cuenta_id),
    ).rowcount


def estado_recibida(conexion: sqlite3.Connection, derivacion_id: int, cuenta_id: int):
    return conexion.execute(
        "SELECT estado FROM derivacion WHERE id = ? AND psiquiatra_cuenta_id = ?",
        (derivacion_id, cuenta_id),
    ).fetchone()
