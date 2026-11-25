from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient as ClienteSinPermisos
from tests.acceso_demo import cliente_con_reserva_de_prueba as TestClient

from app.configuracion import ConfiguracionCorreo
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.cola_correo import marcar_enviado
from app.servicios.confirmacion import (
    ESTADO_SOLICITUD_PENDIENTE,
    ESTADO_SOLICITUD_REEMPLAZADA,
    ESTADO_SOLICITUD_RESPONDIDA,
    ESTADO_SOLICITUD_VENCIDA,
    RESPUESTA_CONFIRMA,
    RESPUESTA_NO_ASISTIRA,
    RESPUESTA_SIN_RESPUESTA,
    TIPO_RECORDATORIO,
    TIPO_VISPERA,
    CargoDuplicado,
    EstadoReservaInvalido,
    SecuenciaSimulacionInvalida,
    SolicitudDuplicada,
    SolicitudPendienteNoDisponible,
    enviar_solicitud,
    marcar_hora_sin_respuesta,
    registrar_respuesta,
)
from app.servicios.planificador import PlanificadorCorreos
from app.servicios.reserva import ESTADO_PENDIENTE, bloque_esta_disponible
from app.tiempo import ahora_utc, programado


def configuracion_prueba(**cambios) -> ConfiguracionCorreo:
    valores = dict(
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
    valores.update(cambios)
    return ConfiguracionCorreo(**valores)


class CorreoFalso:
    def __init__(self):
        self.enviados = []

    def configurado(self) -> bool:
        return True

    def motivo_no_configurado(self) -> str | None:
        return None

    def enviar(self, destinatario, asunto, cuerpo_texto, cuerpo_html=None) -> str:
        self.enviados.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "texto": cuerpo_texto,
                "html": cuerpo_html,
            }
        )
        return f"<falso-{len(self.enviados)}@example.cl>"


