from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date

MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
DIAS = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)


@dataclass(frozen=True)
class Correo:
    asunto: str
    texto: str
    html: str


def _fecha_larga(valor: str) -> str:
    fecha = date.fromisoformat(valor)
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def _monto(valor: int) -> str:
    return f"${valor:,}".replace(",", ".")


def _html(cuerpo: str) -> str:
    return (
        "<html><body style=\"font-family:system-ui,sans-serif;color:#1f2937\">"
        f"{cuerpo}"
        "<p style=\"color:#6b7280;font-size:12px\">"
        "Este mensaje fue generado automáticamente por la Gestión de consulta "
        "psicológica. No responda a este correo."
        "</p></body></html>"
    )


def aviso_reserva(paciente: dict, bloque: dict, reserva: dict) -> Correo:
    fecha = _fecha_larga(bloque["fecha"])
    asunto = f"Reserva registrada para el {fecha}"
    texto = (
        f"Hola {paciente['nombre_completo']}:\n\n"
        "Tu reserva quedó registrada.\n"
        f"Fecha: {fecha}\n"
        f"Hora: {bloque['hora_inicio']} a {bloque['hora_termino']}\n"
        f"Modalidad: {bloque['modalidad']}\n"
        f"Número de reserva: {reserva['id']}\n\n"
        "El día anterior a la atención recibirás la solicitud de confirmación.\n"
    )
    cuerpo = (
        f"<h2>Reserva registrada</h2><p>Hola {html.escape(paciente['nombre_completo'])}:</p>"
        "<p>Tu reserva quedó registrada.</p>"
        f"<p><strong>Fecha:</strong> {fecha}<br>"
        f"<strong>Hora:</strong> {bloque['hora_inicio']} a {bloque['hora_termino']}<br>"
        f"<strong>Modalidad:</strong> {html.escape(str(bloque['modalidad']))}<br>"
        f"<strong>Número de reserva:</strong> {reserva['id']}</p>"
        "<p>El día anterior a la atención recibirás la solicitud de confirmación.</p>"
    )
    return Correo(asunto=asunto, texto=texto, html=_html(cuerpo))


def aviso_reagendamiento(
    paciente: dict, bloque_anterior: dict, bloque_nuevo: dict, reserva: dict
) -> Correo:
    fecha_anterior = _fecha_larga(bloque_anterior["fecha"])
    fecha_nueva = _fecha_larga(bloque_nuevo["fecha"])
    asunto = f"Reserva reagendada para el {fecha_nueva}"
    texto = (
        f"Hola {paciente['nombre_completo']}:\n\n"
        "Tu reserva fue reagendada correctamente.\n"
        f"Horario anterior: {fecha_anterior}, "
        f"{bloque_anterior['hora_inicio']} a {bloque_anterior['hora_termino']}\n"
        f"Nuevo horario: {fecha_nueva}, "
        f"{bloque_nuevo['hora_inicio']} a {bloque_nuevo['hora_termino']}\n"
        f"Modalidad: {bloque_nuevo['modalidad']}\n"
        f"Número de reserva: {reserva['id']}\n\n"
        "La reserva queda pendiente de confirmación. El día anterior a la nueva "
        "atención recibirás la solicitud de confirmación.\n"
    )
    cuerpo = (
        "<h2>Reserva reagendada</h2>"
        f"<p>Hola {html.escape(paciente['nombre_completo'])}:</p>"
        "<p>Tu reserva fue reagendada correctamente.</p>"
        f"<p><strong>Horario anterior:</strong> {fecha_anterior}, "
        f"{bloque_anterior['hora_inicio']} a {bloque_anterior['hora_termino']}<br>"
        f"<strong>Nuevo horario:</strong> {fecha_nueva}, "
        f"{bloque_nuevo['hora_inicio']} a {bloque_nuevo['hora_termino']}<br>"
        f"<strong>Modalidad:</strong> {html.escape(str(bloque_nuevo['modalidad']))}<br>"
        f"<strong>Número de reserva:</strong> {reserva['id']}</p>"
        "<p>La reserva queda pendiente de confirmación. El día anterior a la nueva "
        "atención recibirás la solicitud de confirmación.</p>"
    )
    return Correo(asunto=asunto, texto=texto, html=_html(cuerpo))


