from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from hmac import compare_digest
from secrets import token_bytes, token_urlsafe

from app.servicios.reserva import buscar_paciente_por_rut, normalizar_rut

SEGUNDOS_SESION = 12 * 3600
N_SCRYPT = 2**15
FORMATO_CORREO = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")


class CuentaInvalida(ValueError):
    pass


def normalizar_correo(correo: str) -> str:
    correo = correo.strip().lower()
    if len(correo) > 254 or not FORMATO_CORREO.fullmatch(correo):
        raise CuentaInvalida("Ingresa un correo válido.")
    return correo


def _derivar(clave: str, sal: bytes) -> bytes:
    return hashlib.scrypt(
        clave.encode(), salt=sal, n=N_SCRYPT, r=8, p=3, maxmem=64 * 1024**2, dklen=32,
    )


def hash_clave(clave: str) -> str:
    if not 15 <= len(clave) <= 128:
        raise CuentaInvalida("La contraseña debe tener entre 15 y 128 caracteres.")
    sal = token_bytes(16)
    return f"scrypt:v1:{sal.hex()}:{_derivar(clave, sal).hex()}"


def verificar_clave(clave: str, guardado: str | None) -> bool:
    if len(clave) > 128:
        return False
    if guardado is None:
        _derivar(clave, bytes(16))
        return False
    try:
        algoritmo, version, sal, esperado = guardado.split(":")
        if (algoritmo, version) != ("scrypt", "v1"):
            return False
        return compare_digest(_derivar(clave, bytes.fromhex(sal)), bytes.fromhex(esperado))
    except ValueError:
        return False


