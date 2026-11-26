from dataclasses import replace
from email import policy
from email.parser import Parser
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app import demo
from app.configuracion import cargar_configuracion
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.rutas import disponibilidad as ruta_disponibilidad
from app.rutas import psicologa, reserva as ruta_reserva
from app.servicios import confirmacion, disponibilidad, reagendamiento
from app.servicios.planificador import PlanificadorCorreos
from app.servicios.atenciones import registrar_comprobante
from app.tiempo import programado
from tests.smtp_falso import ServidorSMTPFalso
from tests.acceso_demo import cliente_con_reservas


@pytest.mark.parametrize("bloques_por_hora", [False, True])
def test_arranque_demo_usa_una_base_temporal_y_sin_smtp_externo(
    tmp_path, monkeypatch, bloques_por_hora,
):
    ruta_alternativa = tmp_path / "configurada.db"
    monkeypatch.setenv("CONSULTA_DB", str(ruta_alternativa))
    monkeypatch.setenv("SMTP_HOST", "externo.example.test")
    monkeypatch.setenv("SMTP_REMITENTE", "consulta@example.test")
    monkeypatch.setattr(demo, "ahora_local", lambda _: programado("2026-11-09", "08:00"))
    rutas = []

    def revisar_arranque(app, *, host, port):
        ruta = Path(app.state.ruta_db)
        rutas.append(ruta)
        assert ruta.name == "demo.db" and ruta.parent.name.startswith("consulta-demo-")
        assert ruta.is_file() and ruta != ruta_alternativa
        assert host == "127.0.0.1" and port == 8000
        # El demo ignora el SMTP del entorno y usa el correo local de consola.
        assert isinstance(app.state.servicio_correo, demo.ServicioCorreoDemo)
        assert app.state.configuracion_correo.smtp_host is None
        cliente = TestClient(app)
        assert 'href="/psicologa"' in cliente.get("/").text
        reserva = cliente.get("/reservas/1", auth=("paciente", app.state.clave_paciente_demo))
        assert reserva.status_code == 200
        # Antes de que el planificador entregue la solicitud no se puede responder.
        assert 'action="/reservas/1/confirmar"' not in reserva.text
        if bloques_por_hora:
            semana = cliente.get("/disponibilidad?semana=2026-11-16")
            assert semana.text.count("data-bloque-id=") == 59
            assert "09:00 a 09:50" in semana.text
            assert "18:00 a 18:50" in semana.text
            assert "domingo" not in semana.text.lower()

    monkeypatch.setattr(demo.uvicorn, "run", revisar_arranque)
    demo.main(bloques_por_hora=bloques_por_hora)

    assert len(rutas) == 1
    assert not rutas[0].exists()
    assert not ruta_alternativa.exists()


def test_correo_demo_entrega_la_solicitud_y_habilita_la_respuesta(
    base_temporal, conexion, capsys,
):
    cargar_datos_ejemplo(str(base_temporal))
    configuracion = replace(
        cargar_configuracion(), smtp_host=None, smtp_remitente=None,
        url_publica=demo.URL_DEMO,
    )
    ahora = programado("2026-11-09", "09:30")
    confirmacion.enviar_solicitud(
        conexion, 1, confirmacion.TIPO_VISPERA, configuracion=configuracion, ahora=ahora,
    )
    PlanificadorCorreos(
        str(base_temporal), demo.ServicioCorreoDemo(), configuracion,
    ).ejecutar_ciclo(ahora)

    salida = capsys.readouterr().out
    assert "[CORREO DEMO" in salida
    assert f"{demo.URL_DEMO}/respuesta/confirmar/" in salida
    correo = conexion.execute(
        "SELECT estado, id_mensaje FROM correo_pendiente WHERE tipo = 'solicitud_confirmacion'"
    ).fetchone()
    assert correo["estado"] == "enviado" and correo["id_mensaje"]

    resultado = confirmacion.registrar_respuesta(
        conexion, 1, confirmacion.RESPUESTA_CONFIRMA,
        ahora=ahora, configuracion=configuracion,
    )
    assert resultado["reserva"]["estado"] == "Confirmada"


