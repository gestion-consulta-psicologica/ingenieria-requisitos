"""Crea la primera cuenta administrativa desde una consola autorizada."""

import argparse
import sys
import time
from getpass import getpass

from app.db.conexion import conectar, inicializar_base, ruta_operativa
from app.servicios.cuentas import CuentaInvalida, hash_clave, normalizar_correo
from app.servicios.reserva import normalizar_rut


def crear_administradora(ruta, correo: str, clave: str, rut: str, nombre: str) -> None:
    destino = ruta_operativa(ruta)
    correo = normalizar_correo(correo)
    rut = normalizar_rut(rut)
    if not rut or not nombre.strip():
        raise CuentaInvalida("Ingresa el nombre y RUT de la psicóloga.")
    guardada = hash_clave(clave)
    conexion = conectar(inicializar_base(destino))
    try:
        with conexion:
            conexion.execute("BEGIN IMMEDIATE")
            if conexion.execute("SELECT 1 FROM cuenta WHERE rol = 'psicologa'").fetchone():
                raise CuentaInvalida("Ya existe una cuenta administrativa.")
            if conexion.execute("SELECT 1 FROM cuenta WHERE correo = ?", (correo,)).fetchone():
                raise CuentaInvalida("El correo ya está registrado para otra cuenta.")
            profesionales = conexion.execute("SELECT id, rut, correo FROM psicologa").fetchall()
            if profesionales:
                if len(profesionales) != 1 or (
                    normalizar_rut(profesionales[0]["rut"]) != rut
                    or profesionales[0]["correo"].strip().lower() != correo
                ):
                    raise CuentaInvalida("El RUT y el correo deben coincidir con la única psicóloga registrada.")
                psicologa_id = profesionales[0]["id"]
            else:
                psicologa_id = conexion.execute(
                    "INSERT INTO psicologa (nombre_completo, rut, correo) VALUES (?, ?, ?)",
                    (nombre.strip(), rut, correo),
                ).lastrowid
            ahora = int(time.time())
            conexion.execute(
                """
                INSERT INTO cuenta (correo, clave_hash, rol, psicologa_id,
                                    correo_verificado_en, identidad_verificada_en)
                VALUES (?, ?, 'psicologa', ?, ?, ?)
                """,
                (correo, guardada, psicologa_id, ahora, ahora),
            )
    finally:
        conexion.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Ruta explícita a la base operativa.")
    args = parser.parse_args()
    try:
        ruta_operativa(args.base)
        if not sys.stdin.isatty():
            raise CuentaInvalida("Usa una consola interactiva para introducir la contraseña sin eco.")
        correo = input("Correo de la psicóloga (confirma su titularidad antes de continuar): ")
        rut = input("RUT: ")
        nombre = input("Nombre completo: ")
        clave = getpass("Contraseña: ")
        if clave != getpass("Repite la contraseña: "):
            raise CuentaInvalida("Las contraseñas no coinciden.")
        crear_administradora(args.base, correo, clave, rut, nombre)
    except (ValueError, EOFError, KeyboardInterrupt) as error:
        parser.exit(1, f"{error}\n")
    print("Cuenta administrativa creada.")


if __name__ == "__main__":
    main()
