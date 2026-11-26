"""HU-06 (extensión) — Pagar un cargo de $5.000: comprobante del paciente y verificación de la psicóloga."""

import re

import pytest
from fastapi.testclient import TestClient

from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.atenciones import DatosComprobanteInvalidos
from app.servicios.cargos import (
    CargoYaPagado,
    VerificacionCargoInvalida,
    obtener_cargo,
    registrar_comprobante_cargo,
    verificar_pago_cargo,
)

ADMIN = ("psicologa", "clave-admin")
PACIENTE = ("paciente", "clave-paciente")  # paciente 1 del seed


def _crear_cargo(conexion, motivo="cancelación", reserva_id=2, paciente_id=1) -> int:
    cursor = conexion.execute(
        "INSERT INTO cargo (paciente_id, reserva_id, monto, motivo, fecha) VALUES (?, ?, 5000, ?, '2026-11-17')",
        (paciente_id, reserva_id, motivo),
    )
    conexion.commit()
    return cursor.lastrowid


def _ids_comprobantes(conexion, cargo_id):
    return [f[0] for f in conexion.execute(
        "SELECT id FROM comprobante_cargo WHERE cargo_id = ? AND verificado = 0 ORDER BY id", (cargo_id,))]


def test_cargo_nuevo_queda_pendiente(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    cargo = obtener_cargo(conexion, _crear_cargo(conexion))
    assert (cargo["estado"], cargo["monto_pagado"], cargo["saldo"]) == ("Pendiente", 0, 5000)
    assert cargo["motivo_texto"] == "Cancelación de la hora"


def test_pago_parcial_luego_completo_y_sin_mas_comprobantes(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    cargo_id = _crear_cargo(conexion)

    registrar_comprobante_cargo(conexion, cargo_id, "$3.000", "2026-11-18", "Cuenta de la psicóloga")
    # Registrar el comprobante no cambia el estado (como HU-05A).
    assert obtener_cargo(conexion, cargo_id)["estado"] == "Pendiente"

    with pytest.raises(VerificacionCargoInvalida, match="Pago incompleto"):
        verificar_pago_cargo(conexion, cargo_id, _ids_comprobantes(conexion, cargo_id), estado_elegido="Pagado")
    verificar_pago_cargo(conexion, cargo_id, _ids_comprobantes(conexion, cargo_id), estado_elegido="Pago incompleto")
    cargo = obtener_cargo(conexion, cargo_id)
    assert (cargo["estado"], cargo["monto_pagado"], cargo["saldo"]) == ("Pago incompleto", 3000, 2000)

    registrar_comprobante_cargo(conexion, cargo_id, "2000", "2026-11-19", "Cuenta de la psicóloga")
    verificar_pago_cargo(conexion, cargo_id, _ids_comprobantes(conexion, cargo_id), estado_elegido="Pagado")
    cargo = obtener_cargo(conexion, cargo_id)
    assert (cargo["estado"], cargo["monto_pagado"]) == ("Pagado", 5000)
    assert all(c["verificado"] for c in cargo["comprobantes"])

    with pytest.raises(CargoYaPagado):
        registrar_comprobante_cargo(conexion, cargo_id, "1000", "2026-11-20", "Cuenta")


def test_comprobante_invalido_o_total_excesivo_no_cambian_nada(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    cargo_id = _crear_cargo(conexion)
    with pytest.raises(DatosComprobanteInvalidos) as error:
        registrar_comprobante_cargo(conexion, cargo_id, "0", "2026-13-40", "")
    assert set(error.value.errores) == {"monto", "fecha_transferencia", "cuenta_destino"}

    registrar_comprobante_cargo(conexion, cargo_id, "6000", "2026-11-18", "Cuenta")
    with pytest.raises(VerificacionCargoInvalida, match="supera"):
        verificar_pago_cargo(conexion, cargo_id, _ids_comprobantes(conexion, cargo_id), estado_elegido="Pagado")
    with pytest.raises(VerificacionCargoInvalida, match="Selecciona"):
        verificar_pago_cargo(conexion, cargo_id, [], estado_elegido="Pagado")
    assert obtener_cargo(conexion, cargo_id)["estado"] == "Pendiente"


def test_recorrido_http_paciente_paga_y_psicologa_verifica(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    cargo_id = _crear_cargo(conexion)
    app = crear_app(base_temporal, clave_psicologa_demo=ADMIN[1], clave_paciente_demo=PACIENTE[1])
    csrf = app.state.csrf_psicologa_demo

    with TestClient(app) as paciente, TestClient(app) as anonimo, TestClient(app) as psicologa:
        lista = paciente.get("/cargos", auth=PACIENTE)
        assert f'href="/cargos/{cargo_id}"' in lista.text and "Pagar" in lista.text
        # Desde la reserva que lo originó también se llega al pago.
        assert f'href="/cargos/{cargo_id}"' in paciente.get("/reservas/2", auth=PACIENTE).text

        # Otro navegador sin acceso no ve ni paga el cargo.
        assert f'href="/cargos/{cargo_id}"' not in anonimo.get("/cargos").text
        assert anonimo.get(f"/cargos/{cargo_id}").status_code == 403
        assert anonimo.post(f"/cargos/{cargo_id}/comprobante", data={
            "monto": "5000", "fecha_transferencia": "2026-11-18", "cuenta_destino": "Cuenta"}).status_code == 403

        invalido = paciente.post(f"/cargos/{cargo_id}/comprobante", auth=PACIENTE, data={
            "monto": "", "fecha_transferencia": "", "cuenta_destino": ""})
        assert invalido.status_code == 400
        registro = paciente.post(f"/cargos/{cargo_id}/comprobante", auth=PACIENTE, data={
            "monto": "$5.000", "fecha_transferencia": "2026-11-18", "cuenta_destino": "Cuenta de la psicóloga"},
            follow_redirects=True)
        assert "El comprobante quedó registrado" in registro.text

        # La psicóloga lo ve en su lista y lo verifica.
        assert anonimo.get("/psicologa/cargos").status_code == 401
        pendientes = psicologa.get("/psicologa/cargos", auth=ADMIN)
        assert f'href="/psicologa/cargos/{cargo_id}"' in pendientes.text
        assert 'href="/psicologa/cargos"' in psicologa.get("/psicologa", auth=ADMIN).text
        detalle = psicologa.get(f"/psicologa/cargos/{cargo_id}", auth=ADMIN).text
        comprobante = re.search(r'name="comprobantes" value="(\d+)"', detalle).group(1)
        sin_csrf = psicologa.post(f"/psicologa/cargos/{cargo_id}/estado", auth=ADMIN,
                                  data={"comprobantes": comprobante, "estado": "Pagado", "csrf": "x"})
        assert sin_csrf.status_code == 403
        hecho = psicologa.post(f"/psicologa/cargos/{cargo_id}/estado", auth=ADMIN,
                               data={"comprobantes": comprobante, "estado": "Pagado", "csrf": csrf})
        assert "El estado del cargo quedó registrado" in hecho.text

        assert f'href="/psicologa/cargos/{cargo_id}"' not in psicologa.get("/psicologa/cargos", auth=ADMIN).text
        pagado = paciente.get(f"/cargos/{cargo_id}", auth=PACIENTE).text
        assert "Pagado" in pagado and 'action="/cargos/' not in pagado

    assert obtener_cargo(conexion, cargo_id)["estado"] == "Pagado"


def test_cargo_por_inasistencia_se_asocia_a_la_reserva_de_la_atencion(base_temporal, conexion):
    """Los cargos de HU-08 cuelgan de la atención; su hora y su titular salen de la reserva."""
    cargar_datos_ejemplo(str(base_temporal))
    app = crear_app(base_temporal, clave_psicologa_demo=ADMIN[1], clave_paciente_demo=PACIENTE[1])
    with TestClient(app) as cliente:
        cliente.post("/psicologa/atenciones/1/asistencia", auth=ADMIN, data={
            "estado": "inasistencia", "justificacion": "", "csrf": app.state.csrf_psicologa_demo})
        cargo_id = conexion.execute("SELECT id FROM cargo WHERE atencion_id = 1").fetchone()[0]
        cargo = obtener_cargo(conexion, cargo_id)
        assert cargo["reserva_origen"] == 3 and cargo["bloque_fecha"] == "2026-11-12"
        assert cargo["motivo_texto"] == "Inasistencia sin justificación"
        assert f'href="/cargos/{cargo_id}"' in cliente.get("/cargos", auth=PACIENTE).text
