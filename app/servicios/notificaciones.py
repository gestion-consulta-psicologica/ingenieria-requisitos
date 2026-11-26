from __future__ import annotations

import sqlite3
from datetime import datetime

from app.configuracion import ConfiguracionCorreo
from app.servicios import cola_correo, plantillas_correo
from app.tiempo import ahora_utc

MONTO_CARGO = 5000
MOTIVO_CANCELACION = "cancelación"


def registrar_cargo_con_aviso(
    conexion: sqlite3.Connection,
    contexto: dict,
    motivo: str,
    configuracion: ConfiguracionCorreo,
    ahora: datetime,
) -> tuple[sqlite3.Row, sqlite3.Row]:
    reserva = contexto["reserva"]
    paciente = contexto["paciente"]
    bloque = contexto["bloque"]
    cursor = conexion.execute(
        """
        INSERT INTO cargo (paciente_id, reserva_id, monto, motivo, fecha)
        VALUES (?, ?, ?, ?, ?)
        """,
        (reserva["paciente_id"], reserva["id"], MONTO_CARGO, motivo, bloque["fecha"]),
    )
    cargo = conexion.execute(
        "SELECT * FROM cargo WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    correo = plantillas_correo.aviso_cargo(paciente, reserva, cargo, bloque)
    trabajo = cola_correo.encolar(
        conexion,
        clave=f"cargo:{cargo['id']}",
        tipo=cola_correo.TIPO_AVISO_CARGO,
        asunto=correo.asunto,
        cuerpo_texto=correo.texto,
        cuerpo_html=correo.html,
        destinatario=paciente["correo"],
        reserva_id=reserva["id"],
        solicitud_id=None,
        creado_en=ahora,
        max_intentos=configuracion.max_intentos,
    )
    if trabajo is None:
        raise sqlite3.IntegrityError("El aviso de cargo no quedó encolado.")
    return cargo, trabajo


def encolar_aviso_reserva(
    conexion: sqlite3.Connection,
    paciente: dict,
    bloque: dict,
    reserva: dict,
    configuracion: ConfiguracionCorreo,
    ahora: datetime | None = None,
    *,
    confirmar_transaccion: bool = True,
) -> sqlite3.Row:
    correo = plantillas_correo.aviso_reserva(paciente, bloque, reserva)
    fila = cola_correo.encolar(
        conexion,
        clave=f"aviso_reserva:{reserva['id']}",
        tipo=cola_correo.TIPO_AVISO_RESERVA,
        asunto=correo.asunto,
        cuerpo_texto=correo.texto,
        cuerpo_html=correo.html,
        destinatario=paciente["correo"],
        reserva_id=reserva["id"],
        solicitud_id=None,
        creado_en=ahora or ahora_utc(),
        max_intentos=configuracion.max_intentos,
    )
    if fila is None:
        raise sqlite3.IntegrityError("El aviso de reserva no quedó encolado.")
    if confirmar_transaccion:
        conexion.commit()
    return fila
