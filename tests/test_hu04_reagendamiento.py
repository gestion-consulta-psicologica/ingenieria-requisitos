from __future__ import annotations

from datetime import date, timedelta

import pytest
from tests.acceso_demo import cliente_con_reserva_de_prueba as TestClient

from app.configuracion import ConfiguracionCorreo
from app.db.conexion import conectar
from app.main import crear_app
from app.servicios.confirmacion import (
    TIPO_VISPERA,
    enviar_solicitud,
    registrar_respuesta,
)
from app.servicios.reagendamiento import (
    BloqueNoDisponible,
    EstadoReservaInvalido,
    cancelar_reserva,
    listar_historial,
    obtener_alternativas,
    reagendar_reserva,
)
from app.servicios.reserva import bloque_esta_disponible
from app.tiempo import programado
from app.servicios.cola_correo import marcar_enviado

HOY = date(2026, 11, 9)
AHORA = programado(HOY, "08:00")
FECHA_ACTUAL = (HOY + timedelta(days=1)).isoformat()
FECHA_NUEVA = (HOY + timedelta(days=2)).isoformat()
FECHA_TOMADA = (HOY + timedelta(days=3)).isoformat()
FECHA_LEJANA = (HOY + timedelta(days=20)).isoformat()


def configuracion_prueba() -> ConfiguracionCorreo:
    return ConfiguracionCorreo(
        smtp_host="smtp.prueba.local",
        smtp_puerto=2525,
        smtp_usuario=None,
        smtp_clave=None,
        smtp_remitente="consultas@example.cl",
        smtp_seguridad="ninguna",
        smtp_timeout=5,
        url_publica="http://testserver",
        max_intentos=3,
        reintento_base_segundos=30,
        planificador_activo=False,
        intervalo_planificador_segundos=60,
        timeout_envio_segundos=300,
        hora_vispera="09:00",
        hora_recordatorio="08:00",
        zona_horaria="America/Santiago",
    )


