from __future__ import annotations

import logging
import smtplib
import socket
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Protocol

from app.configuracion import ConfiguracionCorreo

logger = logging.getLogger(__name__)


class CorreoNoConfigurado(RuntimeError):
    """El servicio SMTP no tiene la configuración mínima."""


class ErrorConexionSMTP(RuntimeError):
    """No fue posible conectarse al servidor SMTP."""


class ErrorAutenticacionSMTP(RuntimeError):
    """El servidor SMTP rechazó las credenciales."""


class ErrorEnvioSMTP(RuntimeError):
    """El servidor SMTP rechazó el mensaje o falló durante el envío."""


class ServicioCorreo(Protocol):
    def configurado(self) -> bool:
        ...

    def motivo_no_configurado(self) -> str | None:
        ...

    def enviar(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_texto: str,
        cuerpo_html: str | None = None,
    ) -> str:
        ...


class ServicioCorreoSMTP:
    """Adaptador SMTP desacoplado del resto de la aplicación."""

    def __init__(self, configuracion: ConfiguracionCorreo):
        self.configuracion = configuracion

    def configurado(self) -> bool:
        return self.configuracion.configurado

    def motivo_no_configurado(self) -> str | None:
        return self.configuracion.motivo_no_configurado

    def _mensaje(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_texto: str,
        cuerpo_html: str | None,
    ) -> EmailMessage:
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = self.configuracion.smtp_remitente or ""
        mensaje["To"] = destinatario
        mensaje["Date"] = formatdate(localtime=False)
        mensaje["Message-ID"] = make_msgid(
            domain=(self.configuracion.smtp_remitente or "localhost").split("@")[-1]
        )
        mensaje.set_content(cuerpo_texto)
        if cuerpo_html:
            mensaje.add_alternative(cuerpo_html, subtype="html")
        return mensaje

    def enviar(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_texto: str,
        cuerpo_html: str | None = None,
    ) -> str:
        if not self.configurado():
            raise CorreoNoConfigurado(
                self.motivo_no_configurado()
                or "El servicio SMTP no está configurado."
            )

        config = self.configuracion
        mensaje = self._mensaje(destinatario, asunto, cuerpo_texto, cuerpo_html)
        cliente: smtplib.SMTP | None = None
        try:
            if config.smtp_seguridad == "ssl":
                cliente = smtplib.SMTP_SSL(
                    config.smtp_host,
                    config.smtp_puerto,
                    timeout=config.smtp_timeout,
                )
            else:
                cliente = smtplib.SMTP(
                    config.smtp_host,
                    config.smtp_puerto,
                    timeout=config.smtp_timeout,
                )
                cliente.ehlo()
                if config.smtp_seguridad == "starttls":
                    cliente.starttls()
                    cliente.ehlo()

            if config.smtp_usuario and config.smtp_clave:
                cliente.login(config.smtp_usuario, config.smtp_clave)

            cliente.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as error:
            raise ErrorAutenticacionSMTP(
                "El servidor SMTP rechazó las credenciales configuradas."
            ) from error
        except (
            smtplib.SMTPConnectError,
            smtplib.SMTPServerDisconnected,
            ConnectionRefusedError,
            TimeoutError,
            socket.gaierror,
        ) as error:
            raise ErrorConexionSMTP(
                "No fue posible conectarse al servidor SMTP."
            ) from error
        except smtplib.SMTPException as error:
            raise ErrorEnvioSMTP(
                "El servidor SMTP rechazó el mensaje."
            ) from error
        except OSError as error:
            raise ErrorConexionSMTP(
                "No fue posible conectarse al servidor SMTP."
            ) from error
        finally:
            if cliente is not None:
                try:
                    cliente.quit()
                except (smtplib.SMTPException, OSError):
                    pass

        return str(mensaje["Message-ID"])
