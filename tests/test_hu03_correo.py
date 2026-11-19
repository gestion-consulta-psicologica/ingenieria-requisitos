from __future__ import annotations

import socket
from datetime import timedelta

from app.configuracion import ConfiguracionCorreo
from app.servicios import cola_correo
from app.servicios.correo import ServicioCorreoSMTP
from app.servicios.planificador import PlanificadorCorreos
from app.tiempo import ahora_utc, iso_utc, programado
from tests.smtp_falso import ServidorSMTPFalso


def configuracion_smtp(
    *,
    host: str = "127.0.0.1",
    puerto: int = 25,
    usuario: str | None = None,
    clave: str | None = None,
    seguridad: str = "ninguna",
    max_intentos: int = 3,
    reintento_base_segundos: int = 1,
) -> ConfiguracionCorreo:
    return ConfiguracionCorreo(
        smtp_host=host,
        smtp_puerto=puerto,
        smtp_usuario=usuario,
        smtp_clave=clave,
        smtp_remitente="consultas@example.cl",
        smtp_seguridad=seguridad,
        smtp_timeout=5,
        url_publica="http://testserver",
        max_intentos=max_intentos,
        reintento_base_segundos=reintento_base_segundos,
        planificador_activo=False,
        intervalo_planificador_segundos=60,
        timeout_envio_segundos=300,
        hora_vispera="09:00",
        hora_recordatorio="08:00",
        zona_horaria="America/Santiago",
    )


