from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUTA_DB_POR_DEFECTO = BASE_DIR / "data" / "app.db"
DIRECTORIO_MIGRACIONES = Path(__file__).resolve().parent / "migrations"


class MigracionDatosAmbiguos(RuntimeError):
    """La migración no se aplicó porque hay registros históricos ambiguos."""

    def __init__(self, archivo: str, filas: list[dict]):
        self.archivo = archivo
        self.filas = filas
        detalle = "; ".join(
            f"solicitud {fila['solicitud_id']} de la reserva {fila['reserva_id']}: "
            f"{fila['motivo']}"
            for fila in filas
        )
        super().__init__(
            f"La migración {archivo} requiere revisión manual: {detalle}"
        )


def ruta_base_datos() -> Path:
    return Path(os.environ.get("CONSULTA_DB", RUTA_DB_POR_DEFECTO))


def conectar(ruta: str | Path | None = None) -> sqlite3.Connection:
    ruta_db = Path(ruta) if ruta is not None else ruta_base_datos()
    if str(ruta_db) != ":memory:":
        ruta_db.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta_db)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def aplicar_migraciones(conexion: sqlite3.Connection) -> None:
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conexion.commit()

    aplicadas = {
        fila["version"]
        for fila in conexion.execute("SELECT version FROM schema_migrations")
    }

    for archivo in sorted(DIRECTORIO_MIGRACIONES.glob("*.sql")):
        if archivo.name in aplicadas:
            continue
        try:
            conexion.executescript(archivo.read_text(encoding="utf-8"))
        except sqlite3.IntegrityError as error:
            filas = []
            if archivo.name == "004_solicitud_estado_cierre.sql":
                try:
                    filas = [
                        dict(fila)
                        for fila in conexion.execute(
                            """
                            SELECT solicitud_id, reserva_id, motivo
                            FROM _preflight_004
                            ORDER BY reserva_id, solicitud_id
                            """
                        )
                    ]
                except sqlite3.Error:
                    filas = []
            conexion.rollback()
            if filas:
                raise MigracionDatosAmbiguos(archivo.name, filas) from error
            raise
        except Exception:
            conexion.rollback()
            raise
        conexion.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
            (archivo.name,),
        )
        conexion.commit()


def inicializar_base(ruta: str | Path | None = None) -> Path:
    ruta_db = Path(ruta) if ruta is not None else ruta_base_datos()
    conexion = conectar(ruta_db)
    try:
        aplicar_migraciones(conexion)
    finally:
        conexion.close()
    return ruta_db
