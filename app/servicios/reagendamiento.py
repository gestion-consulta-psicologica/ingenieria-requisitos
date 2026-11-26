from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.servicios import cola_correo, plantillas_correo
from app.servicios.disponibilidad import consultar_bloques_reservables
from app.servicios.notificaciones import MOTIVO_CANCELACION, registrar_cargo_con_aviso
from app.tiempo import ZONA_POR_DEFECTO, ahora_utc, desde_iso_utc, programado, zona

ESTADO_CONFIRMADA = "Confirmada"
ESTADO_CANCELADA = "Cancelada"
ESTADO_PENDIENTE = "Pendiente de confirmación"

TIPO_CANCELACION = "cancelacion"
TIPO_REAGENDAMIENTO = "reagendamiento"

DIAS_ALTERNATIVAS = 14


class ReservaNoEncontrada(Exception):
    """La reserva indicada no existe."""


class EstadoReservaInvalido(Exception):
    """La reserva no está en un estado que permita la gestión."""


class BloqueNoEncontrado(Exception):
    """El bloque horario seleccionado no existe."""


class BloqueNoDisponible(Exception):
    """El bloque horario ya no está disponible."""


def _contexto(conexion: sqlite3.Connection, reserva_id: int) -> dict:
    fila = conexion.execute(
        """
        SELECT r.id AS reserva_id, r.paciente_id, r.bloque_horario_id,
               r.fecha_registro, r.estado, r.version,
               p.nombre_completo AS paciente_nombre, p.rut AS paciente_rut,
               p.correo AS paciente_correo, p.telefono AS paciente_telefono,
               b.fecha, b.hora_inicio, b.hora_termino, b.modalidad, b.psiquiatra_cuenta_id
        FROM reserva r
        JOIN paciente p ON p.id = r.paciente_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        WHERE r.id = ?
        """,
        (reserva_id,),
    ).fetchone()
    if fila is None:
        raise ReservaNoEncontrada("Reserva no encontrada.")
    return {
        "reserva": {
            "id": fila["reserva_id"],
            "paciente_id": fila["paciente_id"],
            "bloque_horario_id": fila["bloque_horario_id"],
            "fecha_registro": fila["fecha_registro"],
            "estado": fila["estado"],
            "version": fila["version"],
        },
        "paciente": {
            "id": fila["paciente_id"],
            "nombre_completo": fila["paciente_nombre"],
            "rut": fila["paciente_rut"],
            "correo": fila["paciente_correo"],
            "telefono": fila["paciente_telefono"],
        },
        "bloque": {
            "id": fila["bloque_horario_id"],
            "fecha": fila["fecha"],
            "hora_inicio": fila["hora_inicio"],
            "hora_termino": fila["hora_termino"],
            "modalidad": fila["modalidad"],
            "psiquiatra_cuenta_id": fila["psiquiatra_cuenta_id"],
        },
    }


def atencion_ya_comenzo(
    bloque: dict, ahora: datetime, zona_horaria: str = ZONA_POR_DEFECTO,
) -> bool:
    """Desde el inicio del bloque la reserva ya no se gestiona: sigue HU-05A/HU-08."""
    return ahora >= programado(bloque["fecha"], bloque["hora_inicio"], zona_horaria)


def reserva_tiene_atencion(conexion: sqlite3.Connection, reserva_id: int) -> bool:
    fila = conexion.execute(
        "SELECT 1 FROM atencion WHERE reserva_id = ? LIMIT 1",
        (reserva_id,),
    ).fetchone()
    return fila is not None


def _obtener_bloque(conexion: sqlite3.Connection, bloque_id: int) -> dict:
    fila = conexion.execute(
        "SELECT * FROM bloque_horario WHERE id = ?", (bloque_id,)
    ).fetchone()
    if fila is None:
        raise BloqueNoEncontrado("Bloque horario no encontrado.")
    return dict(fila)


def obtener_alternativas(
    conexion: sqlite3.Connection,
    reserva_id: int,
    *,
    desde: date | None = None,
    dias: int = DIAS_ALTERNATIVAS,
    ahora: datetime | None = None,
    zona_horaria: str = ZONA_POR_DEFECTO,
) -> list[dict]:
    contexto = _contexto(conexion, reserva_id)
    ahora = ahora or ahora_utc()
    inicio = desde or ahora.astimezone(zona(zona_horaria)).date()
    fin = inicio + timedelta(days=dias - 1)
    return consultar_bloques_reservables(
        conexion, "b.fecha BETWEEN ? AND ? AND b.id <> ?",
        (
            inicio.isoformat(),
            fin.isoformat(),
            contexto["bloque"]["id"],
        ),
        ahora=ahora,
        zona_horaria=zona_horaria,
        psiquiatra_id=contexto["bloque"]["psiquiatra_cuenta_id"],
    )


