from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from app.db.conexion import conectar
from app.db.seed import cargar_datos_ejemplo
from app.servicios.confirmacion import (
    ESTADO_SOLICITUD_REEMPLAZADA,
    ESTADO_SOLICITUD_RESPONDIDA,
    ESTADO_SOLICITUD_VENCIDA,
    RESPUESTA_CONFIRMA,
    RESPUESTA_SIN_RESPUESTA,
    TIPO_RECORDATORIO,
    TIPO_VISPERA,
)
from app.servicios.reserva import registrar_reserva

PROYECTO = Path(__file__).resolve().parent.parent

CODIGO_ESCRITURA = textwrap.dedent(
    """
    import json
    import sys

    from app.db.conexion import conectar
    from app.servicios.confirmacion import (
        RESPUESTA_CONFIRMA,
        TIPO_RECORDATORIO,
        TIPO_VISPERA,
        enviar_solicitud,
        marcar_hora_sin_respuesta,
        registrar_respuesta,
    )

    reserva_id = int(sys.argv[1])
    conexion = conectar()
    try:
        enviar_solicitud(conexion, 1, TIPO_VISPERA)
        enviar_solicitud(conexion, 1, TIPO_RECORDATORIO)
        respuesta = registrar_respuesta(conexion, 1, RESPUESTA_CONFIRMA)
        enviar_solicitud(conexion, reserva_id, TIPO_VISPERA)
        enviar_solicitud(conexion, reserva_id, TIPO_RECORDATORIO)
        marcar_hora_sin_respuesta(conexion, reserva_id)
    finally:
        conexion.close()
    print(json.dumps({"fecha_respuesta": respuesta["fecha_respuesta"]}))
    """
)

CODIGO_LECTURA = textwrap.dedent(
    """
    import json

    from app.db.conexion import conectar

    conexion = conectar()
    try:
        reservas = [
            dict(fila)
            for fila in conexion.execute(
                "SELECT id, paciente_id, bloque_horario_id, fecha_registro, estado "
                "FROM reserva ORDER BY id"
            )
        ]
        solicitudes = [
            dict(fila)
            for fila in conexion.execute(
                "SELECT id, reserva_id, tipo, fecha_envio, estado, respuesta, "
                "fecha_respuesta, fecha_cierre "
                "FROM solicitud_confirmacion ORDER BY id"
            )
        ]
        cargos = [
            dict(fila)
            for fila in conexion.execute(
                "SELECT id, paciente_id, reserva_id, monto, motivo, fecha "
                "FROM cargo ORDER BY id"
            )
        ]
    finally:
        conexion.close()
    print(json.dumps({
        "reservas": reservas,
        "solicitudes": solicitudes,
        "cargos": cargos,
    }))
    """
)


def ejecutar_proceso(codigo: str, base, *argumentos: str):
    entorno = os.environ.copy()
    entorno["CONSULTA_DB"] = str(base)
    return subprocess.run(
        [sys.executable, "-c", codigo, *argumentos],
        cwd=PROYECTO,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_persistencia_entre_procesos(base_temporal):
    cargar_datos_ejemplo(str(base_temporal))
    conexion = conectar(base_temporal)
    try:
        resultado = registrar_reserva(conexion, 4, "22.222.222-2")
        reserva_id = resultado["reserva"]["id"]
    finally:
        conexion.close()

    escritura = ejecutar_proceso(
        CODIGO_ESCRITURA, base_temporal, str(reserva_id)
    )
    assert escritura.returncode == 0, escritura.stderr
    fecha_respuesta = json.loads(escritura.stdout.strip())["fecha_respuesta"]

    lectura = ejecutar_proceso(CODIGO_LECTURA, base_temporal)
    assert lectura.returncode == 0, lectura.stderr
    datos = json.loads(lectura.stdout.strip())

    reservas = {fila["id"]: fila for fila in datos["reservas"]}
    assert reservas[1]["estado"] == "Confirmada"
    assert reservas[reserva_id]["estado"] == "Sin confirmar"

    solicitudes_1 = [
        fila for fila in datos["solicitudes"] if fila["reserva_id"] == 1
    ]
    assert [fila["tipo"] for fila in solicitudes_1] == [
        TIPO_VISPERA,
        TIPO_RECORDATORIO,
    ]
    assert [fila["fecha_envio"] for fila in solicitudes_1] == [
        "2026-11-09",
        "2026-11-10",
    ]
    assert solicitudes_1[0]["estado"] == ESTADO_SOLICITUD_REEMPLAZADA
    assert solicitudes_1[0]["fecha_cierre"] == "2026-11-10"
    assert solicitudes_1[1]["estado"] == ESTADO_SOLICITUD_RESPONDIDA
    assert solicitudes_1[1]["respuesta"] == RESPUESTA_CONFIRMA
    assert solicitudes_1[1]["fecha_respuesta"] == fecha_respuesta
    assert solicitudes_1[1]["fecha_cierre"] is None

    solicitudes_nuevas = [
        fila
        for fila in datos["solicitudes"]
        if fila["reserva_id"] == reserva_id
    ]
    assert [fila["tipo"] for fila in solicitudes_nuevas] == [
        TIPO_VISPERA,
        TIPO_RECORDATORIO,
    ]
    assert [fila["fecha_envio"] for fila in solicitudes_nuevas] == [
        "2026-11-23",
        "2026-11-24",
    ]
    assert solicitudes_nuevas[0]["estado"] == ESTADO_SOLICITUD_REEMPLAZADA
    assert solicitudes_nuevas[0]["fecha_cierre"] == "2026-11-24"
    assert solicitudes_nuevas[1]["estado"] == ESTADO_SOLICITUD_VENCIDA
    assert solicitudes_nuevas[1]["respuesta"] == RESPUESTA_SIN_RESPUESTA
    assert solicitudes_nuevas[1]["fecha_respuesta"] is None
    assert solicitudes_nuevas[1]["fecha_cierre"] == "2026-11-24T10:00"

    assert len(datos["cargos"]) == 1
    cargo = datos["cargos"][0]
    assert cargo["paciente_id"] == 1
    assert cargo["reserva_id"] == reserva_id
    assert cargo["monto"] == 5000
    assert cargo["motivo"] == "sin confirmar"
    assert cargo["fecha"] == "2026-11-24"
