from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.servicios import cola_correo, plantillas_correo, tokens
from app.servicios.notificaciones import MOTIVO_CANCELACION, registrar_cargo_con_aviso
from app.servicios.reserva import ESTADO_PENDIENTE
from app.tiempo import ahora_utc, iso_utc, programado, zona

ESTADO_CONFIRMADA = "Confirmada"
ESTADO_CANCELADA = "Cancelada"
ESTADO_SIN_CONFIRMAR = "Sin confirmar"

ESTADO_SOLICITUD_PENDIENTE = "pendiente"
ESTADO_SOLICITUD_RESPONDIDA = "respondida"
ESTADO_SOLICITUD_REEMPLAZADA = "reemplazada"
ESTADO_SOLICITUD_VENCIDA = "vencida"

TIPO_VISPERA = "aviso de víspera"
TIPO_RECORDATORIO = "recordatorio"

RESPUESTA_CONFIRMA = "confirma"
RESPUESTA_NO_ASISTIRA = "no asistirá"
RESPUESTA_SIN_RESPUESTA = "sin respuesta"

MOTIVO_SIN_CONFIRMAR = "sin confirmar"


class ReservaNoEncontrada(Exception):
    """La reserva indicada no existe."""


class EstadoReservaInvalido(Exception):
    """La reserva no está en un estado que permita la operación."""


class SolicitudPendienteNoDisponible(Exception):
    """No existe una solicitud pendiente válida para la reserva."""


class SecuenciaSimulacionInvalida(Exception):
    """La operación intenta ejecutar un paso antes del paso previo."""


class SolicitudDuplicada(Exception):
    """La solicitud de confirmación ya fue registrada."""


class CargoDuplicado(Exception):
    """La reserva ya tiene un cargo registrado."""


