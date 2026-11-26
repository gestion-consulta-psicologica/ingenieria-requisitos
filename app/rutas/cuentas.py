from __future__ import annotations

import logging
import sqlite3
from hmac import compare_digest
from secrets import token_urlsafe

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from app.db.conexion import conectar
from app.rutas.disponibilidad import obtener_conexion
from app.servicios import cuentas

COOKIE_SESION = "__Host-consulta-sesion"
COOKIE_CSRF = "__Host-consulta-csrf"
logger = logging.getLogger(__name__)


def modo_operativo(request: Request) -> None:
    if not request.app.state.cuentas_persistentes:
        raise HTTPException(404)


router = APIRouter(prefix="/cuenta", dependencies=[Depends(modo_operativo)])


def _cargar_cuenta(ruta: str, token: str) -> dict | None:
    conexion = conectar(ruta)
    try:
        return cuentas.obtener_sesion(conexion, token)
    finally:
        conexion.close()


async def estado_sesion(request: Request, siguiente):
    request.state.cuenta = None
    if not request.app.state.cuentas_persistentes:
        request.state.csrf = request.app.state.csrf_psicologa_demo
        return await siguiente(request)
    if request.url.scheme != "https":
        return PlainTextResponse("El modo operativo requiere HTTPS.", status_code=400)
    token = request.cookies.get(COOKIE_SESION, "")
    if token:
        request.state.cuenta = await run_in_threadpool(
            _cargar_cuenta, request.app.state.ruta_db, token,
        )
    anonimo = request.cookies.get(COOKIE_CSRF, "")
    nuevo = not request.state.cuenta and len(anonimo) != 43
    if nuevo:
        anonimo = token_urlsafe(32)
    request.state.csrf = cuentas.huella("csrf:" + token) if request.state.cuenta else anonimo
    respuesta = await siguiente(request)
    if nuevo:
        respuesta.set_cookie(
            COOKIE_CSRF, anonimo, secure=True, httponly=True, samesite="strict", max_age=3600,
        )
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    return respuesta


async def verificar_csrf(request: Request) -> None:
    if request.app.state.cuentas_persistentes and request.method not in ("GET", "HEAD", "OPTIONS"):
        esperado = request.state.csrf
        actual = (await request.form()).get("csrf", "")
        if not isinstance(actual, str) or not esperado or not compare_digest(actual.encode(), esperado.encode()):
            raise HTTPException(403, detail="Formulario inválido o vencido.")


SIN_CORREO = (
    "El envío de correo no está configurado, así que no podemos enviarte el código. "
    "Contacta a la consulta para crear o recuperar tu cuenta."
)


def _correo_disponible(request) -> bool:
    return request.app.state.servicio_correo.configurado()


def _vista(request, pantalla, *, mensaje="", status=200, bloque_id=None):
    return request.app.state.templates.TemplateResponse(
        request=request, name="cuenta.html",
        context={
            "pantalla": pantalla, "mensaje": mensaje, "bloque_id": bloque_id,
            "sin_correo": (
                pantalla in ("registro", "verificar", "recuperar", "restablecer")
                and not _correo_disponible(request)
            ),
            "aviso_sin_correo": SIN_CORREO,
        },
        status_code=status,
    )


def _limitar(request, conexion, accion, correo="", *, maximo=8):
    ip = request.client.host if request.client else "desconocida"
    if not cuentas.permitir_intento(conexion, f"{accion}:ip:{ip}", maximo * 3, 900):
        raise HTTPException(429, detail="Demasiados intentos. Intenta más tarde.")
    if correo and not cuentas.permitir_intento(conexion, f"{accion}:correo:{correo}", maximo, 900):
        raise HTTPException(429, detail="Demasiados intentos. Intenta más tarde.")