def preparar_base(conexion):
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
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (10, 1, '2026-12-10', '16:00', '16:50', 'presencial')
        """
    )
    conexion.execute(
        """
        INSERT INTO reserva (id, paciente_id, bloque_horario_id, fecha_registro, estado)
        VALUES (1, 1, 10, '2026-11-01T09:00:00', 'Pendiente de confirmación')
        """
    )
    conexion.commit()


def encolar_aviso(conexion, configuracion, ahora=None):
    fila = cola_correo.encolar(
        conexion,
        clave="aviso:1",
        tipo=cola_correo.TIPO_AVISO_RESERVA,
        asunto="Reserva registrada",
        cuerpo_texto="Hola, tu reserva quedó registrada.",
        cuerpo_html="<p>Hola, tu reserva quedó registrada.</p>",
        destinatario="uno@example.cl",
        reserva_id=1,
        solicitud_id=None,
        creado_en=ahora or ahora_utc(),
        max_intentos=configuracion.max_intentos,
    )
    conexion.commit()
    return fila


def estado_correo(conexion, correo_id):
    return conexion.execute(
        "SELECT * FROM correo_pendiente WHERE id = ?", (correo_id,)
    ).fetchone()


def puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_envio_smtp_exitoso(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso()
    try:
        config = configuracion_smtp(puerto=servidor.puerto)
        correo = encolar_aviso(conexion, config)
        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

        fila = estado_correo(conexion, correo["id"])
        assert fila["estado"] == "enviado"
        assert fila["enviado_en"] is not None
        assert fila["id_mensaje"]
        assert len(servidor.mensajes) == 1
        assert "uno@example.cl" in servidor.mensajes[0]
        assert "Reserva registrada" in servidor.mensajes[0]
    finally:
        servidor.cerrar()


def test_error_de_conexion_y_reintento(base_temporal, conexion):
    preparar_base(conexion)
    config_malo = configuracion_smtp(
        puerto=puerto_libre(), max_intentos=3, reintento_base_segundos=1
    )
    correo = encolar_aviso(conexion, config_malo)
    planificador = PlanificadorCorreos(
        str(base_temporal), ServicioCorreoSMTP(config_malo), config_malo
    )
    ahora = programado("2026-12-01", "00:00")
    planificador.ejecutar_ciclo(ahora)

    fila = estado_correo(conexion, correo["id"])
    assert fila["estado"] == "pendiente"
    assert fila["intentos"] == 1
    assert "conectar" in fila["ultimo_error"].lower()

    servidor = ServidorSMTPFalso()
    try:
        config_bueno = configuracion_smtp(puerto=servidor.puerto)
        planificador.servicio_correo = ServicioCorreoSMTP(config_bueno)
        planificador.configuracion = config_bueno
        planificador.ejecutar_ciclo(ahora + timedelta(seconds=60))

        fila = estado_correo(conexion, correo["id"])
        assert fila["estado"] == "enviado"
        assert len(servidor.mensajes) == 1
    finally:
        servidor.cerrar()


def test_credenciales_incorrectas(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso(
        usuario="usuario-correcto", clave="clave-correcta", requerir_auth=True
    )
    try:
        config = configuracion_smtp(
            puerto=servidor.puerto,
            usuario="usuario-incorrecto",
            clave="clave-incorrecta",
        )
        correo = encolar_aviso(conexion, config)
        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

        fila = estado_correo(conexion, correo["id"])
        assert fila["estado"] == "fallido"
        assert "credenciales" in fila["ultimo_error"].lower()
        assert servidor.mensajes == []
    finally:
        servidor.cerrar()


def test_destinatario_rechazado_se_registra_como_error_de_envio(
    base_temporal, conexion
):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso(rechazar_destinatario=True)
    try:
        config = configuracion_smtp(puerto=servidor.puerto, max_intentos=1)
        correo = encolar_aviso(conexion, config)
        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

        fila = estado_correo(conexion, correo["id"])
        assert fila["estado"] == "fallido"
        assert "rechaz" in fila["ultimo_error"].lower()
        assert "conectar" not in fila["ultimo_error"].lower()
        assert servidor.mensajes == []
    finally:
        servidor.cerrar()


def test_smtp_no_configurado_nunca_marca_envio_exitoso(base_temporal, conexion):
    preparar_base(conexion)
    config = configuracion_smtp(host=None, puerto=2525)
    correo = encolar_aviso(conexion, config)
    planificador = PlanificadorCorreos(
        str(base_temporal), ServicioCorreoSMTP(config), config
    )
    planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

    fila = estado_correo(conexion, correo["id"])
    assert fila["estado"] != "enviado"
    assert "no configurado" in fila["ultimo_error"].lower()
    assert fila["enviado_en"] is None


def test_recuperacion_de_trabajo_enviando_tras_reinicio(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso()
    try:
        config = configuracion_smtp(puerto=servidor.puerto)
        correo = encolar_aviso(conexion, config)
        conexion.execute(
            """
            UPDATE correo_pendiente
            SET estado = 'enviando', actualizado_en = ?
            WHERE id = ?
            """,
            (iso_utc(ahora_utc() - timedelta(hours=1)), correo["id"]),
        )
        conexion.commit()

        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        resultado = planificador.ejecutar_ciclo(ahora_utc())

        fila = estado_correo(conexion, correo["id"])
        assert resultado["recuperados"] == 1
        assert fila["estado"] == "enviado"
        assert len(servidor.mensajes) == 1
    finally:
        servidor.cerrar()


def test_recuperacion_de_trabajo_pendiente_tras_reinicio(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso()
    try:
        config = configuracion_smtp(puerto=servidor.puerto)
        correo = encolar_aviso(conexion, config)
        assert estado_correo(conexion, correo["id"])["estado"] == "pendiente"

        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

        assert estado_correo(conexion, correo["id"])["estado"] == "enviado"
        assert len(servidor.mensajes) == 1
    finally:
        servidor.cerrar()


def test_prevencion_de_correos_duplicados(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso()
    try:
        config = configuracion_smtp(puerto=servidor.puerto)
        encolar_aviso(conexion, config)
        encolar_aviso(conexion, config)
        assert conexion.execute(
            "SELECT COUNT(*) FROM correo_pendiente"
        ).fetchone()[0] == 1

        planificador = PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        )
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))
        planificador.ejecutar_ciclo(programado("2026-12-01", "00:00"))

        assert len(servidor.mensajes) == 1
        assert conexion.execute(
            "SELECT COUNT(*) FROM correo_pendiente WHERE estado = 'enviado'"
        ).fetchone()[0] == 1
    finally:
        servidor.cerrar()


def test_integridad_de_datos_tras_envios(base_temporal, conexion):
    preparar_base(conexion)
    servidor = ServidorSMTPFalso()
    try:
        config = configuracion_smtp(puerto=servidor.puerto)
        encolar_aviso(conexion, config)
        PlanificadorCorreos(
            str(base_temporal), ServicioCorreoSMTP(config), config
        ).ejecutar_ciclo(programado("2026-12-01", "00:00"))

        assert conexion.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        servidor.cerrar()