def huella(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def registrar_cuenta(
    conexion: sqlite3.Connection, correo: str, clave: str, rut: str, nombre: str,
    telefono: str, bloque_id: int | None,
) -> int | None:
    correo = normalizar_correo(correo)
    if len(rut) > 30 or len(nombre) > 200 or len(telefono) > 40:
        raise CuentaInvalida("Revisa la longitud de los datos del paciente.")
    rut = normalizar_rut(rut)
    if not rut or not nombre.strip():
        raise CuentaInvalida("Ingresa tu nombre y RUT.")
    clave_guardada = hash_clave(clave)
    with conexion:
        cursor = conexion.execute(
            """
            INSERT INTO cuenta (
                correo, clave_hash, rol, rut_solicitado, nombre_solicitado,
                telefono_solicitado, bloque_preferido_id
            ) VALUES (?, ?, 'paciente', ?, ?, ?, (SELECT id FROM bloque_horario WHERE id = ?))
            ON CONFLICT(correo) DO NOTHING
            """,
            (correo, clave_guardada, rut, nombre.strip(), telefono.strip(), bloque_id),
        )
    return cursor.lastrowid if cursor.rowcount else None


def habilitada(cuenta: sqlite3.Row | None) -> bool:
    return bool(cuenta and cuenta["correo_verificado_en"] is not None and (
        cuenta["rol"] == "psicologa"
        or (cuenta["paciente_id"] is not None and cuenta["identidad_verificada_en"] is not None)
    ))


def crear_sesion(conexion: sqlite3.Connection, cuenta: sqlite3.Row, anterior: str = "") -> str | None:
    token = token_urlsafe(32)
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        vigente = conexion.execute("SELECT * FROM cuenta WHERE id = ?", (cuenta["id"],)).fetchone()
        if not habilitada(vigente) or vigente["clave_hash"] != cuenta["clave_hash"]:
            return None
        conexion.execute("DELETE FROM sesion WHERE expira_en <= ?", (int(time.time()),))
        revocar_sesion(conexion, anterior)
        conexion.execute(
            "INSERT INTO sesion VALUES (?, ?, ?)",
            (huella(token), cuenta["id"], int(time.time()) + SEGUNDOS_SESION),
        )
    return token


def obtener_sesion(conexion: sqlite3.Connection, token: str) -> dict | None:
    if not token or len(token) > 128:
        return None
    cuenta = conexion.execute(
        """
        SELECT c.* FROM sesion s JOIN cuenta c ON c.id = s.cuenta_id
        WHERE s.token_hash = ? AND s.expira_en > ?
        """,
        (huella(token), int(time.time())),
    ).fetchone()
    return dict(cuenta) if habilitada(cuenta) else None


def revocar_sesion(conexion: sqlite3.Connection, token: str) -> None:
    if token and len(token) <= 128:
        conexion.execute("DELETE FROM sesion WHERE token_hash = ?", (huella(token),))


def crear_token(conexion: sqlite3.Connection, cuenta_id: int, proposito: str) -> str:
    token = token_urlsafe(32)
    duracion = 24 * 3600 if proposito == "verificar" else 1800
    with conexion:
        conexion.execute(
            """
            INSERT INTO token_cuenta VALUES (?, ?, ?, ?)
            ON CONFLICT(cuenta_id, proposito) DO UPDATE SET
                token_hash = excluded.token_hash, expira_en = excluded.expira_en
            """,
            (huella(token), cuenta_id, proposito, int(time.time()) + duracion),
        )
    return token


def consumir_token(conexion: sqlite3.Connection, token: str, proposito: str, clave: str = "") -> bool:
    if not token or len(token) > 128:
        return False
    parametros = (huella(token), proposito, int(time.time()))
    consulta = "token_hash = ? AND proposito = ? AND expira_en > ?"
    if conexion.execute(f"SELECT 1 FROM token_cuenta WHERE {consulta}", parametros).fetchone() is None:
        return False
    clave_guardada = hash_clave(clave) if proposito == "restablecer" else None
    with conexion:
        fila = conexion.execute(
            f"DELETE FROM token_cuenta WHERE {consulta} RETURNING cuenta_id",
            (*parametros[:2], int(time.time())),
        ).fetchone()
        if fila is None:
            return False
        if proposito == "verificar":
            conexion.execute(
                "UPDATE cuenta SET correo_verificado_en = ? WHERE id = ? AND correo_verificado_en IS NULL",
                (int(time.time()), fila["cuenta_id"]),
            )
        else:
            conexion.execute(
                "UPDATE cuenta SET clave_hash = ? WHERE id = ?", (clave_guardada, fila["cuenta_id"]),
            )
            conexion.execute("DELETE FROM sesion WHERE cuenta_id = ?", (fila["cuenta_id"],))
    return True


def aceptar_identidad(conexion: sqlite3.Connection, cuenta_id: int, administradora_id: int) -> None:
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        cuenta = conexion.execute(
            """
            SELECT * FROM cuenta WHERE id = ? AND rol = 'paciente'
              AND correo_verificado_en IS NOT NULL AND paciente_id IS NULL
            """, (cuenta_id,),
        ).fetchone()
        if cuenta is None:
            raise CuentaInvalida("La solicitud no está lista para aprobar.")
        paciente = buscar_paciente_por_rut(conexion, cuenta["rut_solicitado"])
        if paciente is None:
            paciente_id = conexion.execute(
                "INSERT INTO paciente (rut, nombre_completo, telefono, correo) VALUES (?, ?, ?, ?)",
                (cuenta["rut_solicitado"], cuenta["nombre_solicitado"],
                 cuenta["telefono_solicitado"] or None, cuenta["correo"]),
            ).lastrowid
        else:
            paciente_id = paciente["id"]
            if paciente["correo"] and paciente["correo"].strip().lower() != cuenta["correo"]:
                raise CuentaInvalida("El correo verificado difiere del registrado para el paciente.")
            if conexion.execute("SELECT 1 FROM cuenta WHERE paciente_id = ?", (paciente_id,)).fetchone():
                raise CuentaInvalida("Este paciente ya tiene una cuenta vinculada.")
            if not paciente["correo"]:
                conexion.execute("UPDATE paciente SET correo = ? WHERE id = ?", (cuenta["correo"], paciente_id))
        conexion.execute(
            """
            UPDATE cuenta SET paciente_id = ?, identidad_verificada_en = ?, verificada_por = ?,
                rut_solicitado = NULL, nombre_solicitado = NULL, telefono_solicitado = NULL
            WHERE id = ?
            """, (paciente_id, int(time.time()), administradora_id, cuenta_id),
        )


def permitir_intento(conexion: sqlite3.Connection, clave: str, maximo: int, segundos: int) -> bool:
    ahora = int(time.time())
    with conexion:
        conexion.execute("DELETE FROM limite_cuenta WHERE expira_en <= ?", (ahora,))
        fila = conexion.execute(
            """
            INSERT INTO limite_cuenta VALUES (?, ?, 1)
            ON CONFLICT(clave) DO UPDATE SET intentos = min(intentos + 1, ?)
            RETURNING intentos
            """, (huella(clave), ahora + segundos, maximo + 1),
        ).fetchone()
    return fila["intentos"] <= maximo
