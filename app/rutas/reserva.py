from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasicCredentials

from app.db.conexion import conectar
from app.rutas.acceso_reserva import conceder_acceso_reserva, es_psicologa, verificar_paciente, verificar_titular
from app.rutas.psicologa import autenticacion
from app.servicios import cola_correo, tokens
from app.servicios.atenciones import obtener_atencion_de_reserva
from app.servicios.confirmacion import (
    ESTADO_SOLICITUD_PENDIENTE,
    RESPUESTA_CONFIRMA,
    RESPUESTA_NO_ASISTIRA,
    EstadoReservaInvalido,
    ReservaNoEncontrada,
    SolicitudPendienteNoDisponible,
    registrar_respuesta,
    registrar_respuesta_con_token,
)
from app.servicios.disponibilidad import obtener_bloques_cercanos
from app.servicios.reagendamiento import (
    BloqueNoDisponible as BloqueNoDisponibleReagenda,
    BloqueNoEncontrado as BloqueNoEncontradoReagenda,
    EstadoReservaInvalido as EstadoReservaNoGestionable,
    ReservaNoEncontrada as ReservaNoGestionable,
    cancelar_reserva,
    listar_historial,
    obtener_alternativas,
    reagendar_reserva,
    reserva_tiene_atencion,
)
from app.servicios.reserva import (
    ESTADO_PENDIENTE,
    BloqueNoDisponible,
    BloqueNoEncontrado,
    PacienteNoRegistrado,
    obtener_bloque,
    obtener_reserva,
    registrar_reserva,
)
from app.tiempo import ahora_utc, programado

router = APIRouter()


def obtener_conexion(request: Request):
    conexion = conectar(request.app.state.ruta_db)
    try:
        yield conexion
    finally:
        conexion.close()


def verificar_acceso_reserva(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
) -> None:
    if request.method == "GET" and es_psicologa(request, credenciales):
        request.state.lectura_admin = True
        return
    titular = conexion.execute(
        "SELECT paciente_id FROM reserva WHERE id = ?", (reserva_id,),
    ).fetchone()
    if titular is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    verificar_titular(request, reserva_id, titular["paciente_id"], credenciales)


def _render_formulario(
    request: Request,
    bloque,
    *,
    error: str | None = None,
    cercanos: list[dict] | None = None,
    rut: str = "",
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="reserva.html",
        context={
            "bloque": bloque,
            "error": error,
            "cercanos": cercanos or [],
            "rut": rut,
        },
        status_code=status_code,
    )


def _programado_texto(fecha: str, hora: str, request: Request) -> str:
    configuracion = request.app.state.configuracion_correo
    valor = programado(fecha, hora, configuracion.zona_horaria)
    local = valor.astimezone(ZoneInfo(configuracion.zona_horaria))
    return (
        f"{local.strftime('%Y-%m-%d %H:%M')} "
        f"({configuracion.zona_horaria})"
    )


