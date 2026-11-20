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
        conexion.execute(
            """
            INSERT OR IGNORE INTO paciente (
                id, nombre_completo, rut, fecha_nacimiento, direccion,
                escolaridad, ocupacion, telefono, correo
            )
            VALUES (
                2, 'Paciente Sin Comprobante', '33.333.333-3', '1992-02-02',
                'Av. Ejemplo 456', 'Universitaria', 'Estudiante', '+56 9 3333 3333',
                'sin.comprobante@example.cl'
            )
            """
        )

        bloques = (
            (1, "2026-11-10", "10:00", "10:50", "presencial"),
            (2, "2026-11-10", "11:00", "11:50", "presencial"),
            (3, "2026-11-17", "10:00", "10:50", "presencial"),
            (4, "2026-11-24", "10:00", "10:50", "online"),
            (5, "2026-11-12", "16:00", "16:50", "presencial"),
            (6, "2026-11-12", "17:00", "17:50", "presencial"),
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
            (3, 1, 5, "2026-11-05T09:00:00", "Confirmada"),
            (4, 2, 6, "2026-11-05T10:00:00", "Confirmada"),
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

        atenciones = (
            (1, 3, "presencial", 30000, "programada"),
            (2, 4, "presencial", 30000, "programada"),
        )
        for atencion in atenciones:
            conexion.execute(
                """
                INSERT OR IGNORE INTO atencion (
                    id, reserva_id, tipo_atencion, monto, estado
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                atencion,
            )

        pagos = (
            (1, 1, 30000, 0, "Pendiente"),
            (2, 2, 30000, 0, "Pendiente"),
        )
        for pago in pagos:
            conexion.execute(
                """
                INSERT OR IGNORE INTO pago (
                    id, atencion_id, monto_atencion, monto_pagado, estado
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                pago,
            )

        conexion.execute(
            """
            INSERT OR IGNORE INTO comprobante_transferencia (
                id, pago_id, monto, fecha_transferencia, cuenta_destino
            )
            VALUES (1, 1, 30000, '2026-11-10', 'Cuenta de ejemplo')
            """
        )

        conexion.commit()
    finally:
        conexion.close()
    return ruta_db


if __name__ == "__main__":
    ruta = cargar_datos_ejemplo()
    print(f"Datos de ejemplo cargados en {ruta}")
