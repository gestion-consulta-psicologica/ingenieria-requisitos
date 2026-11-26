from __future__ import annotations

import sqlite3
from datetime import date, datetime, time
from secrets import compare_digest

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.rutas.disponibilidad import obtener_conexion
from app.rutas.acceso_reserva import es_psicologa
from app.servicios.atenciones import (
    AsistenciaInvalida,
    AtencionNoEncontrada,
    registrar_asistencia,
)
from app.servicios.disponibilidad import (
    DURACION_ATENCION,
    crear_bloques_por_hora,
    horario_dentro_de_jornada,
    insertar_bloque_libre,
)
from app.servicios.cuentas import CuentaInvalida, aceptar_identidad
from app.servicios.reagendamiento import (
    EstadoReservaInvalido,
    ReservaNoEncontrada,
    cancelar_reserva,
)
from app.tiempo import ahora_utc, programado

router = APIRouter(prefix="/psicologa")
autenticacion = HTTPBasic(auto_error=False)


def autenticar_psicologa(
    request: Request,
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
) -> None:
    if request.app.state.cuentas_persistentes:
        if not es_psicologa(request, credenciales):
            raise HTTPException(status_code=403 if request.state.cuenta else 401)
        return
    clave = request.app.state.clave_psicologa_demo
    if clave is None:
        raise HTTPException(status_code=404)
    if not es_psicologa(request, credenciales):
        raise HTTPException(
            status_code=401, headers={"WWW-Authenticate": 'Basic realm="Psicologa"'},
        )


@router.get("", response_class=HTMLResponse, dependencies=[Depends(autenticar_psicologa)])
def panel(
    request: Request,
    asistencia_registrada: int | None = None,
    bloques_generados: int | None = None,
    semana_generada: date | None = None,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    psicologa_id = request.state.cuenta["psicologa_id"] if request.state.cuenta else 1
    solicitudes = conexion.execute(
        """
        SELECT id, correo, rut_solicitado, nombre_solicitado FROM cuenta
        WHERE rol = 'paciente' AND paciente_id IS NULL AND correo_verificado_en IS NOT NULL
        ORDER BY id
        """
    ).fetchall() if request.app.state.cuentas_persistentes else []
    bloques = conexion.execute(
        """
        SELECT fecha, hora_inicio, hora_termino, modalidad
        FROM bloque_horario
        WHERE psicologa_id = ?
        ORDER BY fecha DESC, hora_inicio DESC
        """, (psicologa_id,),
    ).fetchall()
    reservas = conexion.execute(
        """
        SELECT r.id, r.estado, p.id AS paciente_id, p.nombre_completo, b.fecha, b.hora_inicio,
               a.id AS atencion_id, a.estado AS atencion_estado
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        LEFT JOIN atencion a ON a.reserva_id = r.id
        WHERE b.psicologa_id = ?
        ORDER BY b.fecha DESC, b.hora_inicio DESC, r.id DESC
        """, (psicologa_id,),
    ).fetchall()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="psicologa.html",
        context={
            "bloques": bloques, "reservas": reservas,
            "asistencia_registrada": asistencia_registrada,
            "bloques_generados": bloques_generados,
            "semana_generada": semana_generada,
            "solicitudes_identidad": solicitudes,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/horarios", dependencies=[Depends(autenticar_psicologa)])
def crear_horario(
    request: Request,
    fecha: date = Form(),
    inicio: time = Form(),
    termino: time = Form(),
    modalidad: str = Form(),
    csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    if any(hora.tzinfo or hora.second or hora.microsecond for hora in (inicio, termino)):
        raise HTTPException(status_code=400, detail="Ingresa inicio y término en horas y minutos.")
    if not horario_dentro_de_jornada(fecha, inicio, termino):
        raise HTTPException(
            status_code=400, detail="El bloque debe quedar entre las 09:00 y las 19:00 de lunes a sábado.",
        )
    if modalidad not in ("presencial", "online"):
        raise HTTPException(status_code=400, detail="Modalidad inválida.")
    inicio_bloque = datetime.combine(fecha, inicio)
    termino_bloque = datetime.combine(fecha, termino)
    if termino_bloque - inicio_bloque != DURACION_ATENCION:
        raise HTTPException(status_code=400, detail="El bloque debe durar 50 minutos.")
    zona = request.app.state.configuracion_correo.zona_horaria
    hora_inicio = inicio.isoformat(timespec="minutes")
    if programado(fecha, hora_inicio, zona) <= ahora_utc():
        raise HTTPException(status_code=400, detail="El bloque debe comenzar en el futuro.")
    with conexion:
        psicologa_id = request.state.cuenta["psicologa_id"] if request.state.cuenta else 1
        creado = insertar_bloque_libre(conexion, psicologa_id, inicio_bloque, termino_bloque, modalidad)
    if not creado:
        raise HTTPException(status_code=409, detail="El horario se superpone con un bloque existente.")
    return RedirectResponse("/psicologa", status_code=303)


@router.post("/horarios/generar", dependencies=[Depends(autenticar_psicologa)])
def generar_horarios(
    request: Request,
    semana: date = Form(),
    modalidad: str = Form(),
    csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    if modalidad not in ("presencial", "online"):
        raise HTTPException(status_code=400, detail="Modalidad inválida.")
    with conexion:
        psicologa_id = request.state.cuenta["psicologa_id"] if request.state.cuenta else 1
        cantidad = crear_bloques_por_hora(
            conexion, psicologa_id, semana, modalidad, ahora_utc(),
            request.app.state.configuracion_correo.zona_horaria,
        )
    return RedirectResponse(
        f"/psicologa?bloques_generados={cantidad}&semana_generada={semana.isoformat()}#disponibilidad",
        status_code=303,
    )


def verificar_formulario_psicologa(request: Request, csrf: str) -> None:
    if not compare_digest(csrf.encode(), request.state.csrf.encode()):
        raise HTTPException(status_code=403, detail="Formulario de administración inválido.")


@router.post("/identidades/{cuenta_id}/aprobar", dependencies=[Depends(autenticar_psicologa)])
def aprobar_identidad(
    cuenta_id: int, request: Request, csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if not request.app.state.cuentas_persistentes:
        raise HTTPException(404)
    verificar_formulario_psicologa(request, csrf)
    try:
        aceptar_identidad(conexion, cuenta_id, request.state.cuenta["id"])
    except CuentaInvalida as error:
        raise HTTPException(409, detail=str(error)) from error
    return RedirectResponse("/psicologa#identidades", status_code=303)


@router.post("/reservas/{reserva_id}/cancelar", dependencies=[Depends(autenticar_psicologa)])
def cancelar_reserva_confirmada(
    reserva_id: int,
    request: Request,
    csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    try:
        cancelar_reserva(
            conexion, reserva_id,
            configuracion=request.app.state.configuracion_correo, por_psicologa=True,
        )
    except ReservaNoEncontrada as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except EstadoReservaInvalido as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return RedirectResponse("/psicologa", status_code=303)


@router.post("/atenciones/{atencion_id}/asistencia", dependencies=[Depends(autenticar_psicologa)])
def guardar_asistencia(
    atencion_id: int,
    request: Request,
    estado: str = Form(),
    justificacion: str = Form(default=""),
    csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    try:
        registrar_asistencia(
            conexion, atencion_id, estado, justificacion,
            cifrador=request.app.state.cifrador,
        )
    except AtencionNoEncontrada as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AsistenciaInvalida as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return RedirectResponse(
        f"/psicologa?asistencia_registrada={atencion_id}#atencion-{atencion_id}",
        status_code=303,
    )
