from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from secrets import token_bytes, token_urlsafe
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.db.conexion import inicializar_base, ruta_operativa
from app.rutas.cuentas import estado_sesion, router as cuentas_router, verificar_csrf
from app.rutas.disponibilidad import router as disponibilidad_router
from app.rutas.paciente import router as paciente_router
from app.rutas.pagos import router as pagos_router
from app.rutas.psicologa import router as psicologa_router
from app.rutas.clinica import router as clinica_router
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


def monto_clp(valor: int) -> str:
    return f"${valor:,}".replace(",", ".")


def crear_app(
    ruta_db: str | Path | None = None,
    servicio_correo: ServicioCorreo | None = None,
    configuracion: ConfiguracionCorreo | None = None,
    planificador_activo: bool | None = None,
    *,
    clave_psicologa_demo: str | None = None,
    clave_paciente_demo: str | None = None,
    cuentas_persistentes: bool = False,
) -> FastAPI:
    if cuentas_persistentes:
        if clave_paciente_demo or clave_psicologa_demo:
            raise ValueError("Las cuentas persistentes y el acceso de demostración son excluyentes.")
        ruta_db = ruta_operativa(ruta_db)
    config = configuracion or cargar_configuracion()
    if cuentas_persistentes and servicio_correo is None and config.configurado:
        url = urlsplit(config.url_publica)
        if (config.smtp_seguridad == "ninguna" or url.scheme != "https"
                or not url.hostname or url.username or url.query or url.fragment):
            raise ValueError("Para enviar correo operativo configura SMTP con TLS y una URL pública HTTPS.")
    ruta = inicializar_base(ruta_db)
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
        dependencies=[Depends(verificar_csrf)],
    )
    app.state.ruta_db = str(ruta)
    app.state.configuracion_correo = config
    app.state.servicio_correo = correo
    app.state.correo_configurado = correo.configurado()
    app.state.correo_motivo = correo.motivo_no_configurado()
    app.state.planificador = planificador
    app.state.clave_psicologa_demo = clave_psicologa_demo
    app.state.clave_paciente_demo = clave_paciente_demo
    app.state.cuentas_persistentes = cuentas_persistentes
    app.state.clave_acceso_reserva = None if cuentas_persistentes else token_bytes(32)
    app.state.csrf_psicologa_demo = None if cuentas_persistentes else token_urlsafe()
    app.middleware("http")(estado_sesion)

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
    templates.env.filters["clp"] = monto_clp
    templates.env.filters["fecha_hora_local"] = lambda valor: a_local_texto(
        valor, config.zona_horaria
    )
    templates.env.globals["estado_planificador"] = estado_planificador
    app.state.templates = templates

    app.include_router(disponibilidad_router)
    app.include_router(reserva_router)
    app.include_router(paciente_router)
    app.include_router(pagos_router)
    app.include_router(psicologa_router)
    app.include_router(clinica_router)
    app.include_router(cuentas_router)

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse(url="/disponibilidad", status_code=303)

    return app
