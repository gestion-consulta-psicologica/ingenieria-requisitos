from __future__ import annotations

import logging
import sqlite3
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db.conexion import conectar
from app.main import crear_app
from app.servicios.disponibilidad import obtener_bloques_cercanos

from app.servicios.reserva import (
    BloqueNoDisponible,
    PacienteNoRegistrado,
    buscar_paciente_por_rut,
    registrar_reserva,
)


def preparar_psicologa_y_pacientes(conexion):
    conexion.execute(
        """
        INSERT INTO psicologa (id, nombre_completo, rut, correo)
        VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, telefono, correo)
        VALUES (1, 'Paciente Uno', '22.222.222-2', '+56 9 1111 1111', 'uno@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, telefono, correo)
        VALUES (2, 'Paciente Dos', '33.333.333-3', '+56 9 2222 2222', 'dos@example.cl')
        """
    )
    conexion.commit()


def insertar_bloque(
    conexion,
    bloque_id: int,
    fecha: str,
    hora_inicio: str = "10:00",
    hora_termino: str = "10:50",
    modalidad: str = "presencial",
):
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (?, 1, ?, ?, ?, ?)
        """,
        (bloque_id, fecha, hora_inicio, hora_termino, modalidad),
    )
    conexion.commit()


def insertar_reserva(
    conexion,
    reserva_id: int,
    bloque_id: int,
    estado: str = "Confirmada",
    paciente_id: int = 1,
):
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado
        )
        VALUES (?, ?, ?, '2026-11-01T09:00:00', ?)
        """,
        (reserva_id, paciente_id, bloque_id, estado),
    )
    conexion.commit()


def test_obtener_bloques_cercanos_solo_libres_y_en_orden(conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 1, "2026-11-12", "10:00", "10:50")
    insertar_bloque(conexion, 2, "2026-11-12", "16:00", "16:50")
    insertar_bloque(conexion, 3, "2026-11-13", "09:00", "09:50")
    insertar_bloque(conexion, 4, "2026-11-11", "09:00", "09:50")
    insertar_reserva(conexion, 1, 2, "Confirmada")

    cercanos = obtener_bloques_cercanos(conexion, date(2026, 11, 12))

    assert [bloque["id"] for bloque in cercanos] == [1, 3]
    assert [bloque["fecha"] for bloque in cercanos] == ["2026-11-12", "2026-11-13"]


def test_buscar_paciente_por_rut_con_y_sin_formato(conexion):
    preparar_psicologa_y_pacientes(conexion)

    con_formato = buscar_paciente_por_rut(conexion, "22.222.222-2")
    sin_formato = buscar_paciente_por_rut(conexion, "222222222")

    assert con_formato is not None
    assert sin_formato is not None
    assert con_formato["id"] == sin_formato["id"] == 1


def test_buscar_paciente_por_rut_inexistente(conexion):
    preparar_psicologa_y_pacientes(conexion)

    assert buscar_paciente_por_rut(conexion, "99.999.999-9") is None


