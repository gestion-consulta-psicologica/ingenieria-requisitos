from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_RUTA_DB_TEMPORAL = Path(
    tempfile.mkdtemp(prefix="consulta-pytest-")
) / "default.db"
os.environ["CONSULTA_DB"] = str(_RUTA_DB_TEMPORAL)
os.environ["PLANIFICADOR_ACTIVO"] = "0"
os.environ.pop("SMTP_HOST", None)
os.environ.pop("SMTP_REMITENTE", None)

from app.db.conexion import conectar, inicializar_base
from app.rutas import disponibilidad as ruta_disponibilidad
from app.rutas import reserva as ruta_reserva
from app.servicios import disponibilidad, reagendamiento
from app.tiempo import programado


@pytest.fixture(autouse=True)
def reloj_agenda(monkeypatch):
    instante = programado("2026-11-09", "08:00")
    for modulo in (disponibilidad, ruta_disponibilidad, ruta_reserva, reagendamiento):
        monkeypatch.setattr(modulo, "ahora_utc", lambda: instante)


@pytest.fixture
def base_temporal(tmp_path):
    ruta = tmp_path / "prueba.db"
    inicializar_base(ruta)
    return ruta


@pytest.fixture
def conexion(base_temporal):
    conexion = conectar(base_temporal)
    try:
        yield conexion
    finally:
        conexion.close()
