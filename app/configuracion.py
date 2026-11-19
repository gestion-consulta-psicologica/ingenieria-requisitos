from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.tiempo import ZONA_POR_DEFECTO


def _texto(nombre: str) -> str | None:
    valor = os.environ.get(nombre)
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


def _entero(nombre: str, por_defecto: int) -> int:
    valor = _texto(nombre)
    if valor is None:
        return por_defecto
    try:
        return int(valor)
    except ValueError as error:
        raise ValueError(
            f"La variable {nombre} debe ser un número entero."
        ) from error


def _booleano(nombre: str, por_defecto: bool) -> bool:
    valor = _texto(nombre)
    if valor is None:
        return por_defecto
    return valor.lower() in {"1", "si", "sí", "true", "yes", "on"}


def _hora(nombre: str, por_defecto: str) -> str:
    valor = _texto(nombre) or por_defecto
    partes = valor.split(":")
    if len(partes) != 2:
        raise ValueError(f"La variable {nombre} debe usar el formato HH:MM.")
    try:
        horas, minutos = int(partes[0]), int(partes[1])
    except ValueError as error:
        raise ValueError(
            f"La variable {nombre} debe usar el formato HH:MM."
        ) from error
    if not (0 <= horas <= 23 and 0 <= minutos <= 59):
        raise ValueError(f"La variable {nombre} no es una hora válida.")
    return f"{horas:02d}:{minutos:02d}"


@dataclass(frozen=True)
class ConfiguracionCorreo:
    smtp_host: str | None
    smtp_puerto: int
    smtp_usuario: str | None
    smtp_clave: str | None
    smtp_remitente: str | None
    smtp_seguridad: str
    smtp_timeout: int
    url_publica: str
    max_intentos: int
    reintento_base_segundos: int
    planificador_activo: bool
    intervalo_planificador_segundos: int
    timeout_envio_segundos: int
    hora_vispera: str
    hora_recordatorio: str
    zona_horaria: str

    @property
    def configurado(self) -> bool:
        return self.motivo_no_configurado is None

    @property
    def motivo_no_configurado(self) -> str | None:
        faltantes = []
        if not self.smtp_host:
            faltantes.append("SMTP_HOST")
        if not self.smtp_remitente:
            faltantes.append("SMTP_REMITENTE")
        if bool(self.smtp_usuario) != bool(self.smtp_clave):
            faltantes.append("SMTP_USUARIO y SMTP_CLAVE (deben definirse juntas)")
        if faltantes:
            return "Falta configurar: " + ", ".join(faltantes) + "."
        return None

    def destino_recordatorio(self, fecha: str) -> str:
        return f"{fecha} a las {self.hora_recordatorio} ({self.zona_horaria})"

    def destino_vispera(self, fecha: str) -> str:
        return f"{fecha} a las {self.hora_vispera} ({self.zona_horaria})"


def cargar_configuracion() -> ConfiguracionCorreo:
    seguridad = (_texto("SMTP_SEGURIDAD") or "starttls").lower()
    if seguridad not in {"starttls", "ssl", "ninguna"}:
        raise ValueError(
            "La variable SMTP_SEGURIDAD debe ser starttls, ssl o ninguna."
        )
    return ConfiguracionCorreo(
        smtp_host=_texto("SMTP_HOST"),
        smtp_puerto=_entero("SMTP_PORT", 587),
        smtp_usuario=_texto("SMTP_USUARIO"),
        smtp_clave=_texto("SMTP_CLAVE"),
        smtp_remitente=_texto("SMTP_REMITENTE"),
        smtp_seguridad=seguridad,
        smtp_timeout=_entero("SMTP_TIMEOUT", 10),
        url_publica=(_texto("CORREO_URL_PUBLICA") or "http://localhost:8000").rstrip(
            "/"
        ),
        max_intentos=_entero("CORREO_MAX_INTENTOS", 5),
        reintento_base_segundos=_entero("CORREO_REINTENTO_BASE_SEGUNDOS", 60),
        planificador_activo=_booleano("PLANIFICADOR_ACTIVO", True),
        intervalo_planificador_segundos=_entero(
            "PLANIFICADOR_INTERVALO_SEGUNDOS", 60
        ),
        timeout_envio_segundos=_entero("PLANIFICADOR_TIMEOUT_ENVIO_SEGUNDOS", 300),
        hora_vispera=_hora("CONFIRMACION_HORA_VISPERA", "09:00"),
        hora_recordatorio=_hora("CONFIRMACION_HORA_RECORDATORIO", "08:00"),
        zona_horaria=_texto("ZONA_HORARIA") or ZONA_POR_DEFECTO,
    )


def ruta_base_datos_desde_entorno(por_defecto: Path) -> Path:
    return Path(os.environ.get("CONSULTA_DB", por_defecto))
