from fastapi import Request, Response
from fastapi.testclient import TestClient

from app.rutas.acceso_reserva import conceder_acceso_reserva


def cliente_con_reservas(app, *ids: int) -> TestClient:
    cliente = TestClient(app)
    solicitud = Request({"type": "http", "scheme": "http", "path": "/", "headers": [], "app": app})
    for reserva_id in ids:
        respuesta = conceder_acceso_reserva(solicitud, Response(), reserva_id)
        nombre, valor = respuesta.headers["set-cookie"].split(";", 1)[0].split("=", 1)
        cliente.cookies.set(nombre, valor)
    return cliente


def cliente_con_reserva_de_prueba(app) -> TestClient:
    return cliente_con_reservas(app, 1)