def listar_historial(
    conexion: sqlite3.Connection, reserva_id: int
) -> list[dict]:
    filas = conexion.execute(
        """
        SELECT h.*,
               ba.fecha AS anterior_fecha,
               ba.hora_inicio AS anterior_hora_inicio,
               ba.hora_termino AS anterior_hora_termino,
               bn.fecha AS nuevo_fecha,
               bn.hora_inicio AS nuevo_hora_inicio,
               bn.hora_termino AS nuevo_hora_termino
        FROM reserva_historial h
        LEFT JOIN bloque_horario ba ON ba.id = h.bloque_anterior_id
        LEFT JOIN bloque_horario bn ON bn.id = h.bloque_nuevo_id
        WHERE h.reserva_id = ?
        ORDER BY h.fecha, h.id
        """,
        (reserva_id,),
    ).fetchall()
    transferencias = conexion.execute(
        """
        SELECT 'transferencia' AS tipo, d.aceptada_en AS fecha,
               'Pendiente de confirmación' AS estado_anterior,
               'Pendiente de confirmación' AS estado_nuevo,
               d.version_origen AS version_anterior, d.version_origen + 1 AS version_nueva,
               ba.fecha AS anterior_fecha, ba.hora_inicio AS anterior_hora_inicio,
               ba.hora_termino AS anterior_hora_termino, bn.fecha AS nuevo_fecha,
               bn.hora_inicio AS nuevo_hora_inicio, bn.hora_termino AS nuevo_hora_termino,
               p.nombre_completo AS profesional_anterior, c.nombre_psiquiatra AS profesional_nuevo
        FROM derivacion d
        JOIN bloque_horario ba ON ba.id = d.bloque_origen_id
        JOIN bloque_horario bn ON bn.id = d.bloque_destino_id
        JOIN psicologa p ON p.id = ba.psicologa_id
        JOIN cuenta c ON c.id = d.psiquiatra_cuenta_id
        WHERE d.reserva_id = ?
        ORDER BY d.id
        """,
        (reserva_id,),
    ).fetchall()
    return sorted(
        (dict(fila) for fila in (*filas, *transferencias)),
        key=lambda fila: desde_iso_utc(fila["fecha"]),
    )