def test_titularidad_de_reservas_y_comprobantes(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    app = crear_app(
        base_temporal, clave_psicologa_demo="clave-admin", clave_paciente_demo="clave-paciente",
    )
    admin = ("psicologa", "clave-admin")
    titular = ("paciente", "clave-paciente")
    comprobante_ajeno = "/pagos/2/comprobante"
    datos = {"monto": "30000", "fecha_transferencia": "2026-11-12", "cuenta_destino": "Sintética"}
    with TestClient(app) as cliente:
        assert cliente.get("/reservas/3").status_code == 403
        assert cliente.post("/reservar/2", data={"rut": "22.222.222-2"}).status_code == 401
        assert cliente.post("/pacientes/registro", data={"rut": "22.222.222-2"}).status_code == 401
        assert cliente.get("/reservas/3", auth=titular).status_code == 200
        assert cliente.get("/pagos/1/comprobante", auth=titular).status_code == 200
        assert cliente.get("/reservas/4", auth=titular).status_code == 403
        assert cliente.get(comprobante_ajeno, auth=titular).status_code == 403
        assert cliente.post(comprobante_ajeno, auth=titular, data=datos).status_code == 403
        assert cliente.post("/reservas/4/cancelar", auth=admin).status_code == 403
        assert cliente.get("/reservas/4", auth=admin).status_code == 200
        assert cliente.get("/pagos", auth=titular).status_code == 401
        assert cliente.get("/pagos/2", auth=admin).status_code == 200
        reserva = cliente.post(
            "/reservar/2", auth=titular, data={"rut": "22.222.222-2"}, follow_redirects=False,
        )
        assert reserva.status_code == 303
        assert "HttpOnly" in reserva.headers["set-cookie"]
        assert cliente.get(reserva.headers["location"]).status_code == 200
        assert TestClient(app).get(reserva.headers["location"]).status_code == 403

    assert conexion.execute(
        "SELECT COUNT(*) FROM comprobante_transferencia WHERE pago_id = 2"
    ).fetchone()[0] == 0


def test_get_pagos_sin_clave_administrativa_no_publica_datos(base_temporal):
    with TestClient(crear_app(base_temporal)) as cliente:
        assert cliente.get("/pagos").status_code == 404
        assert cliente.get("/pagos/1").status_code == 404


def test_psicologa_agrega_disponibilidad_en_la_misma_base(
    base_temporal, monkeypatch,
):
    cargar_datos_ejemplo(str(base_temporal))
    monkeypatch.setattr(psicologa, "ahora_utc", lambda: programado("2026-11-09", "08:00"))
    app = crear_app(base_temporal, clave_psicologa_demo="clave-de-prueba")
    credenciales = ("psicologa", "clave-de-prueba")
    campos = {
        "fecha": "2026-11-14", "inicio": "18:10", "termino": "19:00",
        "modalidad": "online", "csrf": app.state.csrf_psicologa_demo,
    }
    with TestClient(app) as cliente:
        assert 'href="/psicologa"' in cliente.get("/").text
        assert cliente.get("/psicologa").status_code == 401
        assert cliente.post("/psicologa/horarios", data=campos).status_code == 401
        invalido = cliente.post(
            "/psicologa/horarios", auth=credenciales,
            data={**campos, "csrf": "invalido"},
        )
        assert invalido.status_code == 403
        domingo = cliente.post(
            "/psicologa/horarios", auth=credenciales,
            data={**campos, "fecha": "2026-11-15"},
        )
        assert domingo.status_code == 400
        duracion_invalida = cliente.post(
            "/psicologa/horarios", auth=credenciales,
            data={**campos, "termino": "18:50"},
        )
        assert duracion_invalida.status_code == 400
        assert "50 minutos" in duracion_invalida.json()["detail"]
        panel = cliente.post("/psicologa/horarios", data=campos, auth=credenciales)
        assert panel.url.path == "/psicologa"
        assert 'href="/pagos"' in panel.text
        assert "18:10 a 19:00" in cliente.get("/disponibilidad").text


def test_psicologa_genera_semana_sin_cambiar_reservas_y_sin_duplicar(
    base_temporal, conexion, monkeypatch,
):
    cargar_datos_ejemplo(str(base_temporal))
    ahora = programado("2026-11-09", "08:00")
    monkeypatch.setattr(psicologa, "ahora_utc", lambda: ahora)
    reservas = [tuple(fila) for fila in conexion.execute("SELECT * FROM reserva ORDER BY id")]
    bloques = [tuple(fila) for fila in conexion.execute("SELECT * FROM bloque_horario ORDER BY id")]
    app = crear_app(base_temporal, clave_psicologa_demo="clave-prueba")
    admin = ("psicologa", "clave-prueba")
    ruta = "/psicologa/horarios/generar"
    formulario = {
        "semana": "2026-11-10", "modalidad": "online",
        "csrf": app.state.csrf_psicologa_demo,
    }

    with TestClient(app) as cliente:
        assert cliente.post(ruta, data=formulario).status_code == 401
        sin_csrf = cliente.post(ruta, auth=admin, data={**formulario, "csrf": "inválido"})
        assert sin_csrf.status_code == 403
        panel = cliente.post(ruta, auth=admin, data=formulario)
        assert "Bloques agregados: 56." in panel.text
        semana = cliente.get("/disponibilidad?semana=2026-11-10")
        assert semana.text.count("data-bloque-id=") == 57
        assert 'data-bloque-id="1"' not in semana.text
        assert 'data-bloque-id="5"' not in semana.text
        assert 'data-bloque-id="6"' not in semana.text
        assert 'data-bloque-id="2"' in semana.text
        assert "09:00 a 09:50" in semana.text
        assert "18:00 a 18:50" in semana.text
        assert "domingo" not in semana.text.lower()
        repetido = cliente.post(ruta, auth=admin, data={**formulario, "modalidad": "presencial"})
        assert "Bloques agregados: 0." in repetido.text

    assert reservas == [tuple(fila) for fila in conexion.execute("SELECT * FROM reserva ORDER BY id")]
    assert bloques == [
        tuple(fila) for fila in conexion.execute("SELECT * FROM bloque_horario WHERE id <= 6 ORDER BY id")
    ]
    horarios = conexion.execute(
        """
        SELECT fecha, hora_inicio, hora_termino FROM bloque_horario
        WHERE fecha BETWEEN '2026-11-09' AND '2026-11-15'
        ORDER BY fecha, hora_inicio
        """
    ).fetchall()
    assert [tuple(fila) for fila in horarios] == [
        (f"2026-11-{dia:02}", f"{hora:02}:00", f"{hora:02}:50")
        for dia in range(9, 15) for hora in range(9, 19)
    ]


def test_generacion_respeta_bloque_manual_y_permite_reservar_bloque_nuevo(
    base_temporal, conexion, monkeypatch,
):
    cargar_datos_ejemplo(str(base_temporal))
    ahora = programado("2026-11-09", "10:00")
    monkeypatch.setattr(psicologa, "ahora_utc", lambda: ahora)
    monkeypatch.setattr(ruta_disponibilidad, "ahora_utc", lambda: ahora)
    monkeypatch.setattr(disponibilidad, "ahora_utc", lambda: ahora)
    conexion.execute(
        """
        INSERT INTO bloque_horario (psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
        VALUES (1, '2026-11-09', '11:20', '12:10', 'online')
        """
    )
    conexion.commit()
    app = crear_app(
        base_temporal, clave_psicologa_demo="clave-admin", clave_paciente_demo="clave-paciente",
    )
    with TestClient(app) as cliente:
        respuesta = cliente.post(
            "/psicologa/horarios/generar",
            auth=("psicologa", "clave-admin"),
            data={
                "semana": "2026-11-09", "modalidad": "presencial",
                "csrf": app.state.csrf_psicologa_demo,
            },
        )
        assert respuesta.status_code == 200
        lunes = conexion.execute(
            "SELECT id, hora_inicio FROM bloque_horario WHERE fecha = '2026-11-09'"
        ).fetchall()
        ids = {fila["hora_inicio"]: fila["id"] for fila in lunes}
        assert set(ids) == {"11:20", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"}
        destino = f"/reservar/{ids['13:00']}"
        assert f'href="{destino}"' in cliente.get("/disponibilidad").text
        reserva = cliente.post(
            destino, auth=("paciente", "clave-paciente"), data={"rut": "22.222.222-2"},
        )
        assert reserva.status_code == 200
        assert reserva.url.path.startswith("/reservas/")
        assert f'href="{destino}"' not in cliente.get("/disponibilidad").text


def test_psicologa_verifica_pago_parcial_y_completa_el_saldo(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    primer_comprobante = registrar_comprobante(
        conexion, 2, 20000, "2026-11-11", "Cuenta de prueba",
    )
    app = crear_app(base_temporal, clave_psicologa_demo="clave-de-prueba")
    credenciales = ("psicologa", "clave-de-prueba")
    campos = {
        "comprobantes": str(primer_comprobante["id"]),
        "estado": "Pago incompleto",
        "csrf": app.state.csrf_psicologa_demo,
    }
    with cliente_con_reservas(app, 4) as cliente:
        assert cliente.get("/pagos/2").status_code == 401
        detalle = cliente.get("/pagos/2", auth=credenciales)
        assert "Cuenta de prueba" in detalle.text
        assert 'action="/pagos/2/estado"' in detalle.text
        assert 'name="estado" required' in detalle.text
        assert cliente.post("/pagos/2/estado", data=campos).status_code == 401
        incompatible = cliente.post(
            "/pagos/2/estado", data={**campos, "estado": "Pagado"}, auth=credenciales,
        )
        assert incompatible.status_code == 409
        assert "Pago incompleto" in incompatible.json()["detail"]
        assert conexion.execute(
            "SELECT verificado FROM comprobante_transferencia WHERE id = ?",
            (primer_comprobante["id"],),
        ).fetchone()[0] == 0
        parcial = cliente.post("/pagos/2/estado", data=campos, auth=credenciales)
        assert "El estado del pago quedó registrado" in parcial.text
        assert "Pago incompleto" in parcial.text
        assert "$10.000" in parcial.text
        assert 'href="/pagos/2"' in cliente.get("/pagos", auth=credenciales).text
        assert "33.333.333-3" in parcial.text
        repetido = cliente.post("/pagos/2/estado", data=campos, auth=credenciales)
        assert repetido.status_code == 409

        segundo_comprobante = registrar_comprobante(
            conexion, 2, 10000, "2026-11-12", "Cuenta de prueba",
        )
        pagado = cliente.post(
            "/pagos/2/estado", auth=credenciales,
            data={**campos, "estado": "Pagado", "comprobantes": str(segundo_comprobante["id"])},
        )
        assert "Pagado" in pagado.text
        assert "33.333.333-3" in pagado.text
        assert 'href="/pagos/2"' not in cliente.get("/pagos", auth=credenciales).text
        assert cliente.get("/pagos/2/comprobante").status_code == 409

    pagos = conexion.execute(
        """
        SELECT pg.atencion_id, p.rut, pg.estado, pg.monto_pagado
        FROM pago pg
        JOIN atencion a ON a.id = pg.atencion_id
        JOIN reserva r ON r.id = a.reserva_id
        JOIN paciente p ON p.id = r.paciente_id
        ORDER BY pg.atencion_id
        """
    ).fetchall()
    assert [tuple(fila) for fila in pagos] == [
        (1, "22.222.222-2", "Pendiente", 0),
        (2, "33.333.333-3", "Pagado", 30000),
    ]


@pytest.mark.parametrize(
    ("estado", "justificacion", "cargo_esperado"),
    [
        ("realizada", "", False),
        ("inasistencia", "", True),
        ("inasistencia justificada", "Justificación de prueba", False),
    ],
)
def test_psicologa_registra_asistencia_sin_cambiar_el_pago(
    base_temporal, conexion, estado, justificacion, cargo_esperado,
):
    cargar_datos_ejemplo(str(base_temporal))
    app = crear_app(base_temporal, clave_psicologa_demo="clave-de-prueba")
    credenciales = ("psicologa", "clave-de-prueba")
    ruta = "/psicologa/atenciones/1/asistencia"
    datos = {"estado": estado, "justificacion": justificacion, "csrf": app.state.csrf_psicologa_demo}
    with TestClient(app) as cliente:
        assert cliente.post(ruta, data=datos).status_code == 401
        resultado = cliente.post(ruta, data=datos, auth=credenciales)
        assert resultado.url.path == "/psicologa"
        assert resultado.url.fragment == "atencion-1"
        assert f"Asistencia registrada para Paciente de Ejemplo: {estado}." in resultado.text
        assert resultado.text.count('role="status"') == 1
        detalle = cliente.get("/pagos/1", auth=credenciales)
        assert f"Estado de la atención:</strong> {estado}" in detalle.text
        assert "22.222.222-2" in detalle.text
        assert cliente.post(ruta, data=datos, auth=credenciales).status_code == 409

    atencion = conexion.execute("SELECT estado, justificacion_inasistencia FROM atencion WHERE id = 1").fetchone()
    assert atencion["estado"] == estado
    assert atencion["justificacion_inasistencia"] == (justificacion or None)
    pacientes = conexion.execute(
        """
        SELECT a.id, p.rut, a.estado FROM atencion a
        JOIN reserva r ON r.id = a.reserva_id
        JOIN paciente p ON p.id = r.paciente_id
        ORDER BY a.id
        """
    ).fetchall()
    assert [tuple(fila) for fila in pacientes] == [
        (1, "22.222.222-2", estado),
        (2, "33.333.333-3", "programada"),
    ]
    cargo = conexion.execute(
        "SELECT reserva_id, paciente_id, monto FROM cargo WHERE atencion_id = 1"
    ).fetchone()
    assert (cargo is not None) == cargo_esperado
    if cargo_esperado:
        assert tuple(cargo) == (None, 1, 5000)
    pago = conexion.execute("SELECT estado, monto_pagado FROM pago WHERE atencion_id = 1").fetchone()
    assert dict(pago) == {"estado": "Pendiente", "monto_pagado": 0}


def test_psicologa_cancela_reserva_confirmada_sin_cargo(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    app = crear_app(base_temporal, clave_psicologa_demo="clave-de-prueba")
    with TestClient(app) as cliente:
        resultado = cliente.post(
            "/psicologa/reservas/2/cancelar",
            auth=("psicologa", "clave-de-prueba"),
            data={"csrf": app.state.csrf_psicologa_demo},
        )
        assert resultado.url.path == "/psicologa"
        assert "Cancelada" in cliente.get("/reservas/2", auth=("psicologa", "clave-de-prueba")).text

    assert conexion.execute("SELECT 1 FROM cargo WHERE reserva_id = 2").fetchone() is None
    assert conexion.execute(
        "SELECT tipo FROM reserva_historial WHERE reserva_id = 2"
    ).fetchone()[0] == "cancelacion"


def test_reserva_reagendamiento_y_revision_del_comprobante(
    base_temporal, conexion, monkeypatch,
):
    cargar_datos_ejemplo(str(base_temporal))
    conexion.execute(
        """
        INSERT INTO bloque_horario
            (id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
        VALUES (7, 1, '2026-11-11', '11:00', '11:50', 'online')
        """
    )
    conexion.commit()
    ahora = programado("2026-11-09", "08:00")
    for modulo in (disponibilidad, ruta_disponibilidad, ruta_reserva, confirmacion,
                   reagendamiento):
        monkeypatch.setattr(modulo, "ahora_utc", lambda: ahora)

    smtp = ServidorSMTPFalso()
    try:
        configuracion = replace(
            cargar_configuracion(),
            smtp_host="127.0.0.1",
            smtp_puerto=smtp.puerto,
            smtp_remitente="consulta@example.test",
            smtp_usuario=None,
            smtp_clave=None,
            smtp_seguridad="ninguna",
            url_publica="http://testserver",
            hora_vispera="09:00",
            hora_recordatorio="08:00",
            zona_horaria="America/Santiago",
        )
        credenciales = ("psicologa", "clave-de-integracion")
        app = crear_app(
            base_temporal, configuracion=configuracion, planificador_activo=False,
            clave_psicologa_demo=credenciales[1],
        )
        planificador = PlanificadorCorreos(
            str(base_temporal), app.state.servicio_correo, configuracion,
        )
        with TestClient(app) as cliente:
            assert 'href="/reservar/2"' in cliente.get("/").text
            rut = "99.999.999-9"
            derivacion = cliente.post("/reservar/2", data={"rut": rut})
            assert derivacion.url.path == "/pacientes/registro"
            alta = cliente.post("/pacientes/registro", data={
                "nombre_completo": "Paciente de integración", "rut": rut,
                "correo": "paciente@example.test", "bloque_id": 2,
            })
            assert alta.url.path == "/reservar/2"
            reserva = cliente.post("/reservar/2", data={"rut": rut})
            detalle = reserva.url.path
            assert detalle.startswith("/reservas/")

            ahora = programado("2026-11-09", "09:00")
            planificador.ejecutar_ciclo(ahora)
            mensajes = [Parser(policy=policy.default).parsestr(m) for m in smtp.mensajes]
            solicitud = next(m for m in mensajes if m["To"] == "paciente@example.test"
                             and "Confirma tu hora" in str(m["Subject"]))
            texto = solicitud.get_body(preferencelist=("plain",)).get_content()
            enlace = next(linea for linea in texto.splitlines()
                          if "/respuesta/confirmar/" in linea)
            respuesta = urlsplit(enlace).path
            assert cliente.get(respuesta).status_code == 200
            assert 'href="' + detalle + '/reagendar"' in cliente.post(respuesta).text

            alternativas = cliente.get(detalle + "/reagendar")
            assert 'name="bloque_id" value="7"' in alternativas.text
            cambio = cliente.post(detalle + "/reagendar", data={"bloque_id": 7})
            assert "Pendiente de confirmación" in cambio.text
            assert 'href="/reservar/2"' in cliente.get("/disponibilidad").text

            ahora = programado("2026-11-10", "09:00")
            planificador.ejecutar_ciclo(ahora)
            segunda_confirmacion = cliente.post(detalle + "/confirmar")
            assert 'href="' + detalle + '/reagendar"' in segunda_confirmacion.text

            ahora = programado("2026-11-11", "11:00")
            planificador.ejecutar_ciclo(ahora)
            reserva_id = int(detalle.rsplit("/", 1)[1])
            atencion = conexion.execute(
                "SELECT id FROM atencion WHERE reserva_id = ?", (reserva_id,)
            ).fetchone()
            pago = f"/pagos/{atencion['id']}"
            assert f'href="{pago}/comprobante"' in cliente.get(detalle).text
            assert cliente.post("/reservar/7", data={"rut": rut}).status_code == 409
            comprobante = cliente.post(pago + "/comprobante", data={
                "monto": 30000, "fecha_transferencia": "2026-11-11",
                "cuenta_destino": "Cuenta de integración",
            })
            assert "El comprobante quedó registrado" in comprobante.text
            assert cliente.get(pago).status_code == 401
            assert f'href="{pago}"' in cliente.get("/pagos", auth=credenciales).text
            assert "Cuenta de integración" in cliente.get(pago, auth=credenciales).text

            ahora = programado("2026-11-23", "08:00")
            segunda_reserva = cliente.post("/reservar/4", data={"rut": rut})
            segunda_ruta = segunda_reserva.url.path
            assert segunda_ruta.startswith("/reservas/")
            ahora = programado("2026-11-23", "09:00")
            planificador.ejecutar_ciclo(ahora)
            cancelada = cliente.post(segunda_ruta + "/no-asistir")
            assert "Cancelada" in cancelada.text
            assert "$5.000" in cancelada.text
            assert 'href="/reservar/4"' in cliente.get("/disponibilidad").text
            cargo = conexion.execute(
                "SELECT motivo, monto FROM cargo WHERE reserva_id = ?",
                (int(segunda_ruta.rsplit("/", 1)[1]),),
            ).fetchone()
            assert tuple(cargo) == ("cancelación", 5000)
    finally:
        smtp.cerrar()


def test_mis_reservas_en_demo_lista_lo_del_navegador_y_navega_desde_todas_las_pantallas(
    base_temporal, conexion,
):
    from tests.test_hu02a_registro_paciente import insertar_bloque, preparar_psicologa

    preparar_psicologa(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")
    app = crear_app(base_temporal, clave_psicologa_demo="clave-admin")
    with TestClient(app) as navegador, TestClient(app) as otro:
        assert "No tienes reservas en este navegador" in navegador.get("/mis-reservas").text
        navegador.post("/pacientes/registro", data={
            "nombre_completo": "Paciente Nuevo", "rut": "12.345.678-5",
            "correo": "nuevo@example.cl", "bloque_id": "10",
        })
        reserva = navegador.post("/reservar/10", data={"rut": "123456785"}, follow_redirects=False)
        ruta_reserva_nueva = reserva.headers["location"]

        lista = navegador.get("/mis-reservas")
        assert f'href="{ruta_reserva_nueva}"' in lista.text
        # La cookie de acceso sobrevive al cierre del navegador (12 h).
        assert "Max-Age=43200" in reserva.headers["set-cookie"]
        # Otro navegador no ve reservas ajenas.
        assert f'href="{ruta_reserva_nueva}"' not in otro.get("/mis-reservas").text

        detalle = navegador.get(ruta_reserva_nueva)
        for enlace in ('href="/disponibilidad"', 'href="/mis-reservas"', 'href="/psicologa"'):
            assert enlace in detalle.text