def _obtener_detalle(
    request: Request, conexion: sqlite3.Connection, reserva_id: int
) -> dict:
    reserva = obtener_reserva(conexion, reserva_id)
    if reserva is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    solicitudes = [
        dict(fila)
        for fila in conexion.execute(
            """
            SELECT id, version, tipo, fecha_envio, estado, respuesta,
                   fecha_respuesta, fecha_cierre
            FROM solicitud_confirmacion
            WHERE reserva_id = ?
            ORDER BY version, fecha_envio, id
            """,
            (reserva_id,),
        )
    ]
    cargo = conexion.execute(
        "SELECT * FROM cargo WHERE reserva_id = ?", (reserva_id,)
    ).fetchone()
    correos = [dict(fila) for fila in cola_correo.listar_por_reserva(
        conexion, reserva_id
    )]
    for solicitud in solicitudes:
        solicitud["correos"] = [
            correo for correo in correos if correo["solicitud_id"] == solicitud["id"]
        ]
    pendiente = reserva["estado"] == ESTADO_PENDIENTE
    solicitud_pendiente = next(
        (
            solicitud
            for solicitud in reversed(solicitudes)
            if solicitud["estado"] == ESTADO_SOLICITUD_PENDIENTE
            and solicitud["version"] == reserva["version"]
        ),
        None,
    )
    fecha_bloque = reserva["fecha"]
    vispera = (date.fromisoformat(fecha_bloque) - timedelta(days=1)).isoformat()
    configuracion = request.app.state.configuracion_correo
    inicio = programado(fecha_bloque, reserva["hora_inicio"], configuracion.zona_horaria)

    return {
        "reserva": reserva,
        "solicitudes": solicitudes,
        "cargo": cargo,
        "cargo_monto": (
            f"{cargo['monto']:,}".replace(",", ".") if cargo is not None else None
        ),
        "solicitud_pendiente": solicitud_pendiente,
        "puede_responder": (
            pendiente and solicitud_pendiente is not None and ahora_utc() < inicio
            and cola_correo.solicitud_enviada(conexion, solicitud_pendiente["id"])
        ),
        "puede_gestionar": (
            reserva["estado"] == "Confirmada"
            and not reserva_tiene_atencion(conexion, reserva_id)
        ),
        "atencion_pago": obtener_atencion_de_reserva(conexion, reserva_id),
        "historial": listar_historial(conexion, reserva_id),
        "correos": correos,
        "correos_reserva": correos,
        "correo_configurado": request.app.state.correo_configurado,
        "correo_motivo": request.app.state.correo_motivo,
        "zona_horaria": configuracion.zona_horaria,
        "vispera_programada": _programado_texto(
            vispera, configuracion.hora_vispera, request
        ),
        "recordatorio_programado": _programado_texto(
            fecha_bloque, configuracion.hora_recordatorio, request
        ),
        "atencion_programada": _programado_texto(
            fecha_bloque, reserva["hora_inicio"], request
        ),
    }


