from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import crear_app
from app.servicios.atenciones import crear_atenciones_vencidas
from app.servicios.disponibilidad import (
    obtener_disponibilidad_semana,
    obtener_proximo_bloque,
)
from app.tiempo import programado


def preparar_psicologa_y_paciente(conexion):
    conexion.execute(
        """
        INSERT INTO psicologa (id, nombre_completo, rut, correo)
        VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, correo)
        VALUES (1, 'Paciente de Prueba', '22.222.222-2', 'paciente@example.cl')
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


def insertar_reserva(conexion, reserva_id: int, bloque_id: int, estado: str):
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado
        )
        VALUES (?, 1, ?, '2026-11-01T09:00:00', ?)
        """,
        (reserva_id, bloque_id, estado),
    )
    conexion.commit()


@pytest.mark.parametrize(
    "semana",
    [
        pytest.param(
            date(2026, 11, 9),
            id="HU-01 · El paciente consulta una semana con bloques horarios libres",
        )
    ],
)
def test_semana_con_bloques_libres(base_temporal, conexion, semana):
    preparar_psicologa_y_paciente(conexion)
    insertar_bloque(conexion, 1, "2026-11-10", "10:00", "10:50")
    insertar_bloque(conexion, 2, "2026-11-10", "11:00", "11:50")
    insertar_reserva(conexion, 1, 1, "Pendiente de confirmación")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get(
            "/disponibilidad", params={"semana": semana.isoformat()}
        )

    assert respuesta.status_code == 200
    assert 'data-bloque-id="2"' in respuesta.text
    assert 'data-bloque-id="1"' not in respuesta.text
    assert "11:00" in respuesta.text
    assert "10:00" not in respuesta.text
    assert "martes 10 de noviembre" in respuesta.text
    assert 'href="/disponibilidad" aria-current="page">Paciente' in respuesta.text
    assert "Paciente" in respuesta.text


@pytest.mark.parametrize(
    "semana",
    [
        pytest.param(
            date(2026, 11, 16),
            id="HU-01 · El paciente consulta una semana sin bloques horarios libres",
        )
    ],
)
def test_semana_sin_bloques_libres(base_temporal, conexion, semana):
    preparar_psicologa_y_paciente(conexion)
    insertar_bloque(conexion, 3, "2026-11-17", "10:00", "10:50")
    insertar_reserva(conexion, 2, 3, "Confirmada")
    insertar_bloque(conexion, 4, "2026-11-24", "10:00", "10:50", "online")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get(
            "/disponibilidad", params={"semana": semana.isoformat()}
        )

    assert respuesta.status_code == 200
    assert "No hay horas disponibles para esa semana" in respuesta.text
    assert "24 de noviembre de 2026" in respuesta.text


def test_regla_vigencia_est01(conexion):
    preparar_psicologa_y_paciente(conexion)
    datos = (
        (10, "09:00", "Pendiente de confirmación"),
        (11, "10:00", "Confirmada"),
        (12, "11:00", "Cancelada"),
        (13, "12:00", "Sin confirmar"),
    )
    for bloque_id, hora_inicio, estado in datos:
        insertar_bloque(conexion, bloque_id, "2026-11-10", hora_inicio, "13:00")
        insertar_reserva(conexion, bloque_id, bloque_id, estado)

    bloques = obtener_disponibilidad_semana(conexion, date(2026, 11, 9))

    assert {bloque["id"] for bloque in bloques} == {12, 13}


def test_proximo_bloque_sin_alternativas(conexion):
    preparar_psicologa_y_paciente(conexion)
    insertar_bloque(conexion, 20, "2026-11-17", "10:00", "10:50")
    insertar_reserva(conexion, 20, 20, "Confirmada")

    assert obtener_proximo_bloque(conexion, date(2026, 11, 16)) is None


def test_raiz_redirige_a_disponibilidad(base_temporal):
    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get("/", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/disponibilidad"


def test_semana_omitida_usa_semana_actual(base_temporal):
    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get("/disponibilidad")

    assert respuesta.status_code == 200


def test_jornada_y_hora_de_inicio_filtran_la_disponibilidad(conexion):
    preparar_psicologa_y_paciente(conexion)
    insertar_bloque(conexion, 1, "2026-11-14", "08:59", "09:50")
    insertar_bloque(conexion, 2, "2026-11-14", "09:00", "09:50")
    insertar_bloque(conexion, 3, "2026-11-14", "18:10", "19:00")
    insertar_bloque(conexion, 4, "2026-11-14", "18:15", "19:01")
    insertar_bloque(conexion, 5, "2026-11-15", "09:00", "09:50")
    insertar_bloque(conexion, 6, "2026-11-13", "10:00", "10:50")

    sabado = date(2026, 11, 14)
    antes = obtener_disponibilidad_semana(
        conexion, sabado, ahora=programado(sabado, "08:59"),
    )
    al_inicio = obtener_disponibilidad_semana(
        conexion, sabado, ahora=programado(sabado, "09:00"),
    )

    assert [bloque["id"] for bloque in antes] == [2, 3]
    assert [bloque["id"] for bloque in al_inicio] == [3]


def test_bloque_finalizado_no_se_ofrece_ni_se_puede_reservar(
    base_temporal, conexion, monkeypatch,
):
    from app.rutas import disponibilidad as ruta_disponibilidad
    from app.servicios import disponibilidad

    preparar_psicologa_y_paciente(conexion)
    insertar_bloque(conexion, 1, "2026-11-10", "10:00", "10:50")
    insertar_reserva(conexion, 1, 1, "Confirmada")
    inicio = programado("2026-11-10", "10:00")
    assert crear_atenciones_vencidas(conexion, inicio)
    monkeypatch.setattr(disponibilidad, "ahora_utc", lambda: inicio)
    monkeypatch.setattr(ruta_disponibilidad, "ahora_utc", lambda: inicio)

    with TestClient(crear_app(base_temporal)) as cliente:
        listado = cliente.get("/disponibilidad")
        reserva = cliente.post("/reservar/1", data={"rut": "22.222.222-2"})

    assert 'href="/reservar/1"' not in listado.text
    assert reserva.status_code == 409
    assert [fila["estado"] for fila in conexion.execute("SELECT estado FROM reserva")] == [
        "Finalizada",
    ]
