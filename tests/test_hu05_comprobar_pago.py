from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from app.db.conexion import conectar
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.pagos import (
    listar_atenciones_con_pago_pendiente,
    obtener_pago_de_atencion,
)


def _contar(conexion: sqlite3.Connection, tabla: str) -> int:
    return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def _sembrar(base_temporal) -> None:
    cargar_datos_ejemplo(str(base_temporal))


def _cliente(base_temporal):
    return TestClient(crear_app(base_temporal, planificador_activo=False))


def test_migracion_007_crea_tablas_y_registra_version(base_temporal):
    conexion = conectar(base_temporal)
    try:
        tablas = {
            fila["name"]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"atencion", "pago", "comprobante_transferencia"} <= tablas
        version = conexion.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            ("007_atencion_pago.sql",),
        ).fetchone()
        assert version is not None
    finally:
        conexion.close()


def test_seed_hu05_es_idempotente_y_crea_los_dos_escenarios(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        assert _contar(conexion, "atencion") == 2
        assert _contar(conexion, "pago") == 2
        assert _contar(conexion, "comprobante_transferencia") == 1

        atenciones = [
            dict(fila)
            for fila in conexion.execute(
                """
                SELECT a.id, p.nombre_completo, pg.estado, b.fecha, b.hora_inicio
                FROM atencion a
                JOIN pago pg ON pg.atencion_id = a.id
                JOIN reserva r ON r.id = a.reserva_id
                JOIN paciente p ON p.id = r.paciente_id
                JOIN bloque_horario b ON b.id = r.bloque_horario_id
                ORDER BY a.id
                """
            )
        ]
        assert [fila["id"] for fila in atenciones] == [1, 2]
        assert atenciones[0]["nombre_completo"] == "Paciente de Ejemplo"
        assert atenciones[1]["nombre_completo"] == "Paciente Sin Comprobante"
        assert [fila["estado"] for fila in atenciones] == ["Pendiente", "Pendiente"]
        assert [fila["fecha"] for fila in atenciones] == [
            "2026-11-12",
            "2026-11-12",
        ]
        assert [fila["hora_inicio"] for fila in atenciones] == ["16:00", "17:00"]

        comprobante = conexion.execute(
            """
            SELECT monto, fecha_transferencia, cuenta_destino
            FROM comprobante_transferencia
            WHERE pago_id = 1
            """
        ).fetchone()
        assert dict(comprobante) == {
            "monto": 30000,
            "fecha_transferencia": "2026-11-10",
            "cuenta_destino": "Cuenta de ejemplo",
        }
        assert (
            conexion.execute(
                "SELECT COUNT(*) FROM comprobante_transferencia WHERE pago_id = 2"
            ).fetchone()[0]
            == 0
        )
    finally:
        conexion.close()

    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        assert _contar(conexion, "atencion") == 2
        assert _contar(conexion, "pago") == 2
        assert _contar(conexion, "comprobante_transferencia") == 1
    finally:
        conexion.close()


def test_servicio_entrega_detalle_con_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        detalle = obtener_pago_de_atencion(conexion, 1)
    finally:
        conexion.close()

    assert detalle is not None
    assert detalle["paciente"] == {
        "nombre_completo": "Paciente de Ejemplo",
        "rut": "22.222.222-2",
    }
    assert detalle["bloque"] == {
        "fecha": "2026-11-12",
        "hora_inicio": "16:00",
        "hora_termino": "16:50",
    }
    assert detalle["pago"]["monto_atencion"] == 30000
    assert detalle["pago"]["monto_pagado"] == 0
    assert detalle["pago"]["estado"] == "Pendiente"
    assert detalle["comprobantes"] == [
        {
            "id": 1,
            "monto": 30000,
            "fecha_transferencia": "2026-11-10",
            "cuenta_destino": "Cuenta de ejemplo",
        }
    ]


def test_servicio_devuelve_lista_vacia_sin_comprobante(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        detalle = obtener_pago_de_atencion(conexion, 2)
    finally:
        conexion.close()

    assert detalle is not None
    assert detalle["paciente"]["nombre_completo"] == "Paciente Sin Comprobante"
    assert detalle["comprobantes"] == []


def test_servicio_es_de_solo_lectura(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        primera = obtener_pago_de_atencion(conexion, 1)
        segunda = obtener_pago_de_atencion(conexion, 1)
        pago = conexion.execute(
            "SELECT monto_pagado, estado FROM pago WHERE atencion_id = 1"
        ).fetchone()
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert primera == segunda
    assert dict(pago) == {"monto_pagado": 0, "estado": "Pendiente"}
    assert comprobantes == 1


def test_listado_incluye_solo_atenciones_con_pago_pendiente(base_temporal):
    _sembrar(base_temporal)

    conexion = conectar(base_temporal)
    try:
        conexion.execute(
            "UPDATE pago SET estado = 'Pagado' WHERE atencion_id = 2"
        )
        conexion.commit()
        atenciones = listar_atenciones_con_pago_pendiente(conexion)
    finally:
        conexion.close()

    assert [item["atencion"]["id"] for item in atenciones] == [1]
    assert atenciones[0]["pago"]["estado"] == "Pendiente"


def test_ruta_listado_muestra_atenciones_pendientes(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos")

    assert respuesta.status_code == 200
    assert "Paciente de Ejemplo" in respuesta.text
    assert "Paciente Sin Comprobante" in respuesta.text
    assert "Comprobar pago" in respuesta.text


def test_ruta_inexistente_responde_404(base_temporal):
    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos/999")

    assert respuesta.status_code == 404
    assert "No se encontró la atención" in respuesta.text


def test_hu05_atencion_con_comprobante_registrado(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos/1")

    assert respuesta.status_code == 200
    assert "Paciente de Ejemplo" in respuesta.text
    assert "22.222.222-2" in respuesta.text
    assert "Monto de la atención" in respuesta.text
    assert "$30.000" in respuesta.text
    assert "2026-11-10" in respuesta.text
    assert "Cuenta de ejemplo" in respuesta.text
    assert "Pendiente" in respuesta.text


def test_hu05_atencion_sin_comprobante_de_pago(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos/2")
        listado = cliente.get("/pagos")

    assert respuesta.status_code == 200
    assert "La atención no tiene comprobante de pago." in respuesta.text
    assert "Paciente Sin Comprobante" in listado.text
    assert "17:00 a 17:50" in listado.text


def test_hu05_psicologa_revisa_y_continua_al_registro(base_temporal):
    _sembrar(base_temporal)

    with _cliente(base_temporal) as cliente:
        respuesta = cliente.get("/pagos/1")

    assert respuesta.status_code == 200
    assert "Registrar estado de pago" in respuesta.text
    assert "disabled" in respuesta.text
    assert "no calcula ni cambia el estado" in respuesta.text

    conexion = conectar(base_temporal)
    try:
        pago = conexion.execute(
            "SELECT monto_pagado, estado FROM pago WHERE atencion_id = 1"
        ).fetchone()
        comprobantes = _contar(conexion, "comprobante_transferencia")
    finally:
        conexion.close()

    assert dict(pago) == {"monto_pagado": 0, "estado": "Pendiente"}
    assert comprobantes == 1
