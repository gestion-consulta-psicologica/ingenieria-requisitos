"""RD-02 — Cifrado de la información clínica en reposo.

Los textos clínicos se guardan como ``enc:v1:<token Fernet>`` (AES-128-CBC con
HMAC-SHA256, de la librería ``cryptography``). La clave se lee de la variable
``CONSULTA_CLAVE_CIFRADO`` y nunca se guarda junto a la base de datos.

Generar una clave nueva:

    python -m app.servicios.cifrado

Si la clave se pierde, la información clínica cifrada no se puede recuperar:
respáldala por separado de la base.
"""

from __future__ import annotations

import logging
import os
import sqlite3

from cryptography.fernet import Fernet, InvalidToken

PREFIJO = "enc:v1:"
VARIABLE_CLAVE = "CONSULTA_CLAVE_CIFRADO"
logger = logging.getLogger(__name__)

# Columnas con información clínica o de salud: (tabla, clave primaria, columnas).
COLUMNAS_CLINICAS = (
    ("ficha_clinica", "paciente_id", (
        "motivo_consulta", "antecedentes_salud_mental", "diagnosticos",
        "medicamentos", "datos_adulto_responsable",
    )),
    ("ficha_clinica_historial", "id", (
        "motivo_consulta", "antecedentes_salud_mental", "diagnosticos",
        "medicamentos", "datos_adulto_responsable",
    )),
    ("registro_evolucion", "atencion_id", ("observaciones", "pruebas_aplicadas")),
    ("atencion", "id", ("justificacion_inasistencia",)),
)


class ClaveCifradoInvalida(ValueError):
    """La clave no tiene el formato de Fernet o no descifra los datos guardados."""


class Cifrador:
    def __init__(self, clave: str | bytes, *, persistente: bool = True):
        try:
            self._fernet = Fernet(clave)
        except (ValueError, TypeError) as error:
            raise ClaveCifradoInvalida(
                f"{VARIABLE_CLAVE} no es una clave válida; genera una con "
                "`python -m app.servicios.cifrado`."
            ) from error
        # Una clave temporal (demo y pruebas) se pierde al reiniciar.
        self.persistente = persistente

    @classmethod
    def temporal(cls) -> "Cifrador":
        return cls(Fernet.generate_key(), persistente=False)

    def cifrar(self, texto: str | None) -> str | None:
        """Cifra el texto. Los valores vacíos se guardan vacíos."""
        if texto is None or texto == "" or texto.startswith(PREFIJO):
            return texto
        return PREFIJO + self._fernet.encrypt(texto.encode("utf-8")).decode("ascii")

    def descifrar(self, valor: str | None) -> str | None:
        """Descifra el valor. Un texto plano anterior al cifrado se devuelve tal cual."""
        if valor is None or not valor.startswith(PREFIJO):
            return valor
        try:
            return self._fernet.decrypt(valor[len(PREFIJO):].encode("ascii")).decode("utf-8")
        except InvalidToken as error:
            raise ClaveCifradoInvalida(
                "No se pudo descifrar la información clínica: la clave de cifrado "
                "no corresponde a la usada al guardarla."
            ) from error


def cifrador_desde_entorno(*, obligatorio: bool) -> Cifrador:
    clave = (os.environ.get(VARIABLE_CLAVE) or "").strip()
    if clave:
        return Cifrador(clave)
    if obligatorio:
        raise ClaveCifradoInvalida(
            f"El modo con cuentas requiere {VARIABLE_CLAVE} para cifrar la ficha clínica "
            "(RD-02). Genera una con `python -m app.servicios.cifrado` y guárdala fuera "
            "del repositorio."
        )
    logger.warning(
        "Sin %s: la ficha clínica se cifra con una clave temporal y no podrá leerse "
        "después de reiniciar. Úsalo solo con bases temporales (demo o pruebas).",
        VARIABLE_CLAVE,
    )
    return Cifrador.temporal()


def cifrar_datos_pendientes(conexion: sqlite3.Connection, cifrador: Cifrador) -> int:
    """Cifra en el lugar los textos clínicos que aún estén en texto plano.

    Comprueba antes que la clave descifra los datos ya cifrados, para no mezclar
    datos con dos claves distintas.
    """
    cifrados = 0
    with conexion:
        for tabla, clave_primaria, columnas in COLUMNAS_CLINICAS:
            for columna in columnas:
                muestra = conexion.execute(
                    f"SELECT {columna} FROM {tabla} WHERE {columna} LIKE ? LIMIT 1",
                    (PREFIJO + "%",),
                ).fetchone()
                if muestra is not None:
                    cifrador.descifrar(muestra[0])  # falla si la clave no corresponde
                filas = conexion.execute(
                    f"""
                    SELECT {clave_primaria}, {columna} FROM {tabla}
                    WHERE {columna} IS NOT NULL AND {columna} <> ''
                      AND {columna} NOT LIKE ?
                    """,
                    (PREFIJO + "%",),
                ).fetchall()
                for fila in filas:
                    conexion.execute(
                        f"UPDATE {tabla} SET {columna} = ? WHERE {clave_primaria} = ?",
                        (cifrador.cifrar(fila[1]), fila[0]),
                    )
                cifrados += len(filas)
    if cifrados:
        logger.warning("Se cifraron %s textos clínicos que estaban en texto plano.", cifrados)
    return cifrados


if __name__ == "__main__":
    print(f"{VARIABLE_CLAVE}={Fernet.generate_key().decode('ascii')}")
    print("Guárdala FUERA del repositorio (por ejemplo en ~/.config/consulta/clave.env, "
          "con chmod 600) y respáldala por separado de la base de datos.")
