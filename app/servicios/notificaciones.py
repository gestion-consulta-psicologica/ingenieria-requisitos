from __future__ import annotations

import sqlite3
from datetime import datetime

from app.configuracion import ConfiguracionCorreo
from app.servicios import cola_correo, plantillas_correo
from app.tiempo import ahora_utc


def encolar_aviso_reserva(
    conexion: sqlite3.Connection,
    paciente: dict,
    bloque: dict,
    reserva: dict,
    configuracion: ConfiguracionCorreo,
    ahora: datetime | None = None,
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
    conexion.commit()
    return fila
