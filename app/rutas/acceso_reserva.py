from hmac import compare_digest, digest

from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBasicCredentials


def _firma(request: Request, nombre: str) -> str:
    return digest(
        request.app.state.clave_acceso_reserva, nombre.encode(), "sha256",
    ).hex()


def _conceder_acceso(request: Request, respuesta: Response, nombre: str) -> Response:
    if request.app.state.cuentas_persistentes:
        return respuesta
    respuesta.set_cookie(
        nombre, _firma(request, nombre),
        httponly=True, samesite="strict", secure=request.url.scheme == "https",
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


def conceder_acceso_reserva(request: Request, respuesta: Response, reserva_id: int) -> Response:
    return _conceder_acceso(request, respuesta, f"reserva_{reserva_id}")


def conceder_acceso_paciente(request: Request, respuesta: Response, paciente_id: int) -> Response:
    return _conceder_acceso(request, respuesta, f"paciente_{paciente_id}")


def _tiene_permiso(request: Request, nombre: str) -> bool:
    return compare_digest(request.cookies.get(nombre, "").encode(), _firma(request, nombre).encode())


def es_psicologa(request: Request, credenciales: HTTPBasicCredentials | None) -> bool:
    if request.app.state.cuentas_persistentes:
        return bool(request.state.cuenta and request.state.cuenta["rol"] == "psicologa")
    clave = request.app.state.clave_psicologa_demo
    return bool(clave and credenciales and credenciales.username == "psicologa"
                and compare_digest(credenciales.password.encode(), clave.encode()))


def _es_paciente(request: Request, paciente_id: int, credenciales: HTTPBasicCredentials | None) -> bool:
    if request.app.state.cuentas_persistentes:
        cuenta = request.state.cuenta
        return bool(cuenta and cuenta["rol"] == "paciente" and cuenta["paciente_id"] == paciente_id)
    if _tiene_permiso(request, f"paciente_{paciente_id}"):
        return True
    clave = request.app.state.clave_paciente_demo
    return bool(paciente_id == 1 and clave and credenciales and credenciales.username == "paciente"
                and compare_digest(credenciales.password.encode(), clave.encode()))


def verificar_paciente(request: Request, paciente_id: int, credenciales: HTTPBasicCredentials | None) -> None:
    if not _es_paciente(request, paciente_id, credenciales):
        if request.app.state.cuentas_persistentes:
            raise HTTPException(
                status_code=403 if request.state.cuenta else 401,
                detail="Se requiere acceso del paciente.",
            )
        raise HTTPException(
            status_code=401, detail="Se requiere acceso del paciente.",
            headers={"WWW-Authenticate": 'Basic realm="Paciente"'},
        )


def verificar_titular(
    request: Request, reserva_id: int, paciente_id: int,
    credenciales: HTTPBasicCredentials | None,
) -> None:
    if _es_paciente(request, paciente_id, credenciales) or (
        not request.app.state.cuentas_persistentes and _tiene_permiso(request, f"reserva_{reserva_id}")
    ):
        return
    raise HTTPException(status_code=403, detail="No tienes acceso a esta reserva.")
