import sqlite3
import time

from app.db import derivaciones
from app.servicios.cuentas import CuentaInvalida, hash_clave, normalizar_correo


class SolicitudNoEncontrada(ValueError):
    pass


class DerivacionNoEncontrada(ValueError):
    pass


class DerivacionInvalida(ValueError):
    pass


def registrar_psiquiatra(conexion: sqlite3.Connection, nombre: str, correo: str, clave: str):
    nombre = nombre.strip()
    if not 1 <= len(nombre) <= 200:
        raise CuentaInvalida("Ingresa un nombre de hasta 200 caracteres.")
    correo = normalizar_correo(correo)
    guardada = hash_clave(clave)
    ahora = int(time.time())
    with conexion:
        resultado = conexion.execute(
            """
            INSERT INTO cuenta (
                correo, clave_hash, rol, nombre_psiquiatra,
                correo_verificado_en, identidad_verificada_en
            )
            VALUES (?, ?, 'psiquiatra', ?, ?, ?)
            ON CONFLICT (correo) DO NOTHING
            """,
            (correo, guardada, nombre, ahora, ahora),
        )
        if not resultado.rowcount:
            raise CuentaInvalida("El correo ya está registrado.")
    return resultado.lastrowid


def cambiar_disponibilidad(conexion: sqlite3.Connection, cuenta_id: int, activo: bool):
    with conexion:
        resultado = conexion.execute(
            "UPDATE cuenta SET activo = ? WHERE id = ? AND rol = 'psiquiatra'", (activo, cuenta_id),
        )
        if not resultado.rowcount:
            raise CuentaInvalida("Psiquiatra no encontrado.")
        if not activo:
            conexion.execute("DELETE FROM sesion WHERE cuenta_id = ?", (cuenta_id,))


def crear_derivacion(conexion: sqlite3.Connection, reserva_id: int, emisora_id: int, receptor_id: int):
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        reserva = derivaciones.solicitud(conexion, reserva_id, emisora_id)
        if reserva is None:
            raise SolicitudNoEncontrada("Solicitud de consulta no disponible.")
        if not derivaciones.destino_disponible(conexion, receptor_id):
            raise DerivacionInvalida("Selecciona un médico psiquiatra activo y registrado.")
        if not derivaciones.insertar(conexion, reserva, emisora_id, receptor_id):
            raise DerivacionInvalida("Esta solicitud ya fue derivada a ese médico psiquiatra.")


def aceptar_derivacion(conexion: sqlite3.Connection, derivacion_id: int, receptor_id: int):
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        if not derivaciones.destino_disponible(conexion, receptor_id):
            raise DerivacionNoEncontrada("Derivación no disponible.")
        if derivaciones.aceptar(conexion, derivacion_id, receptor_id):
            return
        if derivaciones.estado_recibida(conexion, derivacion_id, receptor_id) is None:
            raise DerivacionNoEncontrada("Derivación no disponible.")
        raise DerivacionInvalida("Esta derivación ya fue aceptada.")
