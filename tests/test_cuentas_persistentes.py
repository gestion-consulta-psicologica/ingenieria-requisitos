import html
import re
import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient

from app.bootstrap import crear_administradora
from app.db.conexion import RUTA_DB_POR_DEFECTO
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.rutas.cuentas import COOKIE_SESION
from app.rutas import psicologa
from app.servicios.cuentas import CuentaInvalida, huella, verificar_clave
from app.servicios.planificador import PlanificadorCorreos
from app.tiempo import programado

ADMIN = "ana.perez@example.cl"
PACIENTE = "paciente-cuenta@example.test"
CLAVE = "contraseña sintética de prueba"
CLAVE_NUEVA = "contraseña sintética recuperada"
RUT = "44.444.444-4"


class BuzonPrueba:
    def __init__(self):
        self.mensajes = []

    def configurado(self):
        return True

    def motivo_no_configurado(self):
        return None

    def enviar(self, destinatario, asunto, cuerpo_texto, cuerpo_html=None):
        self.mensajes.append((destinatario, asunto, cuerpo_texto))
        return "smtp-prueba"

    def ultimo_codigo(self, correo):
        return next(
            cuerpo.strip().splitlines()[-1] for destino, asunto, cuerpo in reversed(self.mensajes)
            if destino == correo and asunto == "Código de acceso a la consulta"
        )


def _app(base, buzon):
    return crear_app(base, servicio_correo=buzon, planificador_activo=False, cuentas_persistentes=True)


def _cliente(app):
    return TestClient(app, base_url="https://testserver")


def _csrf(cliente, url):
    respuesta = cliente.get(url)
    assert respuesta.status_code == 200
    return html.unescape(re.search(r'name="csrf" value="([^"]+)"', respuesta.text).group(1))


def _ingresar(cliente, correo, clave=CLAVE):
    return cliente.post(
        "/cuenta/ingresar",
        data={"correo": correo, "clave": clave, "csrf": _csrf(cliente, "/cuenta/ingresar")},
        follow_redirects=False,
    )


def _preparar(base):
    cargar_datos_ejemplo(str(base))
    crear_administradora(base, ADMIN, CLAVE, "11.111.111-1", "Psicóloga de prueba")


def _post_registro(cliente, *, correo=PACIENTE, rut=RUT):
    return cliente.post(
        "/cuenta/registro",
        data={
            "correo": correo, "clave": CLAVE, "rut": rut, "nombre": "Paciente persistente",
            "bloque_id": "2", "rol": "psicologa", "csrf": _csrf(cliente, "/cuenta/registro"),
        },
    )


def test_bootstrap_consola_crea_una_sola_cuenta_y_protege_base_real(base_temporal, conexion):
    crear_administradora(base_temporal, ADMIN, CLAVE, "11.111.111-1", "Psicóloga nueva")
    cuenta = conexion.execute("SELECT * FROM cuenta").fetchone()
    assert cuenta["rol"] == "psicologa"
    assert cuenta["psicologa_id"] is not None and cuenta["paciente_id"] is None
    assert CLAVE not in cuenta["clave_hash"]
    assert verificar_clave(CLAVE, cuenta["clave_hash"])
    with pytest.raises(CuentaInvalida, match="Ya existe"):
        crear_administradora(base_temporal, ADMIN, CLAVE, "11.111.111-1", "Psicóloga nueva")
    with pytest.raises(ValueError, match="data/app.db"):
        crear_administradora(RUTA_DB_POR_DEFECTO, ADMIN, CLAVE, "11.111.111-1", "Psicóloga nueva")
    with pytest.raises(ValueError, match="data/app.db"):
        crear_app(RUTA_DB_POR_DEFECTO, cuentas_persistentes=True)


