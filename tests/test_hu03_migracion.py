from __future__ import annotations

import sqlite3

import pytest

from app.db.conexion import (
    DIRECTORIO_MIGRACIONES,
    MigracionDatosAmbiguos,
    aplicar_migraciones,
    conectar,
)

ESTADO_PENDIENTE = "Pendiente de confirmación"
TIPO_VISPERA = "aviso de víspera"
TIPO_RECORDATORIO = "recordatorio"


def crear_base_003(ruta):
    conexion = conectar(ruta)
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    for nombre in (
        "001_crear_tablas_base.sql",
        "002_paciente_correo_opcional.sql",
        "003_confirmacion_asistencia.sql",
    ):
        conexion.executescript(
            (DIRECTORIO_MIGRACIONES / nombre).read_text(encoding="utf-8")
        )
        conexion.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
            (nombre,),
        )
    conexion.commit()
    return conexion


def insertar_datos_base(conexion, estado_reserva: str = ESTADO_PENDIENTE):
    conexion.execute(
        """
        INSERT INTO psicologa (id, nombre_completo, rut, correo)
        VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, correo)
        VALUES (1, 'Paciente Uno', '22.222.222-2', 'uno@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (1, 1, '2026-11-12', '16:00', '16:50', 'presencial')
        """
    )
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado
        )
        VALUES (1, 1, 1, '2026-11-01T09:00:00', ?)
        """,
        (estado_reserva,),
    )


def insertar_solicitud_legacy(
    conexion,
    *,
    solicitud_id: int,
    tipo: str,
    fecha_envio: str,
    respuesta: str | None,
    fecha_respuesta: str | None,
):
    conexion.execute(
        """
        INSERT INTO solicitud_confirmacion (
            id, reserva_id, fecha_envio, tipo, respuesta, fecha_respuesta
        )
        VALUES (?, 1, ?, ?, ?, ?)
        """,
        (solicitud_id, fecha_envio, tipo, respuesta, fecha_respuesta),
    )


def test_migracion_004_backfill_determinista(tmp_path):
    conexion = crear_base_003(tmp_path / "legacy.db")
    insertar_datos_base(conexion)
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, correo)
        VALUES (2, 'Paciente Dos', '33.333.333-3', 'dos@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, correo)
        VALUES (3, 'Paciente Tres', '44.444.444-4', 'tres@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (2, 1, '2026-11-13', '10:00', '10:50', 'presencial')
        """
    )
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (3, 1, '2026-11-14', '11:00', '11:50', 'presencial')
        """
    )
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado
        )
        VALUES (2, 2, 2, '2026-11-01T09:00:00', 'Confirmada')
        """
    )
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado
        )
        VALUES (3, 3, 3, '2026-11-01T09:00:00', 'Sin confirmar')
        """
    )

    insertar_solicitud_legacy(
        conexion,
        solicitud_id=1,
        tipo=TIPO_VISPERA,
        fecha_envio="2026-11-11",
        respuesta=None,
        fecha_respuesta=None,
    )
    insertar_solicitud_legacy(
        conexion,
        solicitud_id=2,
        tipo=TIPO_RECORDATORIO,
        fecha_envio="2026-11-12",
        respuesta=None,
        fecha_respuesta=None,
    )
    conexion.execute(
        """
        INSERT INTO solicitud_confirmacion (
            id, reserva_id, fecha_envio, tipo, respuesta, fecha_respuesta
        )
        VALUES (3, 2, '2026-11-11', 'aviso de víspera', 'confirma', '2026-11-11T18:00:00')
        """
    )
    conexion.execute(
        """
        INSERT INTO solicitud_confirmacion (
            id, reserva_id, fecha_envio, tipo, respuesta, fecha_respuesta
        )
        VALUES (4, 3, '2026-11-14', 'recordatorio', 'sin respuesta', '2026-11-14T11:00')
        """
    )
    conexion.commit()

    aplicar_migraciones(conexion)

    filas = {
        fila["id"]: dict(fila)
        for fila in conexion.execute(
            "SELECT * FROM solicitud_confirmacion ORDER BY id"
        )
    }
    assert filas[1]["estado"] == "reemplazada"
    assert filas[1]["fecha_cierre"] == "2026-11-12"
    assert filas[2]["estado"] == "pendiente"
    assert filas[2]["fecha_cierre"] is None
    assert filas[3]["estado"] == "respondida"
    assert filas[3]["respuesta"] == "confirma"
    assert filas[3]["fecha_respuesta"] == "2026-11-11T18:00:00"
    assert filas[3]["fecha_cierre"] is None
    assert filas[4]["estado"] == "vencida"
    assert filas[4]["respuesta"] == "sin respuesta"
    assert filas[4]["fecha_respuesta"] is None
    assert filas[4]["fecha_cierre"] == "2026-11-14T11:00"
    assert conexion.execute(
        "SELECT COUNT(*) FROM solicitud_confirmacion WHERE estado = 'pendiente'"
    ).fetchone()[0] == 1
    conexion.close()


@pytest.mark.parametrize(
    ("estado_reserva", "respuesta", "motivo"),
    [
        ("Confirmada", "confirma", "respuesta efectiva sin fecha_respuesta"),
        ("Sin confirmar", "sin respuesta", "respuesta sin respuesta sin fecha_respuesta"),
    ],
)
def test_migracion_004_se_detiene_ante_datos_ambiguos(
    tmp_path, estado_reserva, respuesta, motivo
):
    conexion = crear_base_003(tmp_path / "ambigua.db")
    insertar_datos_base(conexion, estado_reserva)
    insertar_solicitud_legacy(
        conexion,
        solicitud_id=1,
        tipo=TIPO_VISPERA,
        fecha_envio="2026-11-11",
        respuesta=respuesta,
        fecha_respuesta=None,
    )
    conexion.commit()

    with pytest.raises(MigracionDatosAmbiguos) as error:
        aplicar_migraciones(conexion)

    assert motivo in str(error.value)
    assert error.value.filas == [
        {
            "solicitud_id": 1,
            "reserva_id": 1,
            "motivo": motivo,
        }
    ]
    columnas = {
        fila["name"] for fila in conexion.execute(
            "PRAGMA table_info(solicitud_confirmacion)"
        )
    }
    assert "estado" not in columnas
    assert "fecha_cierre" not in columnas
    versiones = {
        fila["version"] for fila in conexion.execute("SELECT version FROM schema_migrations")
    }
    assert "004_solicitud_estado_cierre.sql" not in versiones
    conexion.close()


def test_migracion_004_restricciones_finales(tmp_path):
    conexion = crear_base_003(tmp_path / "restricciones.db")
    insertar_datos_base(conexion)
    conexion.commit()
    aplicar_migraciones(conexion)

    conexion.execute(
        """
        INSERT INTO solicitud_confirmacion (
            reserva_id, fecha_envio, tipo, estado
        )
        VALUES (1, '2026-11-11', 'aviso de víspera', 'pendiente')
        """
    )
    conexion.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO solicitud_confirmacion (
                reserva_id, fecha_envio, tipo, estado
            )
            VALUES (1, '2026-11-12', 'recordatorio', 'pendiente')
            """
        )
    conexion.rollback()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO solicitud_confirmacion (
                reserva_id, fecha_envio, tipo, estado
            )
            VALUES (1, '2026-11-12', 'recordatorio', 'reemplazada')
            """
        )
    conexion.rollback()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO solicitud_confirmacion (
                reserva_id, fecha_envio, tipo, estado
            )
            VALUES (1, '2026-11-12', 'recordatorio', 'desconocida')
            """
        )
    conexion.rollback()
    conexion.close()
