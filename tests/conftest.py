from __future__ import annotations

import pytest

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
