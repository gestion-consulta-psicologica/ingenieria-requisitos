from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.conexion import inicializar_base
from app.rutas.disponibilidad import router as disponibilidad_router

BASE_DIR = Path(__file__).resolve().parent

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


def fecha_larga(valor: date | str) -> str:
    if isinstance(valor, str):
        valor = date.fromisoformat(valor)
    return f"{valor.day} de {MESES[valor.month - 1]} de {valor.year}"


def fecha_dia(valor: date | str) -> str:
    if isinstance(valor, str):
        valor = date.fromisoformat(valor)
    return f"{DIAS[valor.weekday()]} {valor.day} de {MESES[valor.month - 1]}"


def crear_app(ruta_db: str | Path | None = None) -> FastAPI:
    ruta = inicializar_base(ruta_db)
    app = FastAPI(title="Gestión de consulta psicológica")
    app.state.ruta_db = str(ruta)

    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    templates.env.filters["fecha_larga"] = fecha_larga
    templates.env.filters["fecha_dia"] = fecha_dia
    app.state.templates = templates

    app.include_router(disponibilidad_router)

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse(url="/disponibilidad", status_code=303)

    return app


app = crear_app()