def test_registro_verificacion_aprobacion_reinicio_reserva_y_comprobante(
    base_temporal, conexion, monkeypatch,
):
    _preparar(base_temporal)
    buzon = BuzonPrueba()
    app = _app(base_temporal, buzon)
    monkeypatch.setattr(psicologa, "ahora_utc", lambda: programado("2026-11-09", "08:00"))
    assert TestClient(app).get("/cuenta/ingresar").status_code == 400
    with _cliente(app) as paciente, _cliente(app) as admin:
        assert admin.get("/psicologa").status_code == 401
        assert _ingresar(admin, ADMIN).status_code == 303
        assert _post_registro(paciente).status_code == 200
        cuenta = conexion.execute("SELECT * FROM cuenta WHERE correo = ?", (PACIENTE,)).fetchone()
        assert cuenta["rol"] == "paciente" and cuenta["paciente_id"] is None
        assert PACIENTE not in admin.get("/psicologa").text
        assert _ingresar(paciente, PACIENTE).status_code == 403
        codigo = buzon.ultimo_codigo(PACIENTE)
        assert conexion.execute(
            "SELECT token_hash FROM token_cuenta WHERE cuenta_id = ?", (cuenta["id"],)
        ).fetchone()[0] == huella(codigo)
        datos = {"codigo": codigo, "csrf": _csrf(paciente, "/cuenta/verificar")}
        assert "Correo verificado" in paciente.post("/cuenta/verificar", data=datos).text
        assert paciente.post("/cuenta/verificar", data=datos).status_code == 400
        assert _ingresar(paciente, PACIENTE).status_code == 403
        assert PACIENTE in admin.get("/psicologa").text
        assert admin.post(
            f"/psicologa/identidades/{cuenta['id']}/aprobar",
            data={"csrf": _csrf(admin, "/psicologa")}, follow_redirects=False,
        ).status_code == 303
        ingreso = _ingresar(paciente, PACIENTE)
        assert ingreso.headers["location"] == "/reservar/2"
        cookie = paciente.cookies.get(COOKIE_SESION)
        assert "HttpOnly" in ingreso.headers["set-cookie"] and "Secure" in ingreso.headers["set-cookie"]
        assert conexion.execute(
            "SELECT 1 FROM sesion WHERE token_hash = ?", (huella(cookie),),
        ).fetchone()
        cookie_admin = admin.cookies.get(COOKIE_SESION)

    reiniciada = _app(base_temporal, buzon)
    with _cliente(reiniciada) as paciente, _cliente(reiniciada) as admin:
        paciente.cookies.set(COOKIE_SESION, cookie)
        admin.cookies.set(COOKIE_SESION, cookie_admin)
        assert paciente.get("/psicologa").status_code == 403
        assert paciente.get("/pagos").status_code == 403
        assert paciente.get("/psicologa/fichas/1").status_code == 403
        assert paciente.get("/reservas/1").status_code == 403
        assert paciente.get("/pagos/1/comprobante").status_code == 403
        assert paciente.post(
            f"/psicologa/identidades/{cuenta['id']}/aprobar",
            data={"csrf": _csrf(paciente, "/disponibilidad")},
        ).status_code == 403
        assert admin.get("/psicologa").status_code == 200
        assert admin.get("/pagos").status_code == 200
        assert admin.get("/psicologa/fichas/1").status_code == 200
        horario = admin.post("/psicologa/horarios", data={
            "csrf": _csrf(admin, "/psicologa"), "fecha": "2026-11-09",
            "inicio": "15:00", "termino": "15:50", "modalidad": "online",
        })
        assert "15:00 a 15:50" in horario.text
        assert paciente.post("/reservar/2", data={"rut": RUT}).status_code == 403
        reserva = paciente.post(
            "/reservar/2", data={"rut": RUT, "csrf": _csrf(paciente, "/reservar/2")},
            follow_redirects=False,
        )
        assert reserva.status_code == 303
        detalle = reserva.headers["location"]
        assert detalle in paciente.get("/cuenta/reservas").text
        plan = PlanificadorCorreos(str(base_temporal), buzon, reiniciada.state.configuracion_correo)
        plan.ejecutar_ciclo(programado("2026-11-09", "09:00"))
        correo = next(
            cuerpo for destino, asunto, cuerpo in buzon.mensajes
            if destino == PACIENTE and asunto.startswith("Confirma tu hora")
        )
        enlace = re.search(r"/respuesta/confirmar/[\w-]+", correo).group()
        with _cliente(reiniciada) as desde_correo:
            assert "quedó confirmada" in desde_correo.post(
                enlace, data={"csrf": _csrf(desde_correo, enlace)},
            ).text
            assert desde_correo.get(detalle).status_code == 403
            assert COOKIE_SESION not in desde_correo.cookies
        plan.ejecutar_ciclo(programado("2026-11-10", "11:00"))
        atencion = conexion.execute(
            "SELECT id FROM atencion WHERE reserva_id = ?", (int(detalle.rsplit("/", 1)[1]),)
        ).fetchone()[0]
        comprobante = f"/pagos/{atencion}/comprobante"
        assert "Comprobante sintético" in paciente.post(comprobante, data={
            "csrf": _csrf(paciente, comprobante), "monto": "30000",
            "fecha_transferencia": "2026-11-10", "cuenta_destino": "Comprobante sintético",
        }).text
        assert "Comprobante sintético" in admin.get(f"/pagos/{atencion}").text
        comprobante_id = conexion.execute(
            """
            SELECT c.id FROM comprobante_transferencia c
            JOIN pago p ON p.id = c.pago_id WHERE p.atencion_id = ?
            """, (atencion,),
        ).fetchone()[0]
        verificacion = admin.post(f"/pagos/{atencion}/estado", data={
            "csrf": _csrf(admin, f"/pagos/{atencion}"),
            "comprobantes": str(comprobante_id), "estado": "Pagado",
        })
        assert "El estado del pago quedó registrado." in verificacion.text
        asistencia = admin.post(f"/psicologa/atenciones/{atencion}/asistencia", data={
            "csrf": _csrf(admin, "/psicologa"), "estado": "realizada",
        })
        assert "Asistencia registrada" in asistencia.text
        assert paciente.post("/cuenta/salir", data={"csrf": _csrf(paciente, "/disponibilidad")}).status_code == 200
        paciente.cookies.set(COOKIE_SESION, cookie)
        assert paciente.get(detalle).status_code == 403