def _contexto(conexion: sqlite3.Connection, reserva_id: int) -> dict:
    fila = conexion.execute(
        """
        SELECT r.id, r.paciente_id, r.bloque_horario_id,
               r.fecha_registro, r.estado, r.version,
               p.nombre_completo AS paciente_nombre,
               p.rut AS paciente_rut,
               p.telefono AS paciente_telefono,
               p.correo AS paciente_correo,
               b.fecha, b.hora_inicio, b.hora_termino, b.modalidad
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
            "id": fila["id"],
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
            "telefono": fila["paciente_telefono"],
            "correo": fila["paciente_correo"],
        },
        "bloque": {
            "id": fila["bloque_horario_id"],
            "fecha": fila["fecha"],
            "hora_inicio": fila["hora_inicio"],
            "hora_termino": fila["hora_termino"],
            "modalidad": fila["modalidad"],
        },
    }


def _obtener_solicitud(
    conexion: sqlite3.Connection, reserva_id: int, tipo: str, version: int
) -> sqlite3.Row | None:
    return conexion.execute(
        """
        SELECT *
        FROM solicitud_confirmacion
        WHERE reserva_id = ? AND tipo = ? AND version = ?
        """,
        (reserva_id, tipo, version),
    ).fetchone()


def _ultima_solicitud(
    conexion: sqlite3.Connection, reserva_id: int, version: int
) -> sqlite3.Row | None:
    return conexion.execute(
        """
        SELECT *
        FROM solicitud_confirmacion
        WHERE reserva_id = ? AND version = ?
        ORDER BY fecha_envio DESC, id DESC
        LIMIT 1
        """,
        (reserva_id, version),
    ).fetchone()


def _solicitud_pendiente(
    conexion: sqlite3.Connection, reserva_id: int, version: int
) -> sqlite3.Row | None:
    return conexion.execute(
        """
        SELECT *
        FROM solicitud_confirmacion
        WHERE reserva_id = ? AND version = ? AND estado = ?
        ORDER BY fecha_envio DESC, id DESC
        LIMIT 1
        """,
        (reserva_id, version, ESTADO_SOLICITUD_PENDIENTE),
    ).fetchone()


def _mensaje_solicitud_no_disponible(solicitud: sqlite3.Row | None) -> str:
    if solicitud is None:
        return "No existe una solicitud de confirmación pendiente para esta reserva."
    if solicitud["estado"] == ESTADO_SOLICITUD_RESPONDIDA:
        return "La solicitud de confirmación más reciente ya fue respondida."
    if solicitud["estado"] == ESTADO_SOLICITUD_REEMPLAZADA:
        return "La solicitud de confirmación más reciente fue reemplazada por el recordatorio."
    if solicitud["estado"] == ESTADO_SOLICITUD_VENCIDA:
        return "La solicitud de confirmación más reciente está vencida."
    return "No existe una solicitud de confirmación pendiente para esta reserva."


def _fecha_envio(bloque: dict, tipo: str) -> str:
    fecha = date.fromisoformat(bloque["fecha"])
    if tipo == TIPO_VISPERA:
        fecha -= timedelta(days=1)
    return fecha.isoformat()


def _expira_token(bloque: dict, configuracion: ConfiguracionCorreo) -> datetime:
    return programado(
        bloque["fecha"], bloque["hora_inicio"], configuracion.zona_horaria
    )


def _encolar_solicitud(
    conexion: sqlite3.Connection,
    contexto: dict,
    solicitud: sqlite3.Row,
    tipo: str,
    tokens_creados: dict[str, str],
    configuracion: ConfiguracionCorreo,
    ahora: datetime,
) -> sqlite3.Row:
    enlace_confirmar = (
        f"{configuracion.url_publica}/respuesta/confirmar/"
        f"{tokens_creados[tokens.ACCION_CONFIRMAR]}"
    )
    enlace_cancelar = (
        f"{configuracion.url_publica}/respuesta/cancelar/"
        f"{tokens_creados[tokens.ACCION_CANCELAR]}"
    )
    correo = plantillas_correo.solicitud_confirmacion(
        contexto["paciente"],
        contexto["bloque"],
        contexto["reserva"],
        tipo,
        enlace_confirmar,
        enlace_cancelar,
    )
    return cola_correo.encolar(
        conexion,
        clave=f"solicitud:{solicitud['id']}",
        tipo=cola_correo.TIPO_SOLICITUD,
        asunto=correo.asunto,
        cuerpo_texto=correo.texto,
        cuerpo_html=correo.html,
        destinatario=contexto["paciente"]["correo"],
        reserva_id=contexto["reserva"]["id"],
        solicitud_id=solicitud["id"],
        creado_en=ahora,
        max_intentos=configuracion.max_intentos,
    )


def enviar_solicitud(
    conexion: sqlite3.Connection,
    reserva_id: int,
    tipo: str,
    *,
    configuracion: ConfiguracionCorreo | None = None,
    ahora: datetime | None = None,
) -> dict:
    if tipo not in (TIPO_VISPERA, TIPO_RECORDATORIO):
        raise ValueError("Tipo de solicitud de confirmación inválido.")

    configuracion = configuracion or cargar_configuracion()
    ahora = ahora or ahora_utc()
    contexto = _contexto(conexion, reserva_id)
    version = contexto["reserva"]["version"]
    if contexto["reserva"]["estado"] != ESTADO_PENDIENTE:
        raise EstadoReservaInvalido(
            "La reserva ya no está en estado Pendiente de confirmación."
        )

    if tipo == TIPO_RECORDATORIO:
        if _obtener_solicitud(conexion, reserva_id, TIPO_VISPERA, version) is None:
            raise SecuenciaSimulacionInvalida(
                "Primero debe enviarse la solicitud de confirmación de la víspera."
            )
    elif _solicitud_pendiente(conexion, reserva_id, version) is not None:
        raise SolicitudDuplicada(
            "Ya existe una solicitud de confirmación pendiente para esta reserva."
        )

    if _obtener_solicitud(conexion, reserva_id, tipo, version) is not None:
        raise SolicitudDuplicada("Esta solicitud ya fue enviada.")

    fecha_envio = _fecha_envio(contexto["bloque"], tipo)
    anterior = None
    if tipo == TIPO_RECORDATORIO:
        anterior = _solicitud_pendiente(conexion, reserva_id, version)
        if anterior is None:
            raise SolicitudPendienteNoDisponible(
                _mensaje_solicitud_no_disponible(
                    _ultima_solicitud(conexion, reserva_id, version)
                )
            )

    try:
        if tipo == TIPO_RECORDATORIO:
            cursor_anterior = conexion.execute(
                """
                UPDATE solicitud_confirmacion
                SET estado = ?, fecha_cierre = ?
                WHERE id = ? AND estado = ?
                """,
                (
                    ESTADO_SOLICITUD_REEMPLAZADA,
                    fecha_envio,
                    anterior["id"],
                    ESTADO_SOLICITUD_PENDIENTE,
                ),
            )
            if cursor_anterior.rowcount != 1:
                raise SolicitudPendienteNoDisponible(
                    "La solicitud pendiente anterior cambió durante el envío."
                )

        cursor = conexion.execute(
            """
            INSERT INTO solicitud_confirmacion (
                reserva_id, version, fecha_envio, tipo, estado,
                respuesta, fecha_respuesta, fecha_cierre
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)
            """,
            (
                reserva_id,
                version,
                fecha_envio,
                tipo,
                ESTADO_SOLICITUD_PENDIENTE,
            ),
        )
        solicitud_id = cursor.lastrowid

        tokens_creados = tokens.crear_tokens(
            conexion,
            solicitud_id,
            _expira_token(contexto["bloque"], configuracion),
            ahora,
        )

        if anterior is not None:
            cola_correo.cancelar_pendientes_de_solicitud(
                conexion, anterior["id"], ahora
            )

        solicitud = conexion.execute(
            "SELECT * FROM solicitud_confirmacion WHERE id = ?", (solicitud_id,)
        ).fetchone()
        correo = _encolar_solicitud(
            conexion,
            contexto,
            solicitud,
            tipo,
            tokens_creados,
            configuracion,
            ahora,
        )
        conexion.commit()
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        raise SolicitudDuplicada("Esta solicitud ya fue enviada.") from error
    except Exception:
        conexion.rollback()
        raise

    return {
        **contexto,
        "solicitud": solicitud,
        "tipo": tipo,
        "tokens": tokens_creados,
        "correo": correo,
    }


def _registrar_respuesta(
    conexion: sqlite3.Connection,
    reserva_id: int,
    respuesta: str,
    *,
    token_id: int | None = None,
    ahora: datetime | None = None,
    configuracion: ConfiguracionCorreo | None = None,
) -> dict:
    if respuesta not in (RESPUESTA_CONFIRMA, RESPUESTA_NO_ASISTIRA):
        raise ValueError("Respuesta de confirmación inválida.")

    configuracion = configuracion or cargar_configuracion()
    ahora = ahora or ahora_utc()
    contexto = _contexto(conexion, reserva_id)
    version = contexto["reserva"]["version"]
    if contexto["reserva"]["estado"] != ESTADO_PENDIENTE:
        raise EstadoReservaInvalido(
            "La reserva ya no está en estado Pendiente de confirmación."
        )

    ultima = _ultima_solicitud(conexion, reserva_id, version)
    if ultima is None or ultima["estado"] != ESTADO_SOLICITUD_PENDIENTE:
        raise SolicitudPendienteNoDisponible(
            _mensaje_solicitud_no_disponible(ultima)
        )

    bloque = contexto["bloque"]
    inicio = programado(bloque["fecha"], bloque["hora_inicio"], configuracion.zona_horaria)
    if ahora >= inicio:
        raise SolicitudPendienteNoDisponible("El plazo de respuesta ya venció.")
    if not cola_correo.solicitud_enviada(conexion, ultima["id"]):
        raise SolicitudPendienteNoDisponible("La solicitud de confirmación aún no fue enviada.")

    nuevo_estado = (
        ESTADO_CONFIRMADA
        if respuesta == RESPUESTA_CONFIRMA
        else ESTADO_CANCELADA
    )
    fecha_respuesta = ahora.astimezone(zona(configuracion.zona_horaria)).isoformat(
        timespec="seconds"
    )

    try:
        if token_id is not None:
            cursor_token = conexion.execute(
                """
                UPDATE token_confirmacion
                SET usado_en = ?
                WHERE id = ? AND usado_en IS NULL
                """,
                (iso_utc(ahora), token_id),
            )
            if cursor_token.rowcount != 1:
                raise tokens.TokenUsado("Este enlace ya fue utilizado.")

        cursor_reserva = conexion.execute(
            """
            UPDATE reserva
            SET estado = ?
            WHERE id = ? AND estado = ?
            """,
            (nuevo_estado, reserva_id, ESTADO_PENDIENTE),
        )
        if cursor_reserva.rowcount != 1:
            raise EstadoReservaInvalido(
                "La reserva ya no está en estado Pendiente de confirmación."
            )

        cursor_solicitud = conexion.execute(
            """
            UPDATE solicitud_confirmacion
            SET estado = ?, respuesta = ?, fecha_respuesta = ?, fecha_cierre = NULL
            WHERE id = ? AND estado = ?
            """,
            (
                ESTADO_SOLICITUD_RESPONDIDA,
                respuesta,
                fecha_respuesta,
                ultima["id"],
                ESTADO_SOLICITUD_PENDIENTE,
            ),
        )
        if cursor_solicitud.rowcount != 1:
            raise SolicitudPendienteNoDisponible(
                "La solicitud pendiente cambió antes de registrar la respuesta."
            )

        if respuesta == RESPUESTA_NO_ASISTIRA:
            registrar_cargo_con_aviso(
                conexion, contexto, MOTIVO_CANCELACION,
                configuracion, ahora,
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise

    solicitud = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE id = ?",
        (ultima["id"],),
    ).fetchone()
    return {
        **contexto,
        "reserva": {**contexto["reserva"], "estado": nuevo_estado},
        "solicitud": solicitud,
        "respuesta": respuesta,
        "fecha_respuesta": fecha_respuesta,
    }


def registrar_respuesta(
    conexion: sqlite3.Connection,
    reserva_id: int,
    respuesta: str,
    *,
    ahora: datetime | None = None,
    configuracion: ConfiguracionCorreo | None = None,
) -> dict:
    return _registrar_respuesta(
        conexion, reserva_id, respuesta, ahora=ahora, configuracion=configuracion,
    )


def registrar_respuesta_con_token(
    conexion: sqlite3.Connection,
    token: str,
    respuesta: str,
    *,
    ahora: datetime | None = None,
    configuracion: ConfiguracionCorreo | None = None,
) -> dict:
    ahora = ahora or ahora_utc()
    fila = tokens.buscar_token(conexion, token, ahora)
    esperada = (
        tokens.ACCION_CONFIRMAR
        if respuesta == RESPUESTA_CONFIRMA
        else tokens.ACCION_CANCELAR
    )
    if fila["accion"] != esperada:
        raise tokens.TokenAccionInvalida(
            "El enlace no corresponde a la acción solicitada."
        )
    return _registrar_respuesta(
        conexion,
        fila["reserva_id"],
        respuesta,
        token_id=fila["id"],
        ahora=ahora,
        configuracion=configuracion,
    )


def marcar_hora_sin_respuesta(
    conexion: sqlite3.Connection,
    reserva_id: int,
    *,
    configuracion: ConfiguracionCorreo | None = None,
    ahora: datetime | None = None,
) -> dict:
    configuracion = configuracion or cargar_configuracion()
    ahora = ahora or ahora_utc()
    contexto = _contexto(conexion, reserva_id)
    version = contexto["reserva"]["version"]

    if conexion.execute(
        "SELECT 1 FROM cargo WHERE reserva_id = ?", (reserva_id,)
    ).fetchone() is not None:
        raise CargoDuplicado("La reserva ya tiene un cargo registrado.")

    if contexto["reserva"]["estado"] != ESTADO_PENDIENTE:
        raise EstadoReservaInvalido(
            "La reserva ya no está en estado Pendiente de confirmación."
        )

    ultima = _ultima_solicitud(conexion, reserva_id, version)
    if ultima is None or ultima["estado"] != ESTADO_SOLICITUD_PENDIENTE:
        raise SolicitudPendienteNoDisponible(
            _mensaje_solicitud_no_disponible(ultima)
        )

    fecha_cierre = (
        f"{contexto['bloque']['fecha']}T{contexto['bloque']['hora_inicio']}"
    )

    try:
        cursor_reserva = conexion.execute(
            """
            UPDATE reserva
            SET estado = ?
            WHERE id = ? AND estado = ?
            """,
            (ESTADO_SIN_CONFIRMAR, reserva_id, ESTADO_PENDIENTE),
        )
        if cursor_reserva.rowcount != 1:
            raise EstadoReservaInvalido(
                "La reserva ya no está en estado Pendiente de confirmación."
            )

        cursor_solicitud = conexion.execute(
            """
            UPDATE solicitud_confirmacion
            SET estado = ?, respuesta = ?, fecha_respuesta = NULL, fecha_cierre = ?
            WHERE id = ? AND estado = ?
            """,
            (
                ESTADO_SOLICITUD_VENCIDA,
                RESPUESTA_SIN_RESPUESTA,
                fecha_cierre,
                ultima["id"],
                ESTADO_SOLICITUD_PENDIENTE,
            ),
        )
        if cursor_solicitud.rowcount != 1:
            raise SolicitudPendienteNoDisponible(
                "La solicitud pendiente cambió antes de marcar la hora."
            )

        cola_correo.cancelar_pendientes_de_solicitud(
            conexion, ultima["id"], ahora, motivo="La solicitud de confirmación venció.",
        )
        cargo = correo_encolado = None
        inicio = programado(
            contexto["bloque"]["fecha"], contexto["bloque"]["hora_inicio"],
            configuracion.zona_horaria,
        )
        enviado = conexion.execute(
            """
            SELECT 1 FROM solicitud_confirmacion s
            JOIN correo_pendiente c ON c.solicitud_id = s.id
            WHERE s.reserva_id = ? AND s.version = ? AND c.estado = ?
              AND c.enviado_en < ?
            LIMIT 1
            """,
            (reserva_id, version, cola_correo.ESTADO_ENVIADO, iso_utc(inicio)),
        ).fetchone()
        if enviado is not None:
            cargo, correo_encolado = registrar_cargo_con_aviso(
                conexion, contexto, MOTIVO_SIN_CONFIRMAR, configuracion, ahora,
            )
        conexion.commit()
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        if conexion.execute(
            "SELECT 1 FROM cargo WHERE reserva_id = ?", (reserva_id,)
        ).fetchone() is not None:
            raise CargoDuplicado("La reserva ya tiene un cargo registrado.") from error
        raise EstadoReservaInvalido(
            "No fue posible registrar el cierre sin respuesta de la reserva."
        ) from error
    except Exception:
        conexion.rollback()
        raise

    solicitud = conexion.execute(
        "SELECT * FROM solicitud_confirmacion WHERE id = ?",
        (ultima["id"],),
    ).fetchone()
    return {
        **contexto,
        "reserva": {**contexto["reserva"], "estado": ESTADO_SIN_CONFIRMAR},
        "solicitud": solicitud,
        "cargo": cargo,
        "correo": correo_encolado,
        "fecha_cierre": fecha_cierre,
    }
