from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.db.conexion import inicializar_base
from app.rutas.disponibilidad import router as disponibilidad_router
from app.rutas.paciente import router as paciente_router
from app.rutas.reserva import router as reserva_router
from app.servicios.correo import ServicioCorreo, ServicioCorreoSMTP
from app.servicios.planificador import PlanificadorCorreos, estado_planificador
from app.tiempo import a_local_texto

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

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


def crear_app(
    ruta_db: str | Path | None = None,
    servicio_correo: ServicioCorreo | None = None,
    configuracion: ConfiguracionCorreo | None = None,
    planificador_activo: bool | None = None,
) -> FastAPI:
    ruta = inicializar_base(ruta_db)
    config = configuracion or cargar_configuracion()
    correo = servicio_correo or ServicioCorreoSMTP(config)
    activo = (
        config.planificador_activo
        if planificador_activo is None
        else planificador_activo
    )
    planificador = (
        PlanificadorCorreos(str(ruta), correo, config) if activo else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if planificador is not None:
            await planificador.iniciar()
        yield
        if planificador is not None:
            await planificador.detener()

    app = FastAPI(
        title="Gestión de consulta psicológica",
        lifespan=lifespan,
    )
    app.state.ruta_db = str(ruta)
    app.state.configuracion_correo = config
    app.state.servicio_correo = correo
    app.state.correo_configurado = correo.configurado()
    app.state.correo_motivo = correo.motivo_no_configurado()
    app.state.planificador = planificador

    if not correo.configurado():
        logger.warning(
            "El servicio de correo no está configurado: %s",
            correo.motivo_no_configurado(),
        )
    if not activo:
        logger.warning("El planificador automático de correos está desactivado.")

    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    templates.env.filters["fecha_larga"] = fecha_larga
    templates.env.filters["fecha_dia"] = fecha_dia
    templates.env.filters["fecha_hora_local"] = lambda valor: a_local_texto(
        valor, config.zona_horaria
    )
    templates.env.globals["estado_planificador"] = estado_planificador
    app.state.templates = templates

    app.include_router(disponibilidad_router)
    app.include_router(reserva_router)
    app.include_router(paciente_router)

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse(url="/disponibilidad", status_code=303)

    return app