def preparar_datos(conexion):
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
    bloque_id: int = 10,
    fecha: str = "2026-11-12",
    hora_inicio: str = "16:00",
    hora_termino: str = "16:50",
):
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (?, 1, ?, ?, ?, 'presencial')
        """,
        (bloque_id, fecha, hora_inicio, hora_termino),
    )
    conexion.commit()


def insertar_reserva(
    conexion,
    reserva_id: int = 1,
    bloque_id: int = 10,
    estado: str = ESTADO_PENDIENTE,
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


def insertar_solicitud(
    conexion,
    *,
    solicitud_id: int | None = None,
    reserva_id: int = 1,
    tipo: str = TIPO_VISPERA,
    fecha_envio: str = "2026-11-11",
    estado: str = ESTADO_SOLICITUD_PENDIENTE,
    respuesta: str | None = None,
    fecha_respuesta: str | None = None,
    fecha_cierre: str | None = None,
):
    campos = [
        "reserva_id",
        "fecha_envio",
        "tipo",
        "estado",
        "respuesta",
        "fecha_respuesta",
        "fecha_cierre",
    ]
    valores = [
        reserva_id,
        fecha_envio,
        tipo,
        estado,
        respuesta,
        fecha_respuesta,
        fecha_cierre,
    ]
    if solicitud_id is not None:
        campos.insert(0, "id")
        valores.insert(0, solicitud_id)
    conexion.execute(
        f"""
        INSERT INTO solicitud_confirmacion ({", ".join(campos)})
        VALUES ({", ".join("?" for _ in campos)})
        """,
        tuple(valores),
    )
    conexion.commit()


def preparar_reserva_pendiente(conexion, fecha: str = "2026-11-12"):
    preparar_datos(conexion)
    insertar_bloque(conexion, fecha=fecha)
    insertar_reserva(conexion)


def filas_de(conexion, tabla):
    return [
        dict(fila)
        for fila in conexion.execute(f"SELECT * FROM {tabla} ORDER BY id")
    ]


def correos_de(conexion, reserva_id=1):
    return [
        dict(fila)
        for fila in conexion.execute(
            "SELECT * FROM correo_pendiente WHERE reserva_id = ? ORDER BY id",
            (reserva_id,),
        )
    ]


def test_migracion_003_y_restricciones_de_unicidad(conexion):
    preparar_reserva_pendiente(conexion)
    tablas = {
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"solicitud_confirmacion", "cargo"} <= tablas

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
            VALUES (1, '2026-11-11', 'aviso de víspera', 'pendiente')
            """
        )
    conexion.rollback()

    conexion.execute(
        """
        INSERT INTO cargo (paciente_id, reserva_id, monto, motivo, fecha)
        VALUES (1, 1, 5000, 'sin confirmar', '2026-11-12')
        """
    )
    conexion.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO cargo (paciente_id, reserva_id, monto, motivo, fecha)
            VALUES (1, 1, 5000, 'sin confirmar', '2026-11-12')
            """
        )
    conexion.rollback()

    assert conexion.execute(
        "SELECT COUNT(*) FROM solicitud_confirmacion"
    ).fetchone()[0] == 1
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 1


def test_migracion_004_y_005_columnas_y_restricciones(conexion):
    columnas = {
        fila["name"] for fila in conexion.execute(
            "PRAGMA table_info(solicitud_confirmacion)"
        )
    }
    indices = {
        fila["name"]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }
    tablas = {
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"estado", "fecha_respuesta", "fecha_cierre"} <= columnas
    assert "ux_solicitud_pendiente" in indices
    assert {"correo_pendiente", "token_confirmacion"} <= tablas

    preparar_reserva_pendiente(conexion)
    insertar_solicitud(conexion)
    with pytest.raises(sqlite3.IntegrityError):
        insertar_solicitud(
            conexion,
            tipo=TIPO_RECORDATORIO,
            fecha_envio="2026-11-12",
        )
    conexion.rollback()


def test_seed_deja_una_reserva_pendiente_visible(base_temporal):
    cargar_datos_ejemplo(str(base_temporal))
    with TestClient(crear_app(base_temporal, planificador_activo=False)) as cliente:
        respuesta = cliente.get("/reservas/1")

    assert respuesta.status_code == 200
    assert "Pendiente de confirmación" in respuesta.text
    assert "Paciente de Ejemplo" in respuesta.text


def test_enviar_solicitud_de_vispera_encola_correo_y_tokens(conexion):
    preparar_reserva_pendiente(conexion)
    config = configuracion_prueba()
    ahora = programado("2026-11-11", "09:00")

    resultado = enviar_solicitud(
        conexion, 1, TIPO_VISPERA, configuracion=config, ahora=ahora
    )

    assert resultado["solicitud"]["tipo"] == TIPO_VISPERA
    assert resultado["solicitud"]["fecha_envio"] == "2026-11-11"
    assert resultado["solicitud"]["estado"] == ESTADO_SOLICITUD_PENDIENTE
    assert resultado["solicitud"]["respuesta"] is None
    assert resultado["solicitud"]["fecha_respuesta"] is None
    assert resultado["solicitud"]["fecha_cierre"] is None
    assert set(resultado["tokens"]) == {"confirmar", "cancelar"}
    assert len(resultado["tokens"]["confirmar"]) >= 32

    correo = correos_de(conexion)[0]
    assert correo["tipo"] == "solicitud_confirmacion"
    assert correo["destinatario"] == "uno@example.cl"
    assert correo["estado"] == "pendiente"
    assert "/respuesta/confirmar/" in correo["cuerpo_texto"]
    assert "/respuesta/cancelar/" in correo["cuerpo_texto"]

    tokens = conexion.execute("SELECT * FROM token_confirmacion").fetchall()
    assert len(tokens) == 2
    assert all(fila["token_hash"] for fila in tokens)
    assert resultado["tokens"]["confirmar"] not in {
        fila["token_hash"] for fila in tokens
    }


def test_recordatorio_reemplaza_y_cancela_correo_anterior(conexion):
    preparar_reserva_pendiente(conexion)
    config = configuracion_prueba()

    with pytest.raises(SecuenciaSimulacionInvalida):
        enviar_solicitud(conexion, 1, TIPO_RECORDATORIO, configuracion=config)

    enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=config,
        ahora=programado("2026-11-11", "09:00"),
    )
    resultado = enviar_solicitud(
        conexion,
        1,
        TIPO_RECORDATORIO,
        configuracion=config,
        ahora=programado("2026-11-12", "08:00"),
    )

    assert resultado["solicitud"]["tipo"] == TIPO_RECORDATORIO
    assert resultado["solicitud"]["fecha_envio"] == "2026-11-12"
    solicitudes = conexion.execute(
        "SELECT tipo, estado, fecha_cierre FROM solicitud_confirmacion ORDER BY id"
    ).fetchall()
    assert [fila["tipo"] for fila in solicitudes] == [
        TIPO_VISPERA,
        TIPO_RECORDATORIO,
    ]
    assert solicitudes[0]["estado"] == ESTADO_SOLICITUD_REEMPLAZADA
    assert solicitudes[0]["fecha_cierre"] == "2026-11-12"
    assert solicitudes[1]["estado"] == ESTADO_SOLICITUD_PENDIENTE
    assert conexion.execute(
        "SELECT COUNT(*) FROM solicitud_confirmacion WHERE estado = 'pendiente'"
    ).fetchone()[0] == 1
    correos = correos_de(conexion)
    assert [correo["estado"] for correo in correos] == ["cancelado", "pendiente"]

    with pytest.raises(SolicitudDuplicada):
        enviar_solicitud(conexion, 1, TIPO_RECORDATORIO, configuracion=config)


def test_registrar_respuesta_confirma(conexion):
    preparar_reserva_pendiente(conexion)
    solicitud = enviar_solicitud(conexion, 1, TIPO_VISPERA, configuracion=configuracion_prueba())
    marcar_enviado(conexion, solicitud["correo"]["id"], "smtp-prueba", programado("2026-11-11", "09:00"))

    resultado = registrar_respuesta(
        conexion, 1, RESPUESTA_CONFIRMA, ahora=programado("2026-11-12", "09:00"),
    )

    assert resultado["reserva"]["estado"] == "Confirmada"
    assert resultado["respuesta"] == RESPUESTA_CONFIRMA
    assert resultado["fecha_respuesta"]
    solicitud = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()
    assert solicitud["estado"] == ESTADO_SOLICITUD_RESPONDIDA
    assert solicitud["respuesta"] == RESPUESTA_CONFIRMA
    assert solicitud["fecha_respuesta"] == resultado["fecha_respuesta"]
    assert solicitud["fecha_cierre"] is None

    with pytest.raises(EstadoReservaInvalido):
        registrar_respuesta(conexion, 1, RESPUESTA_NO_ASISTIRA)
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == "Confirmada"


def test_registrar_respuesta_no_asistira_libera_bloque(conexion):
    preparar_reserva_pendiente(conexion)
    solicitud = enviar_solicitud(conexion, 1, TIPO_VISPERA, configuracion=configuracion_prueba())
    marcar_enviado(conexion, solicitud["correo"]["id"], "smtp-prueba", programado("2026-11-11", "09:00"))

    resultado = registrar_respuesta(
        conexion, 1, RESPUESTA_NO_ASISTIRA, ahora=programado("2026-11-12", "09:00"),
    )

    assert resultado["reserva"]["estado"] == "Cancelada"
    assert bloque_esta_disponible(conexion, 10) is True
    solicitud = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()
    assert solicitud["estado"] == ESTADO_SOLICITUD_RESPONDIDA
    assert solicitud["respuesta"] == RESPUESTA_NO_ASISTIRA
    cargo = conexion.execute(
        "SELECT monto, motivo FROM cargo WHERE reserva_id = 1"
    ).fetchone()
    assert dict(cargo) == {"monto": 5000, "motivo": "cancelación"}


def test_marcar_hora_sin_respuesta_crea_cargo_y_correo(conexion):
    preparar_reserva_pendiente(conexion)
    config = configuracion_prueba()
    vispera = enviar_solicitud(conexion, 1, TIPO_VISPERA, configuracion=config)
    marcar_enviado(conexion, vispera["correo"]["id"], "smtp-prueba", programado("2026-11-11", "09:00"))
    enviar_solicitud(conexion, 1, TIPO_RECORDATORIO, configuracion=config)

    resultado = marcar_hora_sin_respuesta(conexion, 1, configuracion=config)

    assert resultado["reserva"]["estado"] == "Sin confirmar"
    cargo = conexion.execute("SELECT * FROM cargo WHERE reserva_id = 1").fetchone()
    assert cargo["monto"] == 5000
    assert cargo["motivo"] == "sin confirmar"
    assert cargo["paciente_id"] == 1
    assert cargo["fecha"] == "2026-11-12"

    visa = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE tipo = ?", (TIPO_VISPERA,)
    ).fetchone()
    recordatorio = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE tipo = ?",
        (TIPO_RECORDATORIO,),
    ).fetchone()
    assert visa["estado"] == ESTADO_SOLICITUD_REEMPLAZADA
    assert recordatorio["estado"] == ESTADO_SOLICITUD_VENCIDA
    assert recordatorio["respuesta"] == RESPUESTA_SIN_RESPUESTA
    assert recordatorio["fecha_respuesta"] is None
    assert recordatorio["fecha_cierre"] == "2026-11-12T16:00"

    aviso_cargo = [
        correo for correo in correos_de(conexion) if correo["tipo"] == "aviso_cargo"
    ]
    assert len(aviso_cargo) == 1
    assert aviso_cargo[0]["estado"] == "pendiente"
    assert "$5.000" in aviso_cargo[0]["cuerpo_texto"]

    with pytest.raises(CargoDuplicado):
        marcar_hora_sin_respuesta(conexion, 1, configuracion=config)
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 1


@pytest.mark.parametrize("estado_correo", ["pendiente", "fallido", "omitido"])
def test_planificador_cierra_sin_cargo_si_smtp_no_acepto(
    base_temporal, conexion, estado_correo,
):
    preparar_reserva_pendiente(conexion)
    if estado_correo == "omitido":
        conexion.execute("UPDATE paciente SET correo = NULL WHERE id = 1")
        conexion.commit()
    config = configuracion_prueba()
    solicitud = enviar_solicitud(
        conexion, 1, TIPO_VISPERA, configuracion=config,
        ahora=programado("2026-11-11", "09:00"),
    )
    if estado_correo == "fallido":
        conexion.execute(
            "UPDATE correo_pendiente SET estado = 'fallido' WHERE id = ?",
            (solicitud["correo"]["id"],),
        )
        conexion.commit()

    correo = CorreoFalso()
    planificador = PlanificadorCorreos(str(base_temporal), correo, config)
    inicio = programado("2026-11-12", "16:00")
    planificador.ejecutar_ciclo(inicio)
    planificador.ejecutar_ciclo(inicio)

    assert conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()[0] == "Sin confirmar"
    assert tuple(conexion.execute(
        "SELECT estado, respuesta FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()) == ("vencida", "sin respuesta")
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0
    assert conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE tipo = 'aviso_cargo'"
    ).fetchone()[0] == 0
    assert correo.enviados == []


def test_operaciones_invalidas_no_modifican_datos(conexion):
    preparar_datos(conexion)
    insertar_bloque(conexion, 10)
    insertar_bloque(conexion, 11, "2026-11-13", "10:00", "10:50")
    insertar_reserva(conexion, 1, 10, "Confirmada")
    insertar_reserva(conexion, 2, 11, ESTADO_PENDIENTE)

    with pytest.raises(EstadoReservaInvalido):
        registrar_respuesta(conexion, 1, RESPUESTA_CONFIRMA)
    with pytest.raises(SolicitudPendienteNoDisponible):
        marcar_hora_sin_respuesta(conexion, 2)
    with pytest.raises(SolicitudPendienteNoDisponible):
        registrar_respuesta(conexion, 2, RESPUESTA_CONFIRMA)

    estado = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert estado["estado"] == "Confirmada"
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0
    assert conexion.execute("SELECT COUNT(*) FROM solicitud_confirmacion").fetchone()[0] == 0


def test_confirmacion_por_enlace_seguro(base_temporal, conexion):
    preparar_reserva_pendiente(conexion, fecha="2026-12-10")
    config = configuracion_prueba()
    resultado = enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=config,
    )
    marcar_enviado(conexion, resultado["correo"]["id"], "smtp-prueba", programado("2026-11-09", "08:00"))
    token = resultado["tokens"]["confirmar"]

    with ClienteSinPermisos(
        crear_app(
            base_temporal,
            servicio_correo=CorreoFalso(),
            configuracion=config,
            planificador_activo=False,
        )
    ) as cliente:
        pagina = cliente.get(f"/respuesta/confirmar/{token}")
        assert cliente.get("/reservas/1").status_code == 403
        assert cliente.post("/reservas/1/confirmar").status_code == 403
        respuesta = cliente.post(
            f"/respuesta/confirmar/{token}", follow_redirects=False
        )
        reutilizado = cliente.get(f"/respuesta/confirmar/{token}")
        assert cliente.get("/reservas/1").status_code == 200

    assert pagina.status_code == 200
    assert "Confirmar asistencia" in pagina.text
    assert respuesta.status_code == 303
    assert reutilizado.status_code == 409
    assert "ya fue utilizado" in reutilizado.text
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == "Confirmada"


def test_cancelacion_por_enlace_seguro(base_temporal, conexion):
    preparar_reserva_pendiente(conexion, fecha="2026-12-10")
    config = configuracion_prueba()
    resultado = enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=config,
    )
    marcar_enviado(conexion, resultado["correo"]["id"], "smtp-prueba", programado("2026-11-09", "08:00"))
    token = resultado["tokens"]["cancelar"]

    with TestClient(
        crear_app(
            base_temporal,
            servicio_correo=CorreoFalso(),
            configuracion=config,
            planificador_activo=False,
        )
    ) as cliente:
        pagina = cliente.get(f"/respuesta/cancelar/{token}")
        respuesta = cliente.post(
            f"/respuesta/cancelar/{token}", follow_redirects=False
        )

    assert pagina.status_code == 200
    assert respuesta.status_code == 303
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == "Cancelada"
    assert bloque_esta_disponible(conexion, 10) is True
    aviso = conexion.execute(
        "SELECT cuerpo_texto FROM correo_pendiente "
        "WHERE reserva_id = 1 AND tipo = 'aviso_cargo'"
    ).fetchone()
    assert "Se registró la cancelación" in aviso["cuerpo_texto"]


def test_token_vencido_y_accion_incorrecta(base_temporal, conexion, monkeypatch):
    from app.rutas import reserva as ruta_reserva

    monkeypatch.setattr(
        ruta_reserva, "ahora_utc", lambda: programado("2026-11-12", "16:00"),
    )
    preparar_reserva_pendiente(conexion)
    config = configuracion_prueba()
    vencida = enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=config,
        ahora=programado("2026-11-11", "09:00"),
    )

    insertar_bloque(conexion, 11, "2026-12-10", "16:00", "16:50")
    insertar_reserva(conexion, 2, 11)
    vigente = enviar_solicitud(
        conexion,
        2,
        TIPO_VISPERA,
        configuracion=config,
    )
    marcar_enviado(conexion, vigente["correo"]["id"], "smtp-prueba", programado("2026-11-12", "08:00"))

    with TestClient(
        crear_app(
            base_temporal,
            servicio_correo=CorreoFalso(),
            configuracion=config,
            planificador_activo=False,
        )
    ) as cliente:
        vencido = cliente.post(
            f"/respuesta/confirmar/{vencida['tokens']['confirmar']}",
            follow_redirects=False,
        )
        accion = cliente.get(
            f"/respuesta/cancelar/{vigente['tokens']['confirmar']}"
        )

    assert vencido.status_code == 409
    assert "venció" in vencido.text
    assert accion.status_code == 409
    assert "no corresponde" in accion.text
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == ESTADO_PENDIENTE


def test_planificador_envia_vispera_recordatorio_y_vence(base_temporal, conexion):
    preparar_datos(conexion)
    insertar_bloque(conexion, 10, "2026-12-10", "16:00", "16:50")
    insertar_reserva(conexion)
    config = configuracion_prueba()
    correo = CorreoFalso()
    planificador = PlanificadorCorreos(str(base_temporal), correo, config)

    vispera = programado("2026-12-09", "09:00")
    planificador.ejecutar_ciclo(vispera)
    planificador.ejecutar_ciclo(vispera)
    assert conexion.execute(
        "SELECT COUNT(*) FROM solicitud_confirmacion"
    ).fetchone()[0] == 1
    assert conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE tipo = 'solicitud_confirmacion'"
    ).fetchone()[0] == 1

    recordatorio = programado("2026-12-10", "08:00")
    planificador.ejecutar_ciclo(recordatorio)
    planificador.ejecutar_ciclo(recordatorio)
    solicitudes = conexion.execute(
        "SELECT tipo, estado FROM solicitud_confirmacion ORDER BY id"
    ).fetchall()
    assert [fila["tipo"] for fila in solicitudes] == [
        TIPO_VISPERA,
        TIPO_RECORDATORIO,
    ]
    assert [fila["estado"] for fila in solicitudes] == [
        ESTADO_SOLICITUD_REEMPLAZADA,
        ESTADO_SOLICITUD_PENDIENTE,
    ]
    assert conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE tipo = 'solicitud_confirmacion'"
    ).fetchone()[0] == 2

    atencion = programado("2026-12-10", "16:00")
    planificador.ejecutar_ciclo(atencion)
    planificador.ejecutar_ciclo(atencion)
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == "Sin confirmar"
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 1
    assert conexion.execute(
        "SELECT COUNT(*) FROM correo_pendiente WHERE tipo = 'aviso_cargo'"
    ).fetchone()[0] == 1
    assert len(correo.enviados) == 3
    assert conexion.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []


def test_detalle_muestra_estado_de_correos_y_recordatorio(base_temporal, conexion):
    preparar_reserva_pendiente(conexion)
    config = configuracion_prueba()
    solicitud = enviar_solicitud(
        conexion,
        1,
        TIPO_VISPERA,
        configuracion=config,
        ahora=programado("2026-11-11", "09:00"),
    )

    with TestClient(
        crear_app(
            base_temporal,
            servicio_correo=CorreoFalso(),
            configuracion=config,
            planificador_activo=False,
        )
    ) as cliente:
        respuesta = cliente.get("/reservas/1")
        assert cliente.post("/reservas/1/confirmar").status_code == 409
        token = solicitud["tokens"]["confirmar"]
        assert cliente.get(f"/respuesta/confirmar/{token}").status_code == 409
        marcar_enviado(conexion, solicitud["correo"]["id"], "smtp-prueba", programado("2026-11-09", "08:00"))
        detalle_enviado = cliente.get("/reservas/1")

    assert respuesta.status_code == 200
    assert "Estado de las notificaciones por correo" in respuesta.text
    assert "uno@example.cl" in respuesta.text
    assert "Pendiente de envío" in respuesta.text
    assert "Recordatorio programado" in respuesta.text
    assert "2026-11-12 08:00" in respuesta.text
    assert 'action="/reservas/1/confirmar"' not in respuesta.text
    assert 'action="/reservas/1/no-asistir"' not in respuesta.text
    assert 'action="/reservas/1/confirmar"' in detalle_enviado.text
    assert 'action="/reservas/1/no-asistir"' in detalle_enviado.text
    assert "Enviar solicitud (víspera)" not in respuesta.text
    assert "Simulación de tiempo" not in respuesta.text


def test_detalle_sin_solicitud_no_muestra_acciones(base_temporal, conexion):
    preparar_reserva_pendiente(conexion)

    with TestClient(
        crear_app(
            base_temporal,
            servicio_correo=CorreoFalso(),
            configuracion=configuracion_prueba(),
            planificador_activo=False,
        )
    ) as cliente:
        respuesta = cliente.get("/reservas/1")

    assert respuesta.status_code == 200
    assert "Pendiente de confirmación" in respuesta.text
    assert "Confirmar asistencia" not in respuesta.text
    assert "No asistiré" not in respuesta.text
    assert "No hay correos registrados" in respuesta.text


def test_respuesta_sin_solicitud_pendiente_devuelve_409(base_temporal, conexion):
    preparar_reserva_pendiente(conexion)

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        respuesta = cliente.post(
            "/reservas/1/confirmar", follow_redirects=False
        )

    assert respuesta.status_code == 409
    assert "No existe una solicitud de confirmación pendiente" in respuesta.text
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == ESTADO_PENDIENTE
    assert conexion.execute("SELECT COUNT(*) FROM solicitud_confirmacion").fetchone()[0] == 0
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0


def test_respuesta_a_solicitud_respondida_no_cambia_datos(base_temporal, conexion):
    preparar_reserva_pendiente(conexion)
    insertar_solicitud(
        conexion,
        estado=ESTADO_SOLICITUD_RESPONDIDA,
        respuesta=RESPUESTA_CONFIRMA,
        fecha_respuesta="2026-11-11T18:00:00",
    )
    solicitud_antes = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        respuesta = cliente.post(
            "/reservas/1/no-asistir", follow_redirects=False
        )

    assert respuesta.status_code == 409
    assert "ya fue respondida" in respuesta.text
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == ESTADO_PENDIENTE
    solicitud_despues = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()
    assert dict(solicitud_despues) == dict(solicitud_antes)
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0


@pytest.mark.parametrize("estado", [ESTADO_SOLICITUD_REEMPLAZADA, ESTADO_SOLICITUD_VENCIDA])
def test_respuesta_a_solicitud_reemplazada_o_vencida_devuelve_409(
    base_temporal, conexion, estado
):
    preparar_reserva_pendiente(conexion)
    if estado == ESTADO_SOLICITUD_REEMPLAZADA:
        insertar_solicitud(
            conexion,
            estado=estado,
            fecha_cierre="2026-11-12",
        )
    else:
        insertar_solicitud(
            conexion,
            tipo=TIPO_RECORDATORIO,
            fecha_envio="2026-11-12",
            estado=estado,
            respuesta=RESPUESTA_SIN_RESPUESTA,
            fecha_cierre="2026-11-12T16:00",
        )

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        respuesta = cliente.post(
            "/reservas/1/confirmar", follow_redirects=False
        )

    assert respuesta.status_code == 409
    assert "reemplazada" in respuesta.text or "vencida" in respuesta.text
    solicitud = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE reserva_id = 1"
    ).fetchone()
    assert solicitud["estado"] == estado
    reserva = conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()
    assert reserva["estado"] == ESTADO_PENDIENTE
    assert conexion.execute("SELECT COUNT(*) FROM cargo").fetchone()[0] == 0


def test_respuesta_web_al_inicio_se_rechaza_aunque_la_solicitud_siga_pendiente(
    base_temporal, conexion, monkeypatch,
):
    from app.rutas import reserva as ruta_reserva

    preparar_reserva_pendiente(conexion)
    enviar_solicitud(
        conexion, 1, TIPO_VISPERA, configuracion=configuracion_prueba(),
        ahora=programado("2026-11-11", "09:00"),
    )
    monkeypatch.setattr(
        ruta_reserva, "ahora_utc", lambda: programado("2026-11-12", "16:00"),
    )
    with TestClient(crear_app(base_temporal, planificador_activo=False)) as cliente:
        detalle = cliente.get("/reservas/1")
        respuesta = cliente.post("/reservas/1/confirmar")

    assert 'action="/reservas/1/confirmar"' not in detalle.text
    assert respuesta.status_code == 409
    assert "El plazo de respuesta ya venció" in respuesta.text
    assert conexion.execute("SELECT estado FROM reserva WHERE id = 1").fetchone()[0] == (
        "Pendiente de confirmación"
    )


def test_reserva_inexistente_devuelve_404(base_temporal):
    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        detalle = cliente.get("/reservas/999")
        confirmar = cliente.post("/reservas/999/confirmar")
        enlace = cliente.get("/respuesta/confirmar/token-inexistente")
        enlace_post = cliente.post("/respuesta/confirmar/token-inexistente")

    assert detalle.status_code == 404
    assert confirmar.status_code == 404
    assert enlace.status_code == 404
    assert enlace_post.status_code == 404
    assert "Reserva no encontrada" in detalle.text
    assert "Reserva no encontrada" in confirmar.text


def test_respuesta_sobre_reserva_confirmada_no_modifica_datos(
    base_temporal, conexion
):
    preparar_reserva_pendiente(conexion)
    conexion.execute(
        "UPDATE reserva SET estado = ? WHERE id = 1", ("Confirmada",)
    )
    conexion.commit()
    insertar_solicitud(
        conexion,
        estado=ESTADO_SOLICITUD_RESPONDIDA,
        respuesta=RESPUESTA_CONFIRMA,
        fecha_respuesta="2026-11-11T18:00:00",
    )
    tablas = ("reserva", "solicitud_confirmacion", "cargo", "bloque_horario")
    antes = {tabla: filas_de(conexion, tabla) for tabla in tablas}

    with TestClient(
        crear_app(base_temporal, planificador_activo=False)
    ) as cliente:
        confirmar = cliente.post(
            "/reservas/1/confirmar", follow_redirects=False
        )
        no_asistir = cliente.post(
            "/reservas/1/no-asistir", follow_redirects=False
        )

    assert confirmar.status_code == 409
    assert no_asistir.status_code == 409
    assert "ya no está en estado Pendiente de confirmación" in confirmar.text
    assert "ya no está en estado Pendiente de confirmación" in no_asistir.text
    despues = {tabla: filas_de(conexion, tabla) for tabla in tablas}
    assert despues == antes
