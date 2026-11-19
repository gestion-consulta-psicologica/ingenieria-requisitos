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