def test_registrar_reserva_exitosa(conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")

    resultado = registrar_reserva(conexion, 10, "22.222.222-2")
    aviso = conexion.execute(
        "SELECT reserva_id FROM correo_pendiente WHERE tipo = 'aviso_reserva'"
    ).fetchone()
    assert aviso["reserva_id"] == resultado["reserva"]["id"]

    assert resultado["reserva"]["estado"] == "Pendiente de confirmación"
    assert resultado["reserva"]["paciente_id"] == 1
    assert resultado["reserva"]["bloque_horario_id"] == 10
    assert resultado["paciente"]["id"] == 1
    assert resultado["bloque"]["id"] == 10


def test_reserva_se_revierte_si_no_se_puede_encolar_el_aviso(conexion):
    from dataclasses import replace

    from app.configuracion import cargar_configuracion

    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")
    configuracion = replace(cargar_configuracion(), max_intentos=0)

    with pytest.raises(sqlite3.IntegrityError, match="no quedó encolado"):
        registrar_reserva(conexion, 10, "22.222.222-2", configuracion=configuracion)

    assert conexion.execute("SELECT COUNT(*) FROM reserva").fetchone()[0] == 0
    assert conexion.execute("SELECT COUNT(*) FROM correo_pendiente").fetchone()[0] == 0


def test_registrar_reserva_bloque_ocupado(conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 11, "2026-11-12", "16:00", "16:50")
    insertar_reserva(conexion, 1, 11, "Pendiente de confirmación", paciente_id=2)

    with pytest.raises(BloqueNoDisponible):
        registrar_reserva(conexion, 11, "22.222.222-2")

    total = conexion.execute(
        "SELECT COUNT(*) FROM reserva WHERE bloque_horario_id = 11"
    ).fetchone()[0]
    assert total == 1


def test_registrar_reserva_con_rut_no_registrado(conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 12, "2026-11-12", "16:00", "16:50")

    with pytest.raises(PacienteNoRegistrado):
        registrar_reserva(conexion, 12, "99.999.999-9")


def test_dos_conexiones_no_crean_reservas_vigentes_para_el_mismo_bloque(
    base_temporal, conexion
):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")
    conexion_a = conectar(base_temporal)
    conexion_b = conectar(base_temporal)
    try:
        conexion_a.execute(
            """
            INSERT INTO reserva (
                id, paciente_id, bloque_horario_id, fecha_registro, estado
            )
            VALUES (1, 1, 10, '2026-11-01T09:00:00', 'Pendiente de confirmación')
            """
        )
        conexion_a.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conexion_b.execute(
                """
                INSERT INTO reserva (
                    id, paciente_id, bloque_horario_id, fecha_registro, estado
                )
                VALUES (2, 2, 10, '2026-11-01T09:01:00', 'Confirmada')
                """
            )
        conexion_b.rollback()

        assert conexion_a.execute(
            "SELECT COUNT(*) FROM reserva WHERE bloque_horario_id = 10"
        ).fetchone()[0] == 1
        assert conexion_b.execute(
            "SELECT COUNT(*) FROM reserva WHERE bloque_horario_id = 10"
        ).fetchone()[0] == 1
        assert conexion_a.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conexion_b.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conexion_a.close()
        conexion_b.close()


def test_aviso_de_reserva_queda_en_la_cola_de_correos(conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")
    conexion.execute(
        """
        INSERT INTO reserva (id, paciente_id, bloque_horario_id, fecha_registro, estado)
        VALUES (1, 1, 10, '2026-11-01T09:00:00', 'Pendiente de confirmación')
        """
    )
    conexion.commit()
    from app.servicios.notificaciones import encolar_aviso_reserva
    from app.configuracion import cargar_configuracion

    encolar_aviso_reserva(
        conexion,
        {"nombre_completo": "Paciente Uno", "rut": "22.222.222-2", "correo": "uno@example.cl"},
        {"id": 10, "fecha": "2026-11-12", "hora_inicio": "16:00", "hora_termino": "16:50", "modalidad": "presencial"},
        {"id": 1},
        cargar_configuracion(),
    )
    fila = conexion.execute(
        "SELECT * FROM correo_pendiente WHERE reserva_id = 1"
    ).fetchone()
    assert fila["tipo"] == "aviso_reserva"
    assert fila["destinatario"] == "uno@example.cl"
    assert fila["estado"] == "pendiente"


def test_formulario_reserva_muestra_bloque(base_temporal, conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get("/reservar/10")

    assert respuesta.status_code == 200
    assert "jueves 12 de noviembre" in respuesta.text
    assert "16:00" in respuesta.text
    assert "16:50" in respuesta.text
    assert "presencial" in respuesta.text
    assert 'name="rut"' in respuesta.text


@pytest.mark.parametrize(
    "caso",
    [
        pytest.param(
            "bloque disponible",
            id="HU-02 · El paciente reserva un bloque horario disponible",
        )
    ],
)
def test_paciente_reserva_bloque_disponible(base_temporal, conexion, caso):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 10, "2026-11-12", "16:00", "16:50")
    with TestClient(crear_app(base_temporal, clave_paciente_demo="clave-prueba")) as cliente:
        respuesta = cliente.post(
            "/reservar/10",
            data={"rut": "222222222"},
            auth=("paciente", "clave-prueba"),
            follow_redirects=False,
        )
        assert respuesta.status_code == 303
        assert respuesta.headers["location"] == "/reservas/1"

        confirmacion = cliente.get("/reservas/1")
        disponibilidad = cliente.get(
            "/disponibilidad", params={"semana": "2026-11-09"}
        )

    reserva = conexion.execute("SELECT * FROM reserva").fetchone()
    assert reserva["estado"] == "Pendiente de confirmación"
    assert reserva["paciente_id"] == 1
    aviso = conexion.execute(
        "SELECT * FROM correo_pendiente WHERE reserva_id = 1"
    ).fetchone()
    assert aviso["tipo"] == "aviso_reserva"
    assert aviso["destinatario"] == "uno@example.cl"
    assert "Pendiente de confirmación" in confirmacion.text
    assert "Paciente Uno" in confirmacion.text
    assert "aviso de reserva registrada" in confirmacion.text
    assert 'data-bloque-id="10"' not in disponibilidad.text


@pytest.mark.parametrize(
    "caso",
    [
        pytest.param(
            "bloque tomado",
            id="HU-02 · Otro paciente reservó el mismo bloque horario antes",
        )
    ],
)
def test_otro_paciente_reservo_el_mismo_bloque(base_temporal, conexion, caso):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 11, "2026-11-12", "16:00", "16:50")
    insertar_bloque(conexion, 12, "2026-11-13", "10:00", "10:50")
    insertar_reserva(conexion, 1, 11, "Confirmada", paciente_id=2)

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post(
            "/reservar/11",
            data={"rut": "22.222.222-2"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 409
    assert "El bloque ya no está disponible" in respuesta.text
    assert "13 de noviembre" in respuesta.text
    assert "10:00" in respuesta.text

    total = conexion.execute(
        "SELECT COUNT(*) FROM reserva WHERE bloque_horario_id = 11"
    ).fetchone()[0]
    assert total == 1


@pytest.mark.parametrize(
    "caso",
    [
        pytest.param(
            "rut no registrado",
            id="HU-02 · El paciente no está registrado en el sistema",
        )
    ],
)
def test_paciente_no_registrado_en_el_sistema(base_temporal, conexion, caso):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 13, "2026-11-12", "16:00", "16:50")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post(
            "/reservar/13",
            data={"rut": "99.999.999-9"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/pacientes/registro?bloque_id=13"

    total = conexion.execute(
        "SELECT COUNT(*) FROM reserva WHERE bloque_horario_id = 13"
    ).fetchone()[0]
    assert total == 0


def test_disponibilidad_enlaza_reservar(base_temporal, conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 14, "2026-11-10", "11:00", "11:50")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get(
            "/disponibilidad", params={"semana": "2026-11-09"}
        )

    assert respuesta.status_code == 200
    assert 'href="/reservar/14"' in respuesta.text


def test_bloque_ocupado_no_deriva_a_registro_de_paciente(base_temporal, conexion):
    preparar_psicologa_y_pacientes(conexion)
    insertar_bloque(conexion, 11, "2026-11-12", "16:00", "16:50")
    insertar_reserva(conexion, 1, 11, "Pendiente de confirmación")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post("/reservar/11", data={"rut": "99.999.999-9"})

    assert respuesta.status_code == 409
    assert "El bloque ya no está disponible" in respuesta.text


def test_bloque_y_reserva_inexistentes_responden_404(base_temporal):
    with TestClient(crear_app(base_temporal)) as cliente:
        assert cliente.get("/reservar/999").status_code == 404
        assert cliente.get("/reservas/999").status_code == 404