def test_sesion_administrativa_sobrevive_en_un_proceso_nuevo(base_temporal):
    _preparar(base_temporal)
    with _cliente(_app(base_temporal, BuzonPrueba())) as cliente:
        assert _ingresar(cliente, ADMIN).status_code == 303
        token = cliente.cookies.get(COOKIE_SESION)
    codigo = """
import os
import sys
from fastapi.testclient import TestClient
from app.rutas.cuentas import COOKIE_SESION
os.environ["CONSULTA_DB"] = sys.argv[1]
from app.asgi import app
with TestClient(app, base_url="https://testserver") as cliente:
    cliente.cookies.set(COOKIE_SESION, sys.stdin.read())
    assert cliente.get("/psicologa").status_code == 200
"""
    proceso = subprocess.run(
        [sys.executable, "-B", "-c", codigo, str(base_temporal)],
        input=token, capture_output=True, text=True, timeout=20,
    )
    assert proceso.returncode == 0, proceso.stderr


def test_recuperacion_expiracion_replay_y_revocacion_de_sesiones(base_temporal, conexion):
    _preparar(base_temporal)
    buzon = BuzonPrueba()
    app = _app(base_temporal, buzon)
    with _cliente(app) as primera, _cliente(app) as segunda, _cliente(app) as recuperacion:
        assert _ingresar(primera, ADMIN).status_code == 303
        expirada = primera.cookies.get(COOKIE_SESION)
        conexion.execute("UPDATE sesion SET expira_en = ? WHERE token_hash = ?", (
            int(time.time()) - 1, huella(expirada),
        ))
        conexion.commit()
        assert primera.get("/psicologa").status_code == 401
        assert _ingresar(primera, ADMIN).status_code == 303
        assert _ingresar(segunda, ADMIN).status_code == 303
        assert recuperacion.post("/cuenta/recuperar", data={
            "correo": ADMIN, "csrf": _csrf(recuperacion, "/cuenta/recuperar"),
        }).status_code == 200
        codigo = buzon.ultimo_codigo(ADMIN)
        datos = {
            "codigo": codigo, "clave": CLAVE_NUEVA,
            "csrf": _csrf(recuperacion, "/cuenta/restablecer"),
        }
        assert "Contraseña actualizada" in recuperacion.post("/cuenta/restablecer", data=datos).text
        assert recuperacion.post("/cuenta/restablecer", data=datos).status_code == 400
        assert primera.get("/psicologa").status_code == 401
        assert segunda.get("/psicologa").status_code == 401
        assert _ingresar(recuperacion, ADMIN).status_code == 401
        assert _ingresar(recuperacion, ADMIN, CLAVE_NUEVA).status_code == 303
        assert recuperacion.get("/psicologa").status_code == 200


