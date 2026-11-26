from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasicCredentials

from app.rutas.acceso_reserva import conceder_acceso_paciente, verificar_paciente
from app.rutas.psicologa import autenticacion

from app.db.conexion import conectar
from app.servicios.paciente import DatosPacienteInvalidos, registrar_paciente
from app.servicios.reserva import normalizar_rut, obtener_bloque

router = APIRouter()


def obtener_conexion(request: Request):
    conexion = conectar(request.app.state.ruta_db)
    try:
        yield conexion
    finally:
        conexion.close()


def _render_formulario(
    request: Request,
    *,
    bloque_id: int | None = None,
    nombre_completo: str = "",
    rut: str = "",
    telefono: str = "",
    correo: str = "",
    error: str | None = None,
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="registro_paciente.html",
        context={
            "bloque_id": bloque_id,
            "nombre_completo": nombre_completo,
            "rut": rut,
            "telefono": telefono,
            "correo": correo,
            "error": error,
        },
        status_code=status_code,
    )


def _leer_bloque_id(valor: str) -> int | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return int(valor)
    except ValueError:
        return None


@router.get("/pacientes/registro", response_class=HTMLResponse)
def mostrar_registro(
    request: Request,
    bloque_id: int | None = None,
):
    if request.app.state.cuentas_persistentes:
        destino = f"/cuenta/registro?bloque_id={bloque_id}" if bloque_id else "/cuenta/registro"
        return RedirectResponse(destino, status_code=303)
    return _render_formulario(request, bloque_id=bloque_id)


@router.post("/pacientes/registro", response_class=HTMLResponse)
def registrar(
    request: Request,
    nombre_completo: str = Form(default=""),
    rut: str = Form(default=""),
    telefono: str = Form(default=""),
    correo: str = Form(default=""),
    bloque_id: str = Form(default=""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    bloque = _leer_bloque_id(bloque_id)
    if request.app.state.cuentas_persistentes:
        return mostrar_registro(request, bloque)
    try:
        resultado = registrar_paciente(
            conexion, nombre_completo, rut, telefono, correo
        )
    except DatosPacienteInvalidos as error:
        return _render_formulario(
            request,
            bloque_id=bloque,
            nombre_completo=nombre_completo,
            rut=rut,
            telefono=telefono,
            correo=correo,
            error=str(error),
            status_code=400,
        )

    paciente = resultado["paciente"]
    if not resultado["creado"]:
        verificar_paciente(request, paciente["id"], credenciales)
    if bloque is not None and obtener_bloque(conexion, bloque) is not None:
        destino = f"/reservar/{bloque}?rut={normalizar_rut(paciente['rut'])}"
    else:
        destino = f"/pacientes/{paciente['id']}"
    respuesta = RedirectResponse(destino, status_code=303)
    if resultado["creado"]:
        return conceder_acceso_paciente(request, respuesta, paciente["id"])
    return respuesta


@router.get("/pacientes/{paciente_id}", response_class=HTMLResponse)
def mostrar_registro_confirmado(
    paciente_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    paciente = conexion.execute(
        "SELECT * FROM paciente WHERE id = ?", (paciente_id,)
    ).fetchone()
    if paciente is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    verificar_paciente(request, paciente_id, credenciales)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="registro_confirmado.html",
        context={"paciente": paciente},
        headers={"Cache-Control": "no-store"},
    )