def _render_detalle(
    request: Request,
    conexion: sqlite3.Connection,
    reserva_id: int,
    *,
    error: str | None = None,
    status_code: int = 200,
):
    if obtener_reserva(conexion, reserva_id) is None:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="reserva_confirmada.html",
            context={
                "reserva": None,
                "error": error or "Reserva no encontrada.",
            },
            status_code=404,
        )

    contexto = _obtener_detalle(request, conexion, reserva_id)
    contexto["error"] = error
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="reserva_confirmada.html",
        context=contexto,
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _render_respuesta_token(
    request: Request,
    conexion: sqlite3.Connection,
    token: str,
    accion: str,
    *,
    error: str | None = None,
    status_code: int = 200,
):
    try:
        fila = tokens.buscar_token(conexion, token, ahora_utc())
    except tokens.TokenInvalido as exc:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="respuesta_token.html",
            context={"accion": accion, "error": str(exc), "reserva": None},
            status_code=404,
        )
    except (tokens.TokenUsado, tokens.TokenVencido, tokens.TokenSolicitudInvalida) as exc:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="respuesta_token.html",
            context={"accion": accion, "error": str(exc), "reserva": None},
            status_code=409,
        )

    if fila["accion"] != accion:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="respuesta_token.html",
            context={
                "accion": None,
                "error": "El enlace no corresponde a esta acción.",
                "reserva": None,
            },
            status_code=409,
        )

    reserva = obtener_reserva(conexion, fila["reserva_id"])
    respuesta = request.app.state.templates.TemplateResponse(
        request=request,
        name="respuesta_token.html",
        context={
            "accion": accion,
            "token": token,
            "error": error,
            "reserva": reserva,
        },
        status_code=status_code,
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@router.get("/reservar/{bloque_id}", response_class=HTMLResponse)
def mostrar_formulario(
    bloque_id: int,
    request: Request,
    rut: str = "",
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    bloque = obtener_bloque(conexion, bloque_id)
    if bloque is None:
        raise HTTPException(status_code=404, detail="Bloque horario no encontrado")
    if request.app.state.cuentas_persistentes and request.state.cuenta:
        paciente_id = request.state.cuenta["paciente_id"]
        if paciente_id:
            rut = conexion.execute("SELECT rut FROM paciente WHERE id = ?", (paciente_id,)).fetchone()["rut"]
    return _render_formulario(request, bloque, rut=rut)


@router.post("/reservar/{bloque_id}", response_class=HTMLResponse)
def reservar(
    bloque_id: int,
    request: Request,
    rut: str = Form(default=""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    if request.app.state.cuentas_persistentes and not request.state.cuenta:
        return RedirectResponse(f"/cuenta/ingresar?bloque_id={bloque_id}", status_code=303)
    configuracion = request.app.state.configuracion_correo
    try:
        resultado = registrar_reserva(
            conexion, bloque_id, rut, configuracion=configuracion,
            autorizar_paciente=lambda paciente_id: verificar_paciente(request, paciente_id, credenciales),
        )
    except PacienteNoRegistrado:
        return RedirectResponse(
            url=f"/pacientes/registro?bloque_id={bloque_id}", status_code=303
        )
    except BloqueNoEncontrado as error:
        raise HTTPException(
            status_code=404, detail="Bloque horario no encontrado"
        ) from error
    except BloqueNoDisponible:
        bloque = obtener_bloque(conexion, bloque_id)
        if bloque is None:
            raise HTTPException(
                status_code=404, detail="Bloque horario no encontrado"
            )
        cercanos = obtener_bloques_cercanos(
            conexion, date.fromisoformat(bloque["fecha"]),
            zona_horaria=configuracion.zona_horaria,
        )
        return _render_formulario(
            request,
            bloque,
            error="El bloque ya no está disponible.",
            cercanos=cercanos,
            rut=rut,
            status_code=409,
        )

    reserva_id = resultado["reserva"]["id"]
    return conceder_acceso_reserva(
        request, RedirectResponse(f"/reservas/{reserva_id}", status_code=303), reserva_id,
    )


@router.get("/reservas/{reserva_id}", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def mostrar_reserva(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _render_detalle(request, conexion, reserva_id)


@router.post("/reservas/{reserva_id}/confirmar", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def confirmar_asistencia(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        registrar_respuesta(
            conexion, reserva_id, RESPUESTA_CONFIRMA, ahora=ahora_utc(),
            configuracion=request.app.state.configuracion_correo,
        )
    except ReservaNoEncontrada:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error="Reserva no encontrada.",
            status_code=404,
        )
    except (EstadoReservaInvalido, SolicitudPendienteNoDisponible) as error:
        return _render_detalle(
            request, conexion, reserva_id, error=str(error), status_code=409
        )
    return RedirectResponse(url=f"/reservas/{reserva_id}", status_code=303)


@router.post("/reservas/{reserva_id}/no-asistir", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def responder_no_asistira(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        registrar_respuesta(
            conexion, reserva_id, RESPUESTA_NO_ASISTIRA,
            ahora=ahora_utc(),
            configuracion=request.app.state.configuracion_correo,
        )
    except ReservaNoEncontrada:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error="Reserva no encontrada.",
            status_code=404,
        )
    except (EstadoReservaInvalido, SolicitudPendienteNoDisponible) as error:
        return _render_detalle(
            request, conexion, reserva_id, error=str(error), status_code=409
        )
    return RedirectResponse(url=f"/reservas/{reserva_id}", status_code=303)


@router.post("/reservas/{reserva_id}/cancelar", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def cancelar_gestion(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        cancelar_reserva(
            conexion, reserva_id,
            configuracion=request.app.state.configuracion_correo,
        )
    except ReservaNoGestionable:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error="Reserva no encontrada.",
            status_code=404,
        )
    except EstadoReservaNoGestionable as error:
        return _render_detalle(
            request, conexion, reserva_id, error=str(error), status_code=409
        )
    return RedirectResponse(url=f"/reservas/{reserva_id}", status_code=303)


def _render_alternativas(
    request: Request,
    conexion: sqlite3.Connection,
    reserva_id: int,
    *,
    alternativas: list[dict] | None = None,
    error: str | None = None,
    status_code: int = 200,
):
    try:
        detalle = _obtener_detalle(request, conexion, reserva_id)
    except HTTPException:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error="Reserva no encontrada.",
            status_code=404,
        )
    if not detalle["puede_gestionar"]:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error=error or "Solo se puede reagendar una reserva confirmada sin atención asociada.",
            status_code=409,
        )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="reagendar.html",
        context={
            **detalle,
            "alternativas": alternativas
            if alternativas is not None
            else obtener_alternativas(
                conexion, reserva_id,
                zona_horaria=request.app.state.configuracion_correo.zona_horaria,
            ),
            "error": error,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/reservas/{reserva_id}/reagendar", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def mostrar_reagendamiento(
    reserva_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _render_alternativas(request, conexion, reserva_id)


@router.post("/reservas/{reserva_id}/reagendar", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso_reserva)])
def ejecutar_reagendamiento(
    reserva_id: int,
    request: Request,
    bloque_id: int = Form(...),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    try:
        reagendar_reserva(
            conexion,
            reserva_id,
            bloque_id,
            configuracion=request.app.state.configuracion_correo,
        )
    except ReservaNoGestionable:
        return _render_detalle(
            request,
            conexion,
            reserva_id,
            error="Reserva no encontrada.",
            status_code=404,
        )
    except BloqueNoEncontradoReagenda:
        return _render_alternativas(
            request,
            conexion,
            reserva_id,
            error="El bloque seleccionado no existe. Elige otra alternativa.",
            status_code=404,
        )
    except (BloqueNoDisponibleReagenda, EstadoReservaNoGestionable) as error:
        return _render_alternativas(
            request,
            conexion,
            reserva_id,
            error=str(error),
            status_code=409,
        )
    return RedirectResponse(url=f"/reservas/{reserva_id}", status_code=303)


@router.get("/respuesta/confirmar/{token}", response_class=HTMLResponse)
def mostrar_confirmacion_token(
    token: str,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _render_respuesta_token(
        request, conexion, token, tokens.ACCION_CONFIRMAR
    )


@router.post("/respuesta/confirmar/{token}", response_class=HTMLResponse)
def confirmar_con_token(
    token: str,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _ejecutar_respuesta_token(
        request, conexion, token, RESPUESTA_CONFIRMA
    )


@router.get("/respuesta/cancelar/{token}", response_class=HTMLResponse)
def mostrar_cancelacion_token(
    token: str,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _render_respuesta_token(
        request, conexion, token, tokens.ACCION_CANCELAR
    )


@router.post("/respuesta/cancelar/{token}", response_class=HTMLResponse)
def cancelar_con_token(
    token: str,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    return _ejecutar_respuesta_token(
        request, conexion, token, RESPUESTA_NO_ASISTIRA
    )


def _ejecutar_respuesta_token(
    request: Request,
    conexion: sqlite3.Connection,
    token: str,
    respuesta: str,
):
    try:
        resultado = registrar_respuesta_con_token(
            conexion, token, respuesta,
            ahora=ahora_utc(),
            configuracion=request.app.state.configuracion_correo,
        )
    except tokens.TokenInvalido as error:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="respuesta_token.html",
            context={"accion": None, "error": str(error), "reserva": None},
            status_code=404,
        )
    except (
        tokens.TokenUsado,
        tokens.TokenVencido,
        tokens.TokenAccionInvalida,
        tokens.TokenSolicitudInvalida,
        EstadoReservaInvalido,
        SolicitudPendienteNoDisponible,
    ) as error:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="respuesta_token.html",
            context={"accion": None, "error": str(error), "reserva": None},
            status_code=409,
        )
    reserva_id = resultado["reserva"]["id"]
    if request.app.state.cuentas_persistentes:
        return request.app.state.templates.TemplateResponse(
            request=request, name="respuesta_token.html",
            context={
                "resultado": "La asistencia quedó confirmada."
                if respuesta == RESPUESTA_CONFIRMA else "La reserva quedó cancelada.",
                "error": None, "reserva": None,
            },
        )
    return conceder_acceso_reserva(
        request, RedirectResponse(f"/reservas/{reserva_id}", status_code=303), reserva_id,
    )
