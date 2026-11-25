from __future__ import annotations

import sqlite3

import pytest
from tests.acceso_demo import cliente_con_reservas

from app.configuracion import cargar_configuracion, monto_atencion_clp
from app.db.conexion import conectar
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.atenciones import (
    AtencionNoEncontrada,
    DatosComprobanteInvalidos,
    PagoNoEncontrado,
    PagoYaPagado,
    crear_atenciones_vencidas,
    obtener_atencion_de_reserva,
    registrar_comprobante,
)
from app.servicios.pagos import obtener_pago_de_atencion
from app.servicios.planificador import PlanificadorCorreos
from app.tiempo import programado


class CorreoFalso:
    def __init__(self):
        self.enviados = []

    def configurado(self) -> bool:
        return True

    def motivo_no_configurado(self) -> str | None:
        return None

    def enviar(self, destinatario, asunto, cuerpo_texto, cuerpo_html=None) -> str:
        self.enviados.append((destinatario, asunto))
        return f"<falso-{len(self.enviados)}@example.cl>"


def _contar(conexion: sqlite3.Connection, tabla: str) -> int:
    return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def _sembrar(base_temporal) -> None:
    cargar_datos_ejemplo(str(base_temporal))


def _cliente(base_temporal):
    app = crear_app(
        base_temporal, planificador_activo=False, clave_psicologa_demo="clave-prueba",
    )
    return cliente_con_reservas(app, 1, 2, 3, 4)


def test_monto_atencion_clp_usa_30000_por_defecto(monkeypatch):
    monkeypatch.delenv("MONTO_ATENCION_CLP", raising=False)

    assert monto_atencion_clp() == 30000


def test_monto_atencion_clp_lee_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("MONTO_ATENCION_CLP", "45000")

    assert monto_atencion_clp() == 45000