def test_correo_verificado_distinto_no_adquiere_identidad_existente(base_temporal, conexion):
    _preparar(base_temporal)
    buzon = BuzonPrueba()
    app = _app(base_temporal, buzon)
    with _cliente(app) as paciente, _cliente(app) as admin:
        assert _post_registro(paciente, rut="22.222.222-2").status_code == 200
        codigo = buzon.ultimo_codigo(PACIENTE)
        assert "Correo verificado" in paciente.post("/cuenta/verificar", data={
            "codigo": codigo, "csrf": _csrf(paciente, "/cuenta/verificar"),
        }).text
        assert _ingresar(admin, ADMIN).status_code == 303
        cuenta_id = conexion.execute("SELECT id FROM cuenta WHERE correo = ?", (PACIENTE,)).fetchone()[0]
        respuesta = admin.post(
            f"/psicologa/identidades/{cuenta_id}/aprobar",
            data={"csrf": _csrf(admin, "/psicologa")},
        )
        assert respuesta.status_code == 409
        assert _ingresar(paciente, PACIENTE).status_code == 403
    assert conexion.execute("SELECT paciente_id FROM cuenta WHERE id = ?", (cuenta_id,)).fetchone()[0] is None
    assert conexion.execute("SELECT correo FROM paciente WHERE id = 1").fetchone()[0] == "paciente@example.cl"


class _SinCorreo:
    def configurado(self):
        return False

    def motivo_no_configurado(self):
        return "Falta configurar: SMTP_HOST."

    def enviar(self, *args, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("No debe intentar enviar sin correo configurado.")


def test_sin_correo_el_registro_avisa_y_no_crea_la_cuenta(base_temporal, conexion):
    cliente = _cliente(_app(base_temporal, _SinCorreo()))
    formulario = cliente.get("/cuenta/registro")
    assert "El envío de correo no está configurado" in formulario.text

    csrf = _csrf(cliente, "/cuenta/registro")
    respuesta = cliente.post("/cuenta/registro", data={
        "csrf": csrf, "correo": "nuevo@example.cl", "clave": "una-clave-bastante-larga",
        "rut": "12.345.678-5", "nombre": "Paciente Nuevo",
    })
    assert respuesta.status_code == 503
    assert "El envío de correo no está configurado" in respuesta.text
    assert conexion.execute("SELECT COUNT(*) FROM cuenta").fetchone()[0] == 0

    recuperar = cliente.post("/cuenta/recuperar", data={"csrf": csrf, "correo": "nuevo@example.cl"})
    assert recuperar.status_code == 503
