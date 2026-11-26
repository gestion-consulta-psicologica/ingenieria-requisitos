"""HU-06 (extensión) — Rutas para pagar (paciente) y verificar (psicóloga) los cargos."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasicCredentials

from app.rutas.acceso_reserva import accesos_del_navegador, verificar_titular
from app.rutas.disponibilidad import obtener_conexion
from app.rutas.psicologa import autenticacion, autenticar_psicologa, verificar_formulario_psicologa
from app.servicios.atenciones import DatosComprobanteInvalidos
from app.servicios.cargos import (
    CargoNoEncontrado,
    CargoYaPagado,
    VerificacionCargoInvalida,
    listar_cargos_con_saldo,
    listar_cargos_de_pacientes,
    obtener_cargo,
    registrar_comprobante_cargo,
    verificar_pago_cargo,
)

router = APIRouter()
SIN_CACHE = {"Cache-Control": "no-store"}


def _pacientes_del_usuario(
    request: Request, conexion: sqlite3.Connection, credenciales: HTTPBasicCredentials | None,
) -> set[int]:
    if request.app.state.cuentas_persistentes:
        cuenta = request.state.cuenta
        return {cuenta["paciente_id"]} if cuenta and cuenta["paciente_id"] else set()
    pacientes, reservas = accesos_del_navegador(request, credenciales)
    if reservas:
        marcas = ", ".join("?" for _ in reservas)
        pacientes |= {
            fila[0] for fila in conexion.execute(
                f"SELECT paciente_id FROM reserva WHERE id IN ({marcas})", tuple(reservas),
            )
        }
    return pacientes


def _cargo_del_titular(
    cargo_id: int, request: Request, conexion: sqlite3.Connection,
    credenciales: HTTPBasicCredentials | None,
) -> dict:
    cargo = obtener_cargo(conexion, cargo_id)
    if cargo is None:
        raise HTTPException(404, detail="No se encontró el cargo.")
    verificar_titular(request, cargo["reserva_origen"], cargo["paciente_id"], credenciales)
    return cargo


def _vista(request: Request, nombre: str, status_code: int = 200, **contexto):
    return request.app.state.templates.TemplateResponse(
        request=request, name=nombre, context=contexto,
        status_code=status_code, headers=SIN_CACHE,
    )


# --- Paciente ---------------------------------------------------------------

@router.get("/cargos", response_class=HTMLResponse)
def mis_cargos(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    if request.app.state.cuentas_persistentes and not request.state.cuenta:
        return RedirectResponse("/cuenta/ingresar", status_code=303)
    cargos = listar_cargos_de_pacientes(conexion, _pacientes_del_usuario(request, conexion, credenciales))
    return _vista(request, "cargos_lista.html", cargos=cargos, vista="paciente")


@router.get("/cargos/{cargo_id}", response_class=HTMLResponse)
def ver_cargo(
    cargo_id: int, request: Request, registrado: bool = False,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    cargo = _cargo_del_titular(cargo_id, request, conexion, credenciales)
    return _vista(
        request, "cargo_detalle.html", cargo=cargo, vista="paciente",
        registrado=registrado, errores={}, valores={"monto": cargo["saldo"]},
    )


@router.post("/cargos/{cargo_id}/comprobante", response_class=HTMLResponse)
def registrar_comprobante(
    cargo_id: int, request: Request,
    monto: str = Form(""), fecha_transferencia: str = Form(""), cuenta_destino: str = Form(""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    cargo = _cargo_del_titular(cargo_id, request, conexion, credenciales)
    valores = {"monto": monto, "fecha_transferencia": fecha_transferencia, "cuenta_destino": cuenta_destino}
    try:
        registrar_comprobante_cargo(conexion, cargo_id, monto, fecha_transferencia, cuenta_destino)
    except DatosComprobanteInvalidos as error:
        return _vista(request, "cargo_detalle.html", 400, cargo=cargo, vista="paciente",
                      error=error.mensaje, errores=error.errores, valores=valores)
    except (CargoYaPagado, CargoNoEncontrado) as error:
        return _vista(request, "cargo_detalle.html", 409, cargo=cargo, vista="paciente",
                      error=str(error), errores={}, valores=valores)
    return RedirectResponse(f"/cargos/{cargo_id}?registrado=1", status_code=303)


# --- Psicóloga --------------------------------------------------------------

@router.get("/psicologa/cargos", response_class=HTMLResponse, dependencies=[Depends(autenticar_psicologa)])
def cargos_con_saldo(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    return _vista(request, "cargos_lista.html", cargos=listar_cargos_con_saldo(conexion), vista="psicologa")


@router.get("/psicologa/cargos/{cargo_id}", response_class=HTMLResponse, dependencies=[Depends(autenticar_psicologa)])
def revisar_cargo(
    cargo_id: int, request: Request, actualizado: bool = False,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    cargo = obtener_cargo(conexion, cargo_id)
    if cargo is None:
        raise HTTPException(404, detail="No se encontró el cargo.")
    return _vista(request, "cargo_detalle.html", cargo=cargo, vista="psicologa", actualizado=actualizado)


@router.post("/psicologa/cargos/{cargo_id}/estado", dependencies=[Depends(autenticar_psicologa)])
def registrar_estado_cargo(
    cargo_id: int, request: Request,
    comprobantes: list[int] = Form(default=[]), estado: str = Form(), csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    try:
        verificar_pago_cargo(conexion, cargo_id, comprobantes, estado_elegido=estado)
    except CargoNoEncontrado as error:
        raise HTTPException(404, detail=str(error)) from error
    except VerificacionCargoInvalida as error:
        raise HTTPException(409, detail=str(error)) from error
    return RedirectResponse(f"/psicologa/cargos/{cargo_id}?actualizado=1", status_code=303)
