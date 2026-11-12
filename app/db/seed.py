from __future__ import annotations

from app.db.conexion import conectar, inicializar_base


def cargar_datos_ejemplo(ruta: str | None = None):
    ruta_db = inicializar_base(ruta)
    conexion = conectar(ruta_db)
    try:
        conexion.execute(
            """
            INSERT OR IGNORE INTO psicologa (id, nombre_completo, rut, correo)
            VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana.perez@example.cl')
            """
        )
        conexion.execute(
            """
            INSERT OR IGNORE INTO paciente (
                id, nombre_completo, rut, fecha_nacimiento, direccion,
                escolaridad, ocupacion, telefono, correo
            )
            VALUES (
                1, 'Paciente de Ejemplo', '22.222.222-2', '1990-01-01',
                'Av. Ejemplo 123', 'Universitaria', 'Analista', '+56 9 1111 1111',
                'paciente@example.cl'
            )
            """
        )

        bloques = (
            (1, "2026-11-10", "10:00", "10:50", "presencial"),
            (2, "2026-11-10", "11:00", "11:50", "presencial"),
            (3, "2026-11-17", "10:00", "10:50", "presencial"),
            (4, "2026-11-24", "10:00", "10:50", "online"),
        )
        for bloque in bloques:
            conexion.execute(
                """
                INSERT OR IGNORE INTO bloque_horario (
                    id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
                )
                VALUES (?, 1, ?, ?, ?, ?)
                """,
                bloque,
            )

        reservas = (
            (1, 1, 1, "2026-11-01T09:00:00", "Pendiente de confirmación"),
            (2, 1, 3, "2026-11-02T09:00:00", "Confirmada"),
        )
        for reserva in reservas:
            conexion.execute(
                """
                INSERT OR IGNORE INTO reserva (
                    id, paciente_id, bloque_horario_id, fecha_registro, estado
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                reserva,
            )

        conexion.commit()
    finally:
        conexion.close()
    return ruta_db


if __name__ == "__main__":
    ruta = cargar_datos_ejemplo()
    print(f"Datos de ejemplo cargados en {ruta}")
