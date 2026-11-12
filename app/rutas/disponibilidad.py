from __future__ import annotations

import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.db.conexion import conectar
from app.servicios.disponibilidad import (
    obtener_disponibilidad_semana,
    obtener_proximo_bloque,
    rango_semana,
)

router = APIRouter()


def obtener_conexion(request: Request):
    conexion = conectar(request.app.state.ruta_db)
    try:
        yield conexion
    finally:
        conexion.close()


@router.get("/disponibilidad", response_class=HTMLResponse)
def consultar_disponibilidad(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    semana: str | None = Query(
        default=None,
        description="Fecha de la semana en formato AAAA-MM-DD",
    ),
):
    if semana:
        try:
            fecha_semana = date.fromisoformat(semana)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha inválido. Use AAAA-MM-DD.",
            ) from error
    else:
        fecha_semana = date.today()

    inicio, fin = rango_semana(fecha_semana)
    bloques = obtener_disponibilidad_semana(conexion, fecha_semana)
    proximo_bloque = None
    if not bloques:
        proximo_bloque = obtener_proximo_bloque(conexion, fecha_semana)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="disponibilidad.html",
        context={
            "semana_inicio": inicio,
            "semana_fin": fin,
            "bloques": bloques,
            "proximo_bloque": proximo_bloque,
            "sin_disponibilidad": not bloques,
        },
    )