def test_reserva_2_del_seed_esta_confirmada_vencida_y_sin_atencion(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        fila = conexion.execute(
            """
            SELECT r.estado, b.fecha, b.hora_inicio,
                   (SELECT COUNT(*) FROM atencion a WHERE a.reserva_id = r.id)
                       AS atenciones
            FROM reserva r
            JOIN bloque_horario b ON b.id = r.bloque_horario_id
            WHERE r.id = 2
            """
        ).fetchone()
    finally:
        conexion.close()

    assert dict(fila) == {
        "estado": "Confirmada",
        "fecha": "2026-11-17",
        "hora_inicio": "10:00",
        "atenciones": 0,
    }


def test_reserva_confirmada_futura_no_origina_atencion(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        creadas = crear_atenciones_vencidas(
            conexion,
            programado("2026-11-17", "09:59"),
            "America/Santiago",
        )
        atenciones = _contar(conexion, "atencion")
    finally:
        conexion.close()

    assert creadas == []
    assert atenciones == 2


def test_reserva_confirmada_vencida_origina_atencion_y_pago(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        creadas = crear_atenciones_vencidas(
            conexion,
            programado("2026-11-17", "10:00"),
            "America/Santiago",
            monto_clp=30000,
        )
        fila = conexion.execute(
            """
            SELECT a.id AS atencion_id, a.tipo_atencion, a.monto,
                   a.estado AS atencion_estado,
                   p.monto_atencion, p.monto_pagado, p.estado AS pago_estado,
                   r.estado AS reserva_estado
            FROM atencion a
            JOIN pago p ON p.atencion_id = a.id
            JOIN reserva r ON r.id = a.reserva_id
            WHERE a.reserva_id = 2
            """
        ).fetchone()
    finally:
        conexion.close()

    assert len(creadas) == 1
    assert dict(fila) == {
        "atencion_id": 3,
        "tipo_atencion": "presencial",
        "monto": 30000,
        "atencion_estado": "programada",
        "monto_atencion": 30000,
        "monto_pagado": 0,
        "pago_estado": "Pendiente",
        "reserva_estado": "Finalizada",
    }


def test_el_sistema_no_duplica_una_atencion_ya_originada(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        ahora = programado("2026-11-17", "10:00")
        primeras = crear_atenciones_vencidas(
            conexion, ahora, "America/Santiago"
        )
        segundas = crear_atenciones_vencidas(
            conexion, ahora, "America/Santiago"
        )
        atenciones = conexion.execute(
            "SELECT COUNT(*) FROM atencion WHERE reserva_id = 2"
        ).fetchone()[0]
        pagos = _contar(conexion, "pago")
        estado_reserva = conexion.execute(
            "SELECT estado FROM reserva WHERE id = 2"
        ).fetchone()[0]
    finally:
        conexion.close()

    assert len(primeras) == 1
    assert segundas == []
    assert atenciones == 1
    assert pagos == 3
    assert estado_reserva == "Finalizada"


def test_planificador_crea_la_atencion_una_sola_vez_en_dos_ciclos(base_temporal):
    _sembrar(base_temporal)
    configuracion = cargar_configuracion()
    planificador = PlanificadorCorreos(
        str(base_temporal), CorreoFalso(), configuracion
    )

    primero = planificador.ejecutar_ciclo(programado("2026-11-17", "10:00"))
    segundo = planificador.ejecutar_ciclo(programado("2026-11-17", "10:01"))

    conexion = conectar(base_temporal)
    try:
        atenciones = conexion.execute(
            "SELECT COUNT(*) FROM atencion WHERE reserva_id = 2"
        ).fetchone()[0]
    finally:
        conexion.close()

    assert primero["atenciones_creadas"] == 1
    assert segundo["atenciones_creadas"] == 0
    assert atenciones == 1


def test_reserva_finalizada_por_planificador_rechaza_gestion_http(base_temporal, conexion):
    _sembrar(base_temporal)
    planificador = PlanificadorCorreos(
        str(base_temporal), CorreoFalso(), cargar_configuracion(),
    )
    ciclo = planificador.ejecutar_ciclo(programado("2026-11-17", "10:00"))
    assert ciclo["atenciones_creadas"] == 1

    with _cliente(base_temporal) as cliente:
        assert "Finalizada" in cliente.get("/reservas/2").text
        assert cliente.get("/reservas/2/reagendar").status_code == 409
        assert cliente.post("/reservas/2/reagendar", data={"bloque_id": 4}).status_code == 409
        assert cliente.post("/reservas/2/cancelar").status_code == 409

    fila = conexion.execute(
        "SELECT bloque_horario_id, estado, version FROM reserva WHERE id = 2"
    ).fetchone()
    assert tuple(fila) == (3, "Finalizada", 1)
    assert obtener_atencion_de_reserva(conexion, 2)["pago_estado"] == "Pendiente"
    assert conexion.execute("SELECT 1 FROM reserva_historial WHERE reserva_id = 2").fetchone() is None
    assert conexion.execute("SELECT 1 FROM cargo WHERE reserva_id = 2").fetchone() is None


def test_planificador_no_origina_atencion_si_la_reserva_cambio(base_temporal):
    _sembrar(base_temporal)
    conexion = conectar(base_temporal)
    otra_conexion = conectar(base_temporal)

    def cancelar_antes_de_escribir(sql):
        if sql == "BEGIN IMMEDIATE":
            otra_conexion.execute("UPDATE reserva SET estado = 'Cancelada' WHERE id = 2")
            otra_conexion.commit()

    try:
        conexion.set_trace_callback(cancelar_antes_de_escribir)
        creadas = crear_atenciones_vencidas(
            conexion, programado("2026-11-17", "10:00"),
        )

        assert creadas == []
        assert obtener_atencion_de_reserva(conexion, 2) is None
        assert conexion.execute("SELECT estado FROM reserva WHERE id = 2").fetchone()[0] == "Cancelada"
    finally:
        conexion.close()
        otra_conexion.close()


def test_obtener_atencion_de_reserva_entrega_pago_y_estado(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        detalle = obtener_atencion_de_reserva(conexion, 3)
        sin_atencion = obtener_atencion_de_reserva(conexion, 2)
    finally:
        conexion.close()

    assert detalle == {
        "atencion_id": 1,
        "atencion_estado": "programada",
        "pago_id": 1,
        "pago_estado": "Pendiente",
    }
    assert sin_atencion is None


def test_paciente_registra_comprobante_de_su_transferencia(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        resultado = registrar_comprobante(
            conexion, 2, "30.000", "2026-11-12", "Cuenta corriente 123"
        )
        comprobante = conexion.execute(
            """
            SELECT monto, fecha_transferencia, cuenta_destino
            FROM comprobante_transferencia
            WHERE id = ?
            """,
            (resultado["id"],),
        ).fetchone()
        pago = conexion.execute(
            "SELECT estado, monto_pagado FROM pago WHERE atencion_id = 2"
        ).fetchone()
    finally:
        conexion.close()

    assert resultado["monto"] == 30000
    assert dict(comprobante) == {
        "monto": 30000,
        "fecha_transferencia": "2026-11-12",
        "cuenta_destino": "Cuenta corriente 123",
    }
    assert dict(pago) == {"estado": "Pendiente", "monto_pagado": 0}


def test_paciente_registra_un_segundo_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        primero = registrar_comprobante(
            conexion, 2, "10000", "2026-11-12", "Cuenta A"
        )
        segundo = registrar_comprobante(
            conexion, 2, "20000", "2026-11-13", "Cuenta B"
        )
        comprobantes = [
            dict(fila)
            for fila in conexion.execute(
                """
                SELECT id, monto, fecha_transferencia, cuenta_destino
                FROM comprobante_transferencia
                WHERE pago_id = 2
                ORDER BY id
                """
            )
        ]
    finally:
        conexion.close()

    assert [fila["id"] for fila in comprobantes] == [
        primero["id"],
        segundo["id"],
    ]
    assert [fila["monto"] for fila in comprobantes] == [10000, 20000]


def test_paciente_no_completa_los_datos_obligatorios(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        with pytest.raises(DatosComprobanteInvalidos) as error:
            registrar_comprobante(conexion, 2, "", "", "   ")
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert set(error.value.errores) == {
        "monto",
        "fecha_transferencia",
        "cuenta_destino",
    }
    assert comprobantes == 1


def test_comprobante_con_datos_invalidos_no_se_registra(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        with pytest.raises(DatosComprobanteInvalidos) as error:
            registrar_comprobante(
                conexion, 2, "0", "2026-13-40", "Cuenta destino"
            )
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert set(error.value.errores) == {"monto", "fecha_transferencia"}
    assert comprobantes == 1


def test_atencion_con_pago_inexistente_por_datos_inconsistentes_no_permite_registrar_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        conexion.execute(
            """
            INSERT INTO atencion (id, reserva_id, tipo_atencion, monto, estado)
            VALUES (99, 2, 'presencial', 30000, 'programada')
            """
        )
        conexion.commit()
        with pytest.raises(PagoNoEncontrado):
            registrar_comprobante(
                conexion, 99, "30000", "2026-11-12", "Cuenta destino"
            )
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert comprobantes == 1


def test_pago_ya_pagado_no_permite_registrar_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        conexion.execute(
            "UPDATE pago SET estado = 'Pagado' WHERE atencion_id = 2"
        )
        conexion.commit()
        with pytest.raises(PagoYaPagado):
            registrar_comprobante(
                conexion, 2, "30000", "2026-11-12", "Cuenta destino"
            )
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert comprobantes == 1


def test_atencion_inexistente_no_permite_registrar_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        with pytest.raises(AtencionNoEncontrada):
            registrar_comprobante(
                conexion, 999, "30000", "2026-11-12", "Cuenta destino"
            )
    finally:
        conexion.close()


def test_detalle_de_pago_incluye_reserva_y_comprobantes(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        detalle = obtener_pago_de_atencion(conexion, 2)
    finally:
        conexion.close()

    assert detalle is not None
    assert detalle["reserva_id"] == 4
    assert detalle["comprobantes"] == []


def test_formulario_muestra_los_campos_y_los_comprobantes_anteriores(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos/1/comprobante")

    assert respuesta.status_code == 200
    assert 'name="monto"' in respuesta.text
    assert 'name="fecha_transferencia"' in respuesta.text
    assert 'name="cuenta_destino"' in respuesta.text
    assert "Cuenta de ejemplo" in respuesta.text


def test_ruta_registra_comprobante_y_redirige_con_confirmacion(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        reserva = cliente.get("/reservas/4")
        assert 'href="/pagos/2/comprobante"' in reserva.text
        respuesta = cliente.post(
            "/pagos/2/comprobante",
            data={
                "monto": "30000",
                "fecha_transferencia": "2026-11-12",
                "cuenta_destino": "Cuenta corriente 123",
            },
            follow_redirects=False,
        )
        confirmacion = cliente.get(
            "/pagos/2/comprobante?registrado=1"
        )
        inicio = cliente.get("/")
        credenciales = ("psicologa", "clave-prueba")
        bandeja = cliente.get("/pagos", auth=credenciales)
        revision = cliente.get("/pagos/2", auth=credenciales)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/pagos/2/comprobante?registrado=1"
    assert confirmacion.status_code == 200
    assert "El comprobante quedó registrado" in confirmacion.text
    assert "Cuenta corriente 123" in confirmacion.text
    assert 'href="/psicologa"' in inicio.text
    assert 'href="/pagos/2"' in bandeja.text
    assert "Cuenta corriente 123" in revision.text
    assert 'href="/reservas/4"' in revision.text


def test_ruta_rechaza_datos_invalidos_sin_registrar(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.post(
            "/pagos/2/comprobante",
            data={
                "monto": "",
                "fecha_transferencia": "",
                "cuenta_destino": "",
            },
        )

    assert respuesta.status_code == 400
    assert "Revisa los datos del comprobante" in respuesta.text
    assert "Ingresa un monto válido" in respuesta.text

    conexion = conectar(base_temporal)
    try:
        assert _contar(conexion, "comprobante_transferencia") == 1
    finally:
        conexion.close()


def test_ruta_responde_404_si_la_atencion_o_el_pago_no_existe(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        inexistente = cliente.get("/pagos/999/comprobante")
        sin_pago = cliente.post(
            "/pagos/999/comprobante",
            data={
                "monto": "30000",
                "fecha_transferencia": "2026-11-12",
                "cuenta_destino": "Cuenta",
            },
        )

    assert inexistente.status_code == 404
    assert sin_pago.status_code == 404


def test_ruta_responde_409_si_el_pago_ya_esta_pagado(base_temporal):
    _sembrar(base_temporal)
    conexion = conectar(base_temporal)
    try:
        conexion.execute(
            "UPDATE pago SET estado = 'Pagado' WHERE atencion_id = 2"
        )
        conexion.commit()
    finally:
        conexion.close()

    with _cliente(base_temporal) as cliente:
        formulario = cliente.get("/pagos/2/comprobante")
        respuesta = cliente.post(
            "/pagos/2/comprobante",
            data={
                "monto": "30000",
                "fecha_transferencia": "2026-11-12",
                "cuenta_destino": "Cuenta",
            },
        )

    assert formulario.status_code == 409
    assert respuesta.status_code == 409
    assert "El pago ya está pagado" in formulario.text
    assert "El pago ya está pagado" in respuesta.text


def test_detalle_de_reserva_muestra_enlace_solo_si_el_pago_lo_permite(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        con_pago_pendiente = cliente.get("/reservas/3")
        sin_atencion = cliente.get("/reservas/1")

    assert con_pago_pendiente.status_code == 200
    assert "Registrar comprobante de pago" in con_pago_pendiente.text
    assert "Sin atención" not in con_pago_pendiente.text
    assert "Registrar comprobante de pago" not in sin_atencion.text

    conexion = conectar(base_temporal)
    try:
        conexion.execute(
            "UPDATE pago SET estado = 'Pagado' WHERE atencion_id = 1"
        )
        conexion.commit()
    finally:
        conexion.close()

    with _cliente(base_temporal) as cliente:
        con_pago_pagado = cliente.get("/reservas/3")

    assert "Registrar comprobante de pago" not in con_pago_pagado.text


@pytest.mark.parametrize("escrito", ["30000", "30.000", "$30.000", "$ 30.000"])
def test_monto_del_comprobante_acepta_formato_chileno(base_temporal, escrito):
    _sembrar(base_temporal)
    conexion = conectar(base_temporal)
    try:
        comprobante = registrar_comprobante(
            conexion, 2, escrito, "2026-11-10", "Cuenta destino"
        )
    finally:
        conexion.close()

    assert comprobante["monto"] == 30000


@pytest.mark.parametrize("escrito", ["30,000", "$", "treinta mil", "-30000"])
def test_monto_del_comprobante_rechaza_formatos_ambiguos(base_temporal, escrito):
    _sembrar(base_temporal)
    conexion = conectar(base_temporal)
    try:
        with pytest.raises(DatosComprobanteInvalidos) as error:
            registrar_comprobante(conexion, 2, escrito, "2026-11-10", "Cuenta destino")
    finally:
        conexion.close()

    assert set(error.value.errores) == {"monto"}


@pytest.mark.parametrize("modalidad", ["Presencial", "remota", ""])
def test_bloque_con_modalidad_invalida_se_rechaza_en_la_base(conexion, modalidad):
    conexion.execute(
        "INSERT INTO psicologa (id, nombre_completo, rut, correo) VALUES (1, 'A', '1-9', 'a@a.cl')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="modalidad inválida"):
        conexion.execute(
            """
            INSERT INTO bloque_horario (psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
            VALUES (1, '2026-11-12', '10:00', '10:50', ?)
            """,
            (modalidad,),
        )
    conexion.execute(
        """
        INSERT INTO bloque_horario (id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
        VALUES (50, 1, '2026-11-12', '10:00', '10:50', 'online')
        """
    )
    with pytest.raises(sqlite3.IntegrityError, match="modalidad inválida"):
        conexion.execute("UPDATE bloque_horario SET modalidad = ? WHERE id = 50", (modalidad,))
