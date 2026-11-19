from __future__ import annotations

from app.db.conexion import RUTA_DB_POR_DEFECTO, ruta_base_datos


def test_pytest_usa_base_temporal():
    ruta = ruta_base_datos().resolve()
    assert ruta != RUTA_DB_POR_DEFECTO.resolve()
    assert "consulta-pytest-" in str(ruta)