def _enviar_codigo(servicio, ruta_db, base, cuenta_id, correo, proposito):
    if not servicio.configurado():
        return
    try:
        conexion = conectar(ruta_db)
        try:
            codigo = cuentas.crear_token(conexion, cuenta_id, proposito)
        finally:
            conexion.close()
        pagina = "verificar" if proposito == "verificar" else "restablecer"
        servicio.enviar(
            correo, "Código de acceso a la consulta",
            f"Abre {base}/cuenta/{pagina} e ingresa este código de un solo uso:\n\n{codigo}",
        )
    except Exception as error:
        logger.warning("No se pudo enviar el correo de cuenta (%s).", type(error).__name__)


def _programar_codigo(request, tareas, cuenta_id, correo, proposito):
    tareas.add_task(
        _enviar_codigo, request.app.state.servicio_correo, request.app.state.ruta_db,
        request.app.state.configuracion_correo.url_publica, cuenta_id, correo, proposito,
    )


@router.get("/ingresar", response_class=HTMLResponse)
def ingreso(request: Request, bloque_id: int | None = None):
    return _vista(request, "ingresar", bloque_id=bloque_id)


@router.post("/ingresar")
def ingresar(
    request: Request, correo: str = Form(), clave: str = Form(),
    bloque_id: str = Form(default=""), conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    correo = correo.strip().lower()[:254]
    destino_bloque = int(bloque_id) if bloque_id.isascii() and bloque_id.isdecimal() and len(bloque_id) <= 18 else None
    _limitar(request, conexion, "ingreso", correo)
    cuenta = conexion.execute("SELECT * FROM cuenta WHERE correo = ?", (correo,)).fetchone()
    coincide = cuentas.verificar_clave(clave, cuenta["clave_hash"] if cuenta else None)
    if not coincide:
        return _vista(request, "ingresar", mensaje="Correo o contraseña incorrectos.", status=401,
                      bloque_id=destino_bloque)
    if not cuentas.habilitada(cuenta):
        return _vista(request, "ingresar", mensaje="La cuenta aún requiere verificación de correo o identidad.",
                      status=403, bloque_id=destino_bloque)
    token = cuentas.crear_sesion(conexion, cuenta, request.cookies.get(COOKIE_SESION, ""))
    if token is None:
        return _vista(request, "ingresar", mensaje="Vuelve a ingresar.", status=401,
                      bloque_id=destino_bloque)
    bloque = destino_bloque or cuenta["bloque_preferido_id"]
    if cuenta["rol"] == "psicologa":
        destino = "/psicologa"
    else:
        destino = f"/reservar/{bloque}" if bloque else "/disponibilidad"
        if cuenta["bloque_preferido_id"]:
            with conexion:
                conexion.execute("UPDATE cuenta SET bloque_preferido_id = NULL WHERE id = ?", (cuenta["id"],))
    respuesta = RedirectResponse(destino, status_code=303)
    respuesta.set_cookie(
        COOKIE_SESION, token, secure=True, httponly=True, samesite="lax", max_age=cuentas.SEGUNDOS_SESION,
    )
    return respuesta


@router.post("/salir")
def salir(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    with conexion:
        cuentas.revocar_sesion(conexion, request.cookies.get(COOKIE_SESION, ""))
    respuesta = RedirectResponse("/disponibilidad", status_code=303)
    respuesta.delete_cookie(COOKIE_SESION, secure=True, httponly=True, samesite="lax")
    return respuesta


@router.get("/registro", response_class=HTMLResponse)
def formulario_registro(request: Request, bloque_id: int | None = None):
    return _vista(request, "registro", bloque_id=bloque_id)


@router.post("/registro")
def registrar(
    request: Request, tareas: BackgroundTasks, correo: str = Form(), clave: str = Form(), rut: str = Form(),
    nombre: str = Form(), telefono: str = Form(default=""), bloque_id: str = Form(default=""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    bloque = int(bloque_id) if bloque_id.isascii() and bloque_id.isdecimal() and len(bloque_id) <= 18 else None
    if not _correo_disponible(request):
        # Sin correo la cuenta nunca podría verificarse: no se crea.
        return _vista(request, "registro", mensaje=SIN_CORREO, status=503, bloque_id=bloque)
    try:
        correo = cuentas.normalizar_correo(correo)
        _limitar(request, conexion, "registro", correo, maximo=4)
        cuenta_id = cuentas.registrar_cuenta(conexion, correo, clave, rut, nombre, telefono, bloque)
    except cuentas.CuentaInvalida as error:
        return _vista(request, "registro", mensaje=str(error), status=400, bloque_id=bloque)
    if cuenta_id:
        _programar_codigo(request, tareas, cuenta_id, correo, "verificar")
    return _vista(request, "verificar", mensaje="Si procede, recibirás un código de verificación.")


@router.get("/verificar", response_class=HTMLResponse)
def formulario_verificacion(request: Request):
    return _vista(request, "verificar")


@router.post("/verificar")
def verificar(
    request: Request, codigo: str = Form(), conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    _limitar(request, conexion, "verificar")
    if not cuentas.consumir_token(conexion, codigo.strip(), "verificar"):
        return _vista(request, "verificar", mensaje="Código inválido o vencido.", status=400)
    return _vista(request, "ingresar", mensaje="Correo verificado. La psicóloga debe aprobar tu identidad.")


@router.get("/recuperar", response_class=HTMLResponse)
def formulario_recuperar(request: Request):
    return _vista(request, "recuperar")


@router.post("/recuperar")
def recuperar(
    request: Request, tareas: BackgroundTasks, correo: str = Form(), proposito: str = Form(default="restablecer"),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    correo = correo.strip().lower()[:254]
    if proposito not in ("verificar", "restablecer"):
        raise HTTPException(400)
    if not _correo_disponible(request):
        pantalla = "verificar" if proposito == "verificar" else "recuperar"
        return _vista(request, pantalla, mensaje=SIN_CORREO, status=503)
    _limitar(request, conexion, "codigo", correo, maximo=4)
    cuenta = conexion.execute("SELECT * FROM cuenta WHERE correo = ?", (correo,)).fetchone()
    if cuenta and ((cuenta["correo_verificado_en"] is None) == (proposito == "verificar")):
        _programar_codigo(request, tareas, cuenta["id"], correo, proposito)
    pantalla = "verificar" if proposito == "verificar" else "restablecer"
    return _vista(request, pantalla, mensaje="Si procede, recibirás un código por correo.")


@router.get("/restablecer", response_class=HTMLResponse)
def formulario_restablecer(request: Request):
    return _vista(request, "restablecer")


@router.post("/restablecer")
def restablecer(
    request: Request, codigo: str = Form(), clave: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    _limitar(request, conexion, "restablecer")
    try:
        if not cuentas.consumir_token(conexion, codigo.strip(), "restablecer", clave):
            return _vista(request, "restablecer", mensaje="Código inválido o vencido.", status=400)
    except cuentas.CuentaInvalida as error:
        return _vista(request, "restablecer", mensaje=str(error), status=400)
    return _vista(request, "ingresar", mensaje="Contraseña actualizada. Las sesiones anteriores fueron cerradas.")


@router.get("/reservas", response_class=HTMLResponse)
def mis_reservas(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    cuenta = request.state.cuenta
    if not cuenta:
        return RedirectResponse("/cuenta/ingresar", status_code=303)
    if cuenta["rol"] != "paciente":
        raise HTTPException(403)
    reservas = conexion.execute(
        """
        SELECT r.id, r.estado, b.fecha, b.hora_inicio
        FROM reserva r JOIN bloque_horario b ON b.id = r.bloque_horario_id
        WHERE r.paciente_id = ? ORDER BY b.fecha DESC, b.hora_inicio DESC
        """, (cuenta["paciente_id"],),
    ).fetchall()
    return request.app.state.templates.TemplateResponse(
        request=request, name="mis_reservas.html", context={"reservas": reservas},
    )
