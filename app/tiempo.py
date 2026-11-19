from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

ZONA_POR_DEFECTO = "America/Santiago"


def zona(nombre: str = ZONA_POR_DEFECTO) -> ZoneInfo:
    return ZoneInfo(nombre)


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def ahora_local(nombre_zona: str = ZONA_POR_DEFECTO) -> datetime:
    return ahora_utc().astimezone(zona(nombre_zona))


def a_utc(valor: datetime, nombre_zona: str = ZONA_POR_DEFECTO) -> datetime:
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=zona(nombre_zona))
    return valor.astimezone(timezone.utc)


def programado(
    fecha: str | date,
    hora: str,
    nombre_zona: str = ZONA_POR_DEFECTO,
) -> datetime:
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)
    partes = hora.split(":")
    momento = time(hour=int(partes[0]), minute=int(partes[1]))
    return datetime.combine(fecha, momento, tzinfo=zona(nombre_zona)).astimezone(
        timezone.utc
    )


def iso_utc(valor: datetime | None = None) -> str:
    valor = valor or ahora_utc()
    return valor.astimezone(timezone.utc).isoformat(timespec="seconds")


def desde_iso_utc(valor: str) -> datetime:
    fecha = datetime.fromisoformat(valor)
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def a_local_texto(valor: str | None, nombre_zona: str = ZONA_POR_DEFECTO) -> str:
    if not valor:
        return "—"
    try:
        fecha = desde_iso_utc(valor)
    except ValueError:
        return valor
    return fecha.astimezone(zona(nombre_zona)).isoformat(
        sep=" ", timespec="minutes"
    )
