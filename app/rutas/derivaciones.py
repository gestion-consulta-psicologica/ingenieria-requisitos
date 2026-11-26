import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import derivaciones
from app.rutas.cuentas import modo_operativo
from app.rutas.disponibilidad import obtener_conexion
from app.rutas.psicologa import autenticar_psicologa
from app.servicios import derivaciones as servicio
from app.servicios.cuentas import CuentaInvalida

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


def vista(request, **contexto):
    return request.app.state.templates.TemplateResponse(
        request=request, name="derivaciones.html", context=contexto,
    )


@router.get(PANEL, response_class=HTMLResponse, dependencies=protegida)
def historial(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    return vista(
        request, registros=derivaciones.historial(conexion, request.state.cuenta["id"], recibidas=False),
        profesionales=derivaciones.psiquiatras(conexion, solo_disponibles=False),
    )


@router.get(PANEL + "/nueva/{reserva_id}", response_class=HTMLResponse, dependencies=protegida)
def formulario(reserva_id: IdRuta, request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    solicitud = derivaciones.solicitud(conexion, reserva_id, request.state.cuenta["id"])
    if solicitud is None:
        raise HTTPException(404, detail="Solicitud de consulta no disponible.")
    return vista(
        request, solicitud=solicitud,
        profesionales=derivaciones.psiquiatras(conexion, solo_disponibles=True),
    )


@router.post(PANEL + "/nueva/{reserva_id}", dependencies=protegida)
def crear(
    reserva_id: IdRuta, request: Request, psiquiatra_id: IdFormulario,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.crear_derivacion(conexion, reserva_id, request.state.cuenta["id"], psiquiatra_id)
    except servicio.SolicitudNoEncontrada as error:
        raise HTTPException(404, detail=str(error)) from error
    except servicio.DerivacionInvalida as error:
        raise HTTPException(409, detail=str(error)) from error
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
    return vista(request, recibidas=True, registros=derivaciones.historial(conexion, cuenta_id, recibidas=True))


@router.post(BANDEJA + "/{derivacion_id}/aceptar")
def aceptar(
    derivacion_id: IdRuta, cuenta_id: int = Depends(autenticar_psiquiatra),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        servicio.aceptar_derivacion(conexion, derivacion_id, cuenta_id)
    except servicio.DerivacionNoEncontrada as error:
        raise HTTPException(404, detail=str(error)) from error
    except servicio.DerivacionInvalida as error:
        raise HTTPException(409, detail=str(error)) from error
    return RedirectResponse(BANDEJA, status_code=303)