def cancelar_reserva(
    conexion: sqlite3.Connection, reserva_id: int, *,
    ahora: datetime | None = None,
    configuracion: ConfiguracionCorreo | None = None,
    por_psicologa: bool = False,
) -> dict:
    configuracion = configuracion or cargar_configuracion()
    ahora = ahora or ahora_utc()
    fecha_local = ahora.astimezone(zona(configuracion.zona_horaria)).isoformat(
        timespec="seconds"
    )

    conexion.execute("BEGIN IMMEDIATE")
    try:
        contexto = _contexto(conexion, reserva_id)
        if contexto["reserva"]["estado"] != ESTADO_CONFIRMADA:
            raise EstadoReservaInvalido(
                "Solo se puede cancelar una reserva confirmada."
            )
        if reserva_tiene_atencion(conexion, reserva_id):
            raise EstadoReservaInvalido(
                "La reserva ya tiene una atención y no se puede cancelar."
            )
        if atencion_ya_comenzo(contexto["bloque"], ahora, configuracion.zona_horaria):
            raise EstadoReservaInvalido(
                "La hora de la atención ya comenzó; no se puede cancelar."
            )

        cursor = conexion.execute(
            """
            UPDATE reserva
            SET estado = ?
            WHERE id = ? AND estado = ?
            """,
            (ESTADO_CANCELADA, reserva_id, ESTADO_CONFIRMADA),
        )
        if cursor.rowcount != 1:
            raise EstadoReservaInvalido(
                "La reserva ya no está en estado Confirmada."
            )

        cursor_historial = conexion.execute(
            """
            INSERT INTO reserva_historial (
                reserva_id, tipo, estado_anterior, estado_nuevo,
                bloque_anterior_id, bloque_nuevo_id,
                version_anterior, version_nueva, fecha
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                reserva_id,
                TIPO_CANCELACION,
                ESTADO_CONFIRMADA,
                ESTADO_CANCELADA,
                contexto["bloque"]["id"],
                contexto["reserva"]["version"],
                contexto["reserva"]["version"],
                fecha_local,
            ),
        )
        if por_psicologa and contexto["bloque"]["psiquiatra_cuenta_id"] is not None:
            raise EstadoReservaInvalido("La reserva ya fue transferida a psiquiatría.")
        if not por_psicologa and contexto["bloque"]["psiquiatra_cuenta_id"] is None:
            registrar_cargo_con_aviso(
                conexion, contexto, MOTIVO_CANCELACION, configuracion, ahora,
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise

    historial = conexion.execute(
        "SELECT * FROM reserva_historial WHERE id = ?",
        (cursor_historial.lastrowid,),
    ).fetchone()
    return {
        **contexto,
        "reserva": {**contexto["reserva"], "estado": ESTADO_CANCELADA},
        "historial": historial,
    }


def reagendar_reserva(
    conexion: sqlite3.Connection,
    reserva_id: int,
    nuevo_bloque_id: int,
    *,
    configuracion: ConfiguracionCorreo | None = None,
    ahora: datetime | None = None,
) -> dict:
    configuracion = configuracion or cargar_configuracion()

    conexion.execute("BEGIN IMMEDIATE")
    try:
        ahora = ahora or ahora_utc()
        local = ahora.astimezone(zona(configuracion.zona_horaria))
        fecha_local = local.isoformat(timespec="seconds")
        contexto = _contexto(conexion, reserva_id)
        if contexto["reserva"]["estado"] != ESTADO_CONFIRMADA:
            raise EstadoReservaInvalido(
                "Solo se puede reagendar una reserva confirmada."
            )
        if reserva_tiene_atencion(conexion, reserva_id):
            raise EstadoReservaInvalido(
                "La reserva ya tiene una atención y no se puede reagendar."
            )
        if atencion_ya_comenzo(contexto["bloque"], ahora, configuracion.zona_horaria):
            raise EstadoReservaInvalido(
                "La hora de la atención ya comenzó; no se puede reagendar."
            )

        nuevo_bloque = _obtener_bloque(conexion, nuevo_bloque_id)
        if nuevo_bloque_id == contexto["bloque"]["id"]:
            raise BloqueNoDisponible(
                "El bloque seleccionado es el bloque actual de la reserva."
            )
        inicio = local.date()
        fin = inicio + timedelta(days=DIAS_ALTERNATIVAS - 1)
        if not consultar_bloques_reservables(
            conexion, "b.id = ? AND b.fecha BETWEEN ? AND ?",
            (nuevo_bloque_id, inicio.isoformat(), fin.isoformat()),
            ahora=ahora, zona_horaria=configuracion.zona_horaria,
            psiquiatra_id=contexto["bloque"]["psiquiatra_cuenta_id"],
        ):
            raise BloqueNoDisponible(
                "El bloque seleccionado ya no está disponible."
            )

        version_anterior = contexto["reserva"]["version"]
        version_nueva = version_anterior + 1
        cursor = conexion.execute(
            """
            UPDATE reserva
            SET bloque_horario_id = ?, estado = ?, version = ?
            WHERE id = ? AND estado = ? AND version = ?
            """,
            (
                nuevo_bloque_id,
                ESTADO_PENDIENTE,
                version_nueva,
                reserva_id,
                ESTADO_CONFIRMADA,
                version_anterior,
            ),
        )
        if cursor.rowcount != 1:
            raise EstadoReservaInvalido(
                "La reserva cambió antes de registrar el reagendamiento."
            )

        cursor_historial = conexion.execute(
            """
            INSERT INTO reserva_historial (
                reserva_id, tipo, estado_anterior, estado_nuevo,
                bloque_anterior_id, bloque_nuevo_id,
                version_anterior, version_nueva, fecha
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reserva_id,
                TIPO_REAGENDAMIENTO,
                ESTADO_CONFIRMADA,
                ESTADO_PENDIENTE,
                contexto["bloque"]["id"],
                nuevo_bloque_id,
                version_anterior,
                version_nueva,
                fecha_local,
            ),
        )

        correo = plantillas_correo.aviso_reagendamiento(
            contexto["paciente"],
            contexto["bloque"],
            nuevo_bloque,
            contexto["reserva"],
        )
        correo_encolado = cola_correo.encolar(
            conexion,
            clave=f"aviso_reagendamiento:{reserva_id}:{version_nueva}",
            tipo=cola_correo.TIPO_AVISO_RESERVA,
            asunto=correo.asunto,
            cuerpo_texto=correo.texto,
            cuerpo_html=correo.html,
            destinatario=contexto["paciente"]["correo"],
            reserva_id=reserva_id,
            solicitud_id=None,
            creado_en=ahora,
            max_intentos=configuracion.max_intentos,
        )
        conexion.commit()
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        raise BloqueNoDisponible(
            "El bloque seleccionado ya no está disponible."
        ) from error
    except Exception:
        conexion.rollback()
        raise

    historial = conexion.execute(
        "SELECT * FROM reserva_historial WHERE id = ?",
        (cursor_historial.lastrowid,),
    ).fetchone()
    return {
        "reserva": {
            **contexto["reserva"],
            "bloque_horario_id": nuevo_bloque_id,
            "estado": ESTADO_PENDIENTE,
            "version": version_nueva,
        },
        "paciente": contexto["paciente"],
        "bloque_anterior": contexto["bloque"],
        "bloque": nuevo_bloque,
        "historial": historial,
        "correo": correo_encolado,
    }