def preparar_base(conexion, *, estado: str = "Confirmada", version: int = 1) -> None:
    conexion.execute(
        """
        INSERT INTO psicologa (id, nombre_completo, rut, correo)
        VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (
            id, nombre_completo, rut, telefono, correo
        )
        VALUES (1, 'Paciente Uno', '22.222.222-2', '+56 9 1111 1111', 'uno@example.cl')
        """
    )
    conexion.execute(
        """
        INSERT INTO paciente (
            id, nombre_completo, rut, telefono, correo
        )
        VALUES (2, 'Paciente Dos', '33.333.333-3', '+56 9 2222 2222', 'dos@example.cl')
        """
    )
    bloques = (
        (1, FECHA_ACTUAL, "18:00", "18:50"),
        (2, FECHA_NUEVA, "17:00", "17:50"),
        (3, FECHA_TOMADA, "16:00", "16:50"),
        (4, FECHA_LEJANA, "15:00", "15:50"),
    )
    for bloque_id, fecha, inicio, termino in bloques:
        conexion.execute(
            """
            INSERT INTO bloque_horario (
                id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
            )
            VALUES (?, 1, ?, ?, ?, 'presencial')
            """,
            (bloque_id, fecha, inicio, termino),
        )
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado, version
        )
        VALUES (1, 1, 1, '2026-11-01T09:00:00', ?, ?)
        """,
        (estado, version),
    )
    conexion.commit()


def insertar_reserva_tomada(conexion) -> None:
    conexion.execute(
        """
        INSERT INTO reserva (
            id, paciente_id, bloque_horario_id, fecha_registro, estado, version
        )
        VALUES (2, 2, 3, '2026-11-01T10:00:00', 'Confirmada', 1)
        """
    )
    conexion.commit()


def correos_de(conexion, reserva_id: int = 1):
    return [
        dict(fila)
        for fila in conexion.execute(
            "SELECT * FROM correo_pendiente WHERE reserva_id = ? ORDER BY id",
            (reserva_id,),
        )
    ]


def test_cancelar_reserva_confirmada_libera_bloque_y_registra_historial(conexion):
    preparar_base(conexion)

    resultado = cancelar_reserva(conexion, 1)

    assert resultado["reserva"]["estado"] == "Cancelada"
    assert resultado["reserva"]["version"] == 1
    assert bloque_esta_disponible(conexion, 1) is True
    historial = listar_historial(conexion, 1)
    assert len(historial) == 1
    assert historial[0]["tipo"] == "cancelacion"
    assert historial[0]["estado_anterior"] == "Confirmada"
    assert historial[0]["estado_nuevo"] == "Cancelada"
    cargo = conexion.execute(
        "SELECT monto, motivo FROM cargo WHERE reserva_id = 1"
    ).fetchone()
    assert dict(cargo) == {"monto": 5000, "motivo": "cancelación"}
    assert conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE tipo = 'aviso_cargo'"
    ).fetchone()[0] == 1


def test_no_se_puede_cancelar_una_reserva_pendiente(conexion):
    preparar_base(conexion, estado="Pendiente de confirmación")

    with pytest.raises(EstadoReservaInvalido):
        cancelar_reserva(conexion, 1)

    fila = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert fila["estado"] == "Pendiente de confirmación"
    assert listar_historial(conexion, 1) == []


def test_no_se_puede_cancelar_una_reserva_con_atencion(conexion):
    preparar_base(conexion)
    conexion.execute(
        """
        INSERT INTO atencion (reserva_id, tipo_atencion, monto, estado)
        VALUES (1, 'presencial', 30000, 'programada')
        """
    )
    conexion.commit()

    with pytest.raises(EstadoReservaInvalido):
        cancelar_reserva(conexion, 1)

    fila = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert fila["estado"] == "Confirmada"
    assert listar_historial(conexion, 1) == []


def test_no_se_puede_reagendar_una_reserva_con_atencion(conexion):
    preparar_base(conexion)
    conexion.execute(
        """
        INSERT INTO atencion (reserva_id, tipo_atencion, monto, estado)
        VALUES (1, 'presencial', 30000, 'programada')
        """
    )
    conexion.commit()

    with pytest.raises(EstadoReservaInvalido):
        reagendar_reserva(conexion, 1, 2)

    fila = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert fila["estado"] == "Confirmada"
    assert listar_historial(conexion, 1) == []


@pytest.mark.parametrize("operacion", ["cancelar", "reagendar"])
def test_no_se_gestiona_una_hora_que_ya_comenzo(conexion, operacion):
    # El bloque 1 empieza a las 18:00 de FECHA_ACTUAL; aún no hay atención porque
    # el planificador no ha pasado, pero la reserva ya no se puede gestionar.
    preparar_base(conexion)
    inicio = programado(FECHA_ACTUAL, "18:00")

    with pytest.raises(EstadoReservaInvalido, match="ya comenzó"):
        if operacion == "cancelar":
            cancelar_reserva(conexion, 1, ahora=inicio)
        else:
            reagendar_reserva(conexion, 1, 2, ahora=inicio)

    fila = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert (fila["estado"], fila["bloque_horario_id"]) == ("Confirmada", 1)
    assert listar_historial(conexion, 1) == []
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0


def test_detalle_oculta_gestion_cuando_la_hora_ya_comenzo(base_temporal, monkeypatch):
    from app.rutas import reserva as ruta_reserva

    conexion = conectar(base_temporal)
    try:
        preparar_base(conexion)
    finally:
        conexion.close()
    monkeypatch.setattr(ruta_reserva, "ahora_utc", lambda: programado(FECHA_ACTUAL, "18:00"))

    with TestClient(crear_app(base_temporal)) as cliente:
        detalle = cliente.get("/reservas/1")
        reagendar = cliente.get("/reservas/1/reagendar")

    assert detalle.status_code == 200
    assert 'action="/reservas/1/cancelar"' not in detalle.text
    assert reagendar.status_code == 409


def test_alternativas_excluyen_bloque_actual_ocupados_y_fuera_de_rango(conexion):
    preparar_base(conexion)
    insertar_reserva_tomada(conexion)

    alternativas = obtener_alternativas(
        conexion, 1, desde=HOY, dias=14
    )

    assert [bloque["id"] for bloque in alternativas] == [2]


def test_guardado_rechaza_bloque_fuera_de_la_ventana(conexion):
    preparar_base(conexion)
    fecha_fuera = (HOY + timedelta(days=14)).isoformat()
    conexion.execute(
        "UPDATE bloque_horario SET fecha = ? WHERE id = 2", (fecha_fuera,)
    )
    conexion.commit()

    with pytest.raises(BloqueNoDisponible):
        reagendar_reserva(conexion, 1, 2, ahora=AHORA)

    reserva = conexion.execute(
        "SELECT bloque_horario_id, estado, version FROM reserva WHERE id = 1"
    ).fetchone()
    assert tuple(reserva) == (1, "Confirmada", 1)
    assert listar_historial(conexion, 1) == []
    assert conexion.execute("SELECT COUNT(*) FROM correo_pendiente").fetchone()[0] == 0


def test_sin_alternativas_conserva_reserva(conexion):
    preparar_base(conexion)
    insertar_reserva_tomada(conexion)
    conexion.execute(
        "UPDATE bloque_horario SET fecha = ? WHERE id = 2",
        (FECHA_LEJANA,),
    )
    conexion.commit()

    assert obtener_alternativas(conexion, 1, desde=HOY, dias=14) == []
    reserva = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert reserva["bloque_horario_id"] == 1
    assert reserva["estado"] == "Confirmada"


def test_reagendar_actualiza_reserva_libera_anterior_y_encola_aviso(conexion):
    preparar_base(conexion)

    resultado = reagendar_reserva(
        conexion,
        1,
        2,
        configuracion=configuracion_prueba(),
        ahora=AHORA,
    )

    assert resultado["reserva"]["id"] == 1
    assert resultado["reserva"]["bloque_horario_id"] == 2
    assert resultado["reserva"]["estado"] == "Pendiente de confirmación"
    assert resultado["reserva"]["version"] == 2
    assert bloque_esta_disponible(conexion, 1) is True
    assert bloque_esta_disponible(conexion, 2) is False

    historial = listar_historial(conexion, 1)
    assert len(historial) == 1
    assert historial[0]["tipo"] == "reagendamiento"
    assert historial[0]["bloque_anterior_id"] == 1
    assert historial[0]["bloque_nuevo_id"] == 2
    assert historial[0]["version_anterior"] == 1
    assert historial[0]["version_nueva"] == 2

    correos = correos_de(conexion)
    assert len(correos) == 1
    assert correos[0]["clave_idempotencia"] == "aviso_reagendamiento:1:2"
    assert "reagendada" in correos[0]["asunto"].lower()
    assert correos[0]["estado"] == "pendiente"


def test_reagendar_bloque_tomado_no_cambia_nada(conexion):
    preparar_base(conexion)
    insertar_reserva_tomada(conexion)

    with pytest.raises(BloqueNoDisponible):
        reagendar_reserva(
            conexion,
            1,
            3,
            configuracion=configuracion_prueba(),
            ahora=AHORA,
        )

    reserva = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert reserva["bloque_horario_id"] == 1
    assert reserva["estado"] == "Confirmada"
    assert reserva["version"] == 1
    assert listar_historial(conexion, 1) == []
    assert correos_de(conexion) == []


def test_reagendar_al_mismo_bloque_se_rechaza(conexion):
    preparar_base(conexion)

    with pytest.raises(BloqueNoDisponible):
        reagendar_reserva(
            conexion,
            1,
            1,
            configuracion=configuracion_prueba(),
            ahora=AHORA,
        )


def test_reagendar_inicia_un_nuevo_ciclo_de_confirmacion(conexion):
    preparar_base(conexion)
    conexion.execute(
        """
        INSERT INTO solicitud_confirmacion (
            reserva_id, version, fecha_envio, tipo, estado, respuesta,
            fecha_respuesta
        )
        VALUES (
            1, 1, ?, 'recordatorio', 'respondida', 'confirma',
            '2026-11-18T10:00:00'
        )
        """,
        (FECHA_ACTUAL,),
    )
    conexion.commit()

    reagendar_reserva(
        conexion,
        1,
        2,
        configuracion=configuracion_prueba(),
        ahora=AHORA,
    )
    solicitud = enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=configuracion_prueba(),
        ahora=AHORA,
    )
    marcar_enviado(conexion, solicitud["correo"]["id"], "smtp-prueba", AHORA)

    solicitudes = [
        dict(fila)
        for fila in conexion.execute(
            "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1 ORDER BY id"
        )
    ]
    assert [solicitud["version"] for solicitud in solicitudes] == [1, 2]
    assert solicitudes[1]["estado"] == "pendiente"
    assert solicitudes[1]["tipo"] == TIPO_VISPERA

    resultado = registrar_respuesta(
        conexion, 1, "confirma", ahora=AHORA
    )
    assert resultado["reserva"]["estado"] == "Confirmada"
    fila = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
    assert fila["version"] == 2


def test_rutas_de_gestion_muestran_alternativas_y_permiten_reagendar(base_temporal):
    conexion = conectar(base_temporal)
    try:
        preparar_base(conexion)
    finally:
        conexion.close()

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        detalle = cliente.get("/reservas/1")
        assert detalle.status_code == 200
        assert "Reagendar hora" in detalle.text
        assert "Cancelar reserva" in detalle.text

        alternativas = cliente.get("/reservas/1/reagendar")
        assert alternativas.status_code == 200
        assert "Horarios disponibles" in alternativas.text
        assert "Elegir este horario" in alternativas.text

        cambio = cliente.post(
            "/reservas/1/reagendar",
            data={"bloque_id": 2},
            follow_redirects=False,
        )
        assert cambio.status_code == 303
        assert cambio.headers["location"] == "/reservas/1"

        detalle_nuevo = cliente.get("/reservas/1")
        assert detalle_nuevo.status_code == 200
        assert "Pendiente de confirmación" in detalle_nuevo.text
        assert "Reagendamiento" in detalle_nuevo.text
        assert "Aviso de reserva reagendada" in detalle_nuevo.text


def test_http_reagendar_bloque_tomado_muestra_conflicto(base_temporal, conexion):
    preparar_base(conexion)
    insertar_reserva_tomada(conexion)

    with TestClient(crear_app(base_temporal, planificador_activo=False)) as cliente:
        respuesta = cliente.post("/reservas/1/reagendar", data={"bloque_id": 3})

    assert respuesta.status_code == 409
    assert "El bloque seleccionado ya no está disponible." in respuesta.text
    fila = conexion.execute(
        "SELECT bloque_horario_id, estado, version FROM reserva WHERE id = 1"
    ).fetchone()
    assert tuple(fila) == (1, "Confirmada", 1)
    assert listar_historial(conexion, 1) == []


def test_http_reagendar_sin_alternativas_muestra_mensaje(base_temporal, conexion):
    preparar_base(conexion)
    insertar_reserva_tomada(conexion)
    conexion.execute("UPDATE bloque_horario SET fecha = ? WHERE id = 2", (FECHA_LEJANA,))
    conexion.commit()

    with TestClient(crear_app(base_temporal, planificador_activo=False)) as cliente:
        respuesta = cliente.get("/reservas/1/reagendar")

    assert respuesta.status_code == 200
    assert "No hay alternativas disponibles en los próximos 14 días." in respuesta.text
    assert "La reserva original se conserva sin cambios." in respuesta.text
    assert 'name="bloque_id"' not in respuesta.text
    fila = conexion.execute(
        "SELECT bloque_horario_id, estado, version FROM reserva WHERE id = 1"
    ).fetchone()
    assert tuple(fila) == (1, "Confirmada", 1)


def test_ruta_de_cancelacion_libera_bloque(base_temporal):
    conexion = conectar(base_temporal)
    try:
        preparar_base(conexion)
    finally:
        conexion.close()

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        respuesta = cliente.post(
            "/reservas/1/cancelar", follow_redirects=False
        )
        assert respuesta.status_code == 303

    conexion = conectar(base_temporal)
    try:
        reserva = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
        assert reserva["estado"] == "Cancelada"
        assert bloque_esta_disponible(conexion, 1) is True
    finally:
        conexion.close()
