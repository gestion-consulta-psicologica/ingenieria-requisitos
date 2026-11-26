"""Prueba la configuración SMTP enviando un correo a la dirección indicada.

Uso (con las variables SMTP_* ya cargadas en la terminal):

    python -m app.probar_correo tu-correo@example.com

No toca la base de datos ni la cola de correos: solo abre la conexión SMTP con
la configuración del entorno y envía un mensaje de prueba.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.servicios.correo import (
    CorreoNoConfigurado,
    ErrorAutenticacionSMTP,
    ErrorConexionSMTP,
    ErrorEnvioSMTP,
    ServicioCorreoSMTP,
)

CONSEJO_GMAIL_AUTENTICACION = (
    "Gmail rechazó el usuario o la clave. Usa una *contraseña de aplicación* de 16 "
    "caracteres (no tu contraseña normal): https://myaccount.google.com/apppasswords "
    "(requiere la verificación en 2 pasos activa). SMTP_USUARIO debe ser la dirección "
    "completa de Gmail."
)
CONSEJO_GMAIL_CONEXION = (
    "No se pudo conectar. Para Gmail usa SMTP_HOST=smtp.gmail.com, SMTP_PORT=587 y "
    "SMTP_SEGURIDAD=starttls (o 465 con ssl). Revisa también tu conexión a internet."
)
CONSEJO_GMAIL_ENVIO = (
    "El servidor rechazó el mensaje. En Gmail, SMTP_REMITENTE debe ser la misma cuenta "
    "de SMTP_USUARIO o un alias verificado de esa cuenta."
)


def _resumen(configuracion: ConfiguracionCorreo) -> str:
    usuario = configuracion.smtp_usuario or "(sin usuario)"
    return (
        f"Servidor: {configuracion.smtp_host}:{configuracion.smtp_puerto} "
        f"({configuracion.smtp_seguridad}) · Usuario: {usuario} · "
        f"Remitente: {configuracion.smtp_remitente}"
    )


def probar(destinatario: str, configuracion: ConfiguracionCorreo | None = None) -> int:
    configuracion = configuracion or cargar_configuracion()
    servicio = ServicioCorreoSMTP(configuracion)
    if not servicio.configurado():
        print(f"Correo no configurado: {servicio.motivo_no_configurado()}", file=sys.stderr)
        return 2
    es_gmail = "gmail" in (configuracion.smtp_host or "").lower()
    print(_resumen(configuracion))
    try:
        id_mensaje = servicio.enviar(
            destinatario,
            "Prueba de correo · Consulta psicológica",
            "Este es un correo de prueba de la configuración SMTP de la consulta.\n"
            "Si lo recibiste, los avisos y las solicitudes de confirmación llegarán bien.",
        )
    except CorreoNoConfigurado as error:
        print(f"Correo no configurado: {error}", file=sys.stderr)
        return 2
    except ErrorAutenticacionSMTP as error:
        print(f"Error de autenticación: {error}", file=sys.stderr)
        if es_gmail:
            print(CONSEJO_GMAIL_AUTENTICACION, file=sys.stderr)
        return 3
    except ErrorConexionSMTP as error:
        print(f"Error de conexión: {error}", file=sys.stderr)
        if es_gmail:
            print(CONSEJO_GMAIL_CONEXION, file=sys.stderr)
        return 4
    except ErrorEnvioSMTP as error:
        print(f"Error de envío: {error}", file=sys.stderr)
        if es_gmail:
            print(CONSEJO_GMAIL_ENVIO, file=sys.stderr)
        return 5
    print(f"Correo aceptado por el servidor SMTP (Message-ID {id_mensaje}). Revisa la bandeja de {destinatario}.")
    return 0


def main() -> None:
    argumentos = ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("destinatario", help="Dirección a la que enviar el correo de prueba.")
    sys.exit(probar(argumentos.parse_args().destinatario))


if __name__ == "__main__":
    main()
