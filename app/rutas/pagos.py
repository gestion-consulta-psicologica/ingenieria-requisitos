from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db.conexion import conectar
from app.servicios.atenciones import (
    ESTADO_PAGO_PAGADO,
    AtencionNoEncontrada,
    DatosComprobanteInvalidos,
    EstadoPagoNoPermiteRegistro,
    PagoNoEncontrado,
    PagoYaPagado,
    permite_registrar_comprobante,
    registrar_comprobante,
)
from app.servicios.pagos import (
    listar_atenciones_con_pago_pendiente,
    obtener_pago_de_atencion,
)

router = APIRouter()


def obtener_conexion(request: Request):
    conexion = conectar(request.app.state.ruta_db)
    try:
        yield conexion
    finally:
        conexion.close()


@router.get("/pagos", response_class=HTMLResponse)
def listar_pagos(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    atenciones = listar_atenciones_con_pago_pendiente(conexion)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pagos.html",
        context={"atenciones": atenciones},
    )


@router.get("/pagos/{atencion_id}", response_class=HTMLResponse)
def consultar_pago(
    atencion_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    detalle = obtener_pago_de_atencion(conexion, atencion_id)
    if detalle is None:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="pago_detalle.html",
            context={
                "detalle": None,
                "error": (
                    "No se encontró la atención o no tiene un pago asociado."
                ),
            },
            status_code=404,
        )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pago_detalle.html",
        context={"detalle": detalle},
    )


def _valores_comprobante(detalle: dict | None, valores: dict | None = None) -> dict:
    if valores is not None:
        return valores
    return {
        "monto": (
            detalle["pago"]["monto_atencion"] if detalle else ""
        ),
        "fecha_transferencia": "",
        "cuenta_destino": "",
    }


def _render_comprobante(
    request: Request,
    detalle: dict | None,
    *,
    error: str | None = None,
    errores: dict[str, str] | None = None,
    valores: dict | None = None,
    registrado: bool = False,
    status_code: int = 200,
):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pago_comprobante.html",
        context={
            "detalle": detalle,
            "error": error,
            "errores": errores or {},
            "valores": _valores_comprobante(detalle, valores),
            "registrado": registrado,
            "formulario_habilitado": (
                detalle is not None
                and permite_registrar_comprobante(detalle["pago"]["estado"])
            ),
        },
        status_code=status_code,
    )


def _error_estado_pago(estado: str) -> str:
    if estado == ESTADO_PAGO_PAGADO:
        return "El pago ya está pagado; no se puede registrar otro comprobante."
    return "El estado actual del pago no permite registrar comprobantes."


@router.get("/pagos/{atencion_id}/comprobante", response_class=HTMLResponse)
def mostrar_comprobante(
    atencion_id: int,
    request: Request,
    registrado: bool = False,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    detalle = obtener_pago_de_atencion(conexion, atencion_id)
    if detalle is None:
        return _render_comprobante(
            request,
            None,
            error="No se encontró la atención o no tiene un pago asociado.",
            status_code=404,
        )
    if not permite_registrar_comprobante(detalle["pago"]["estado"]):
        return _render_comprobante(
            request,
            detalle,
            error=_error_estado_pago(detalle["pago"]["estado"]),
            status_code=409,
        )
    return _render_comprobante(
        request, detalle, registrado=registrado
    )


@router.post("/pagos/{atencion_id}/comprobante", response_class=HTMLResponse)
def registrar_comprobante_de_pago(
    atencion_id: int,
    request: Request,
    monto: str = Form(""),
    fecha_transferencia: str = Form(""),
    cuenta_destino: str = Form(""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    detalle = obtener_pago_de_atencion(conexion, atencion_id)
    valores = {
        "monto": monto,
        "fecha_transferencia": fecha_transferencia,
        "cuenta_destino": cuenta_destino,
    }
    if detalle is None:
        return _render_comprobante(
            request,
            None,
            error="No se encontró la atención o no tiene un pago asociado.",
            valores=valores,
            status_code=404,
        )

    try:
        registrar_comprobante(
            conexion,
            atencion_id,
            monto,
            fecha_transferencia,
            cuenta_destino,
        )
    except DatosComprobanteInvalidos as error:
        return _render_comprobante(
            request,
            detalle,
            error=error.mensaje,
            errores=error.errores,
            valores=valores,
            status_code=400,
        )
    except (AtencionNoEncontrada, PagoNoEncontrado) as error:
        return _render_comprobante(
            request,
            detalle,
            error=str(error),
            valores=valores,
            status_code=404,
        )
    except (PagoYaPagado, EstadoPagoNoPermiteRegistro) as error:
        return _render_comprobante(
            request,
            detalle,
            error=str(error),
            valores=valores,
            status_code=409,
        )

    return RedirectResponse(
        url=f"/pagos/{atencion_id}/comprobante?registrado=1",
        status_code=303,
    )