def solicitud_confirmacion(
    paciente: dict,
    bloque: dict,
    reserva: dict,
    tipo: str,
    enlace_confirmar: str,
    enlace_cancelar: str,
) -> Correo:
    fecha = _fecha_larga(bloque["fecha"])
    es_recordatorio = tipo == "recordatorio"
    asunto = (
        f"Recordatorio: confirma tu hora del {fecha}"
        if es_recordatorio
        else f"Confirma tu hora del {fecha}"
    )
    introduccion = (
        "Este es un recordatorio de tu hora reservada."
        if es_recordatorio
        else "Ya está disponible la confirmación de tu hora reservada."
    )
    texto = (
        f"Hola {paciente['nombre_completo']}:\n\n"
        f"{introduccion}\n"
        f"Fecha: {fecha}\n"
        f"Hora: {bloque['hora_inicio']} a {bloque['hora_termino']}\n"
        f"Modalidad: {bloque['modalidad']}\n"
        f"Número de reserva: {reserva['id']}\n\n"
        "Para confirmar tu asistencia abre este enlace:\n"
        f"{enlace_confirmar}\n\n"
        "Si no podrás asistir, abre este enlace:\n"
        f"{enlace_cancelar}\n\n"
        "Si no respondes antes de la hora de la atención, la reserva quedará "
        "sin confirmar y se registrará el cargo por reserva de hora.\n"
    )
    cuerpo = (
        "<h2>Confirmación de asistencia</h2>"
        f"<p>Hola {html.escape(paciente['nombre_completo'])}:</p>"
        f"<p>{introduccion}</p>"
        f"<p><strong>Fecha:</strong> {fecha}<br>"
        f"<strong>Hora:</strong> {bloque['hora_inicio']} a {bloque['hora_termino']}<br>"
        f"<strong>Modalidad:</strong> {html.escape(str(bloque['modalidad']))}<br>"
        f"<strong>Número de reserva:</strong> {reserva['id']}</p>"
        f"<p><a href=\"{html.escape(enlace_confirmar)}\">Confirmar asistencia</a></p>"
        f"<p><a href=\"{html.escape(enlace_cancelar)}\">No podré asistir</a></p>"
        "<p>Si no respondes antes de la hora de la atención, la reserva quedará "
        "sin confirmar y se registrará el cargo por reserva de hora.</p>"
    )
    return Correo(asunto=asunto, texto=texto, html=_html(cuerpo))


def aviso_cargo(paciente: dict, reserva: dict, cargo: dict, bloque: dict) -> Correo:
    fecha = _fecha_larga(bloque["fecha"])
    asunto = f"Cargo por reserva de hora del {fecha}"
    texto = (
        f"Hola {paciente['nombre_completo']}:\n\n"
        "No se recibió la confirmación de asistencia antes de la hora de la "
        "atención, por lo que la reserva quedó sin confirmar.\n"
        f"Fecha de la atención: {fecha}\n"
        f"Hora: {bloque['hora_inicio']} a {bloque['hora_termino']}\n"
        f"Número de reserva: {reserva['id']}\n"
        f"Monto del cargo: {_monto(cargo['monto'])}\n"
        f"Motivo: {cargo['motivo']}\n\n"
        "El cargo es un registro administrativo; el pago se gestiona por los "
        "canales habituales.\n"
    )
    cuerpo = (
        "<h2>Cargo por reserva de hora</h2>"
        f"<p>Hola {html.escape(paciente['nombre_completo'])}:</p>"
        "<p>No se recibió la confirmación de asistencia antes de la hora de la "
        "atención, por lo que la reserva quedó sin confirmar.</p>"
        f"<p><strong>Fecha de la atención:</strong> {fecha}<br>"
        f"<strong>Hora:</strong> {bloque['hora_inicio']} a {bloque['hora_termino']}<br>"
        f"<strong>Número de reserva:</strong> {reserva['id']}<br>"
        f"<strong>Monto del cargo:</strong> {_monto(cargo['monto'])}<br>"
        f"<strong>Motivo:</strong> {html.escape(str(cargo['motivo']))}</p>"
        "<p>El cargo es un registro administrativo; el pago se gestiona por los "
        "canales habituales.</p>"
    )
    return Correo(asunto=asunto, texto=texto, html=_html(cuerpo))
