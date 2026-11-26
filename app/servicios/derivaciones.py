import sqlite3
import time

from app.configuracion import ConfiguracionCorreo, cargar_configuracion
from app.db import derivaciones
from app.servicios import cola_correo, plantillas_correo
from app.servicios.cuentas import CuentaInvalida, hash_clave, normalizar_correo
from app.tiempo import ahora_utc, iso_utc, programado


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


def solicitud_vigente(conexion, reserva_id, emisora_id, zona_horaria, ahora):
    reserva = derivaciones.solicitud(conexion, reserva_id, emisora_id)
    if reserva is None or programado(reserva["fecha"], reserva["hora_inicio"], zona_horaria) <= ahora:
        raise SolicitudNoEncontrada("Solicitud de consulta no disponible.")
    return reserva


def crear_derivacion(
    conexion: sqlite3.Connection, reserva_id: int, emisora_id: int, receptor_id: int,
    *, configuracion: ConfiguracionCorreo | None = None,
):
    configuracion = configuracion or cargar_configuracion()
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        reserva = solicitud_vigente(
            conexion, reserva_id, emisora_id, configuracion.zona_horaria, ahora_utc(),
        )
        if not derivaciones.destinos_para_solicitud(conexion, reserva, receptor_id):
            raise DerivacionInvalida("Selecciona un médico psiquiatra activo y registrado con un bloque libre para esta cita.")
        if not derivaciones.insertar(conexion, reserva, emisora_id, receptor_id):
            raise DerivacionInvalida("Ya existe una derivación pendiente o este médico ya recibió la solicitud en este ciclo.")


def responder_derivacion(
    conexion: sqlite3.Connection, derivacion_id: int, receptor_id: int,
    *, acepta: bool, configuracion: ConfiguracionCorreo | None = None,
):
    configuracion = configuracion or cargar_configuracion()
    with conexion:
        conexion.execute("BEGIN IMMEDIATE")
        recibida = derivaciones.recibida(conexion, derivacion_id, receptor_id)
        if recibida is None or not derivaciones.destino_disponible(conexion, receptor_id):
            raise DerivacionNoEncontrada("Derivación no disponible.")
        if recibida["estado"] != "Pendiente" or recibida["version_origen"] is None:
            raise DerivacionInvalida("Esta derivación ya no admite respuesta.")
        ahora = ahora_utc()
        try:
            reserva = solicitud_vigente(
                conexion, recibida["reserva_id"], recibida["psicologa_cuenta_id"],
                configuracion.zona_horaria, ahora,
            )
        except SolicitudNoEncontrada as error:
            raise DerivacionInvalida("La reserva ya no admite una transferencia.") from error
        if (reserva["version"], reserva["bloque_horario_id"]) != (
            recibida["version_origen"], recibida["bloque_origen_id"],
        ):
            raise DerivacionInvalida("La reserva cambió desde que se solicitó la derivación.")
        if not acepta:
            conexion.execute(
                "UPDATE derivacion SET rechazada_en = ? WHERE id = ?", (iso_utc(ahora), derivacion_id),
            )
            return
        destinos = derivaciones.destinos_para_solicitud(conexion, reserva, receptor_id)
        if not destinos:
            raise DerivacionInvalida("El bloque del médico psiquiatra ya no está disponible.")
        destino = destinos[0]
        conexion.execute(
            "UPDATE reserva SET bloque_horario_id = ?, version = version + 1 WHERE id = ?",
            (destino["bloque_id"], reserva["id"]),
        )
        conexion.execute(
            "UPDATE derivacion SET aceptada_en = ?, bloque_destino_id = ? WHERE id = ?",
            (iso_utc(ahora), destino["bloque_id"], derivacion_id),
        )
        solicitudes = conexion.execute(
            """
            UPDATE solicitud_confirmacion SET estado = 'reemplazada', fecha_cierre = ?
            WHERE reserva_id = ? AND estado = 'pendiente'
            RETURNING id
            """,
            (iso_utc(ahora), reserva["id"]),
        ).fetchall()
        for solicitud in solicitudes:
            cola_correo.cancelar_pendientes_de_solicitud(
                conexion, solicitud["id"], ahora, motivo="La reserva fue transferida a psiquiatría.",
            )
        correo = plantillas_correo.aviso_transferencia(
            reserva["id"], reserva["fecha"], reserva["hora_inicio"],
        )
        cola_correo.encolar(
            conexion, clave=f"aviso_transferencia:{derivacion_id}",
            tipo=cola_correo.TIPO_AVISO_RESERVA, asunto=correo.asunto,
            cuerpo_texto=correo.texto, cuerpo_html=correo.html,
            destinatario=reserva["paciente_correo"], reserva_id=reserva["id"],
            solicitud_id=None, creado_en=ahora, max_intentos=configuracion.max_intentos,
        )
