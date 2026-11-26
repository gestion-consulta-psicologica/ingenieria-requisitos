import sqlite3
from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import derivaciones
from app.rutas.cuentas import modo_operativo
from app.rutas.disponibilidad import obtener_conexion
from app.rutas.psicologa import autenticar_psicologa
from app.servicios import derivaciones as servicio
from app.servicios.cuentas import CuentaInvalida
from app.servicios.disponibilidad import DURACION_ATENCION, horario_dentro_de_jornada, insertar_bloque_libre
from app.tiempo import programado

router = APIRouter(dependencies=[Depends(modo_operativo)])
protegida = [Depends(autenticar_psicologa)]
IdRuta = Annotated[int, Path(gt=0, le=2**63 - 1)]
IdFormulario = Annotated[int, Form(gt=0, le=2**63 - 1)]
PANEL = "/psicologa/derivaciones"
BANDEJA = "/psiquiatra/derivaciones"


def autenticar_psiquiatra(request: Request):
    cuenta = request.state.cuenta
    if not cuenta or cuenta["rol"] != "psiquiatra":
        raise HTTPException(403 if cuenta else 401)
    return cuenta["id"]


def vista(request, *, status_code=200, **contexto):
    return request.app.state.templates.TemplateResponse(
        request=request, name="derivaciones.html", context=contexto,
        status_code=status_code,
    )


@router.get(PANEL, response_class=HTMLResponse, dependencies=protegida)
def historial(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    return vista(
        request, registros=derivaciones.historial(conexion, request.state.cuenta["id"], recibidas=False),
        profesionales=derivaciones.psiquiatras(conexion, solo_disponibles=False),
    )


@router.get(PANEL + "/nueva/{reserva_id}", response_class=HTMLResponse, dependencies=protegida)
def formulario(reserva_id: IdRuta, request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    return _formulario(request, conexion, reserva_id)


def _formulario(request, conexion, reserva_id, error=None):
    try:
        solicitud = servicio.solicitud_vigente(
            conexion, reserva_id, request.state.cuenta["id"],
            request.app.state.configuracion_correo.zona_horaria, servicio.ahora_utc(),
        )
    except servicio.SolicitudNoEncontrada as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    return vista(
        request, solicitud=solicitud,
        profesionales=derivaciones.destinos_para_solicitud(conexion, solicitud),
        error=error, status_code=409 if error else 200,
    )


@router.post(PANEL + "/nueva/{reserva_id}", dependencies=protegida)
def crear(
    reserva_id: IdRuta, request: Request, psiquiatra_id: IdFormulario,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.crear_derivacion(
            conexion, reserva_id, request.state.cuenta["id"], psiquiatra_id,
            configuracion=request.app.state.configuracion_correo,
        )
    except servicio.SolicitudNoEncontrada as error:
        raise HTTPException(404, detail=str(error)) from error
    except servicio.DerivacionInvalida as error:
        return _formulario(request, conexion, reserva_id, error=str(error))
    return RedirectResponse(PANEL, status_code=303)


@router.post(PANEL + "/psiquiatras", dependencies=protegida)
def registrar(
    nombre: Annotated[str, Form(min_length=1, max_length=200)],
    correo: Annotated[str, Form(min_length=1, max_length=254)],
    clave: Annotated[str, Form()],
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.registrar_psiquiatra(conexion, nombre, correo, clave)
    except CuentaInvalida as error:
        raise HTTPException(400, detail=str(error)) from error
    return RedirectResponse(PANEL + "#psiquiatras", status_code=303)


@router.post(PANEL + "/psiquiatras/{cuenta_id}/disponibilidad", dependencies=protegida)
def disponibilidad(
    cuenta_id: IdRuta, activo: Annotated[bool, Form()],
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.cambiar_disponibilidad(conexion, cuenta_id, activo)
    except CuentaInvalida as error:
        raise HTTPException(404, detail=str(error)) from error
    return RedirectResponse(PANEL + "#psiquiatras", status_code=303)


@router.get(BANDEJA, response_class=HTMLResponse)
def recibidas(
    request: Request, cuenta_id: int = Depends(autenticar_psiquiatra),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _bandeja(request, conexion, cuenta_id)


def _bandeja(request, conexion, cuenta_id, *, error=None, status_code=200):
    return vista(
        request, recibidas=True, registros=derivaciones.historial(conexion, cuenta_id, recibidas=True),
        agenda=derivaciones.bloques_de_psiquiatra(conexion, cuenta_id),
        error=error, status_code=status_code,
    )


@router.post(BANDEJA + "/horarios")
def agregar_horario(
    request: Request, fecha: Annotated[date, Form()], inicio: Annotated[time, Form()],
    modalidad: Annotated[str, Form()], cuenta_id: int = Depends(autenticar_psiquiatra),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    comienzo = datetime.combine(fecha, inicio)
    termino = comienzo + DURACION_ATENCION
    zona = request.app.state.configuracion_correo.zona_horaria
    if (
        inicio.tzinfo or inicio.second or inicio.microsecond or termino.date() != fecha
        or not horario_dentro_de_jornada(fecha, inicio, termino.time())
        or modalidad not in ("presencial", "online")
        or programado(fecha, inicio.isoformat(), zona) <= servicio.ahora_utc()
    ):
        return _bandeja(request, conexion, cuenta_id, error="Ingresa un bloque futuro dentro de la jornada.", status_code=400)
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        if not derivaciones.destino_disponible(conexion, cuenta_id):
            raise HTTPException(403)
        creado = insertar_bloque_libre(conexion, cuenta_id, comienzo, termino, modalidad, psiquiatra=True)
    if not creado:
        return _bandeja(request, conexion, cuenta_id, error="El bloque se superpone con otro de tu agenda.", status_code=409)
    return RedirectResponse(BANDEJA + "#agenda", status_code=303)


@router.post(BANDEJA + "/{derivacion_id}/aceptar")
@router.post(BANDEJA + "/{derivacion_id}/rechazar")
def aceptar(
    derivacion_id: IdRuta, request: Request, cuenta_id: int = Depends(autenticar_psiquiatra),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.responder_derivacion(
            conexion, derivacion_id, cuenta_id, acepta=request.url.path.endswith("/aceptar"),
            configuracion=request.app.state.configuracion_correo,
        )
    except servicio.DerivacionNoEncontrada as error:
        raise HTTPException(404, detail=str(error)) from error
    except servicio.DerivacionInvalida as error:
        return _bandeja(request, conexion, cuenta_id, error=str(error), status_code=409)
    return RedirectResponse(BANDEJA, status_code=303)
