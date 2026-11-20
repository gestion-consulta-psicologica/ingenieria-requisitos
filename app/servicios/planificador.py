from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import date, datetime, timedelta

from app.configuracion import ConfiguracionCorreo
from app.db.conexion import conectar
from app.servicios import atenciones as servicio_atenciones
from app.servicios import cola_correo
from app.servicios.confirmacion import (
    CargoDuplicado,
    EstadoReservaInvalido,
    ReservaNoEncontrada,
    SecuenciaSimulacionInvalida,
    SolicitudDuplicada,
    SolicitudPendienteNoDisponible,
    TIPO_RECORDATORIO,
    TIPO_VISPERA,
    enviar_solicitud,
    marcar_hora_sin_respuesta,
)
from app.servicios.correo import (
    CorreoNoConfigurado,
    ErrorAutenticacionSMTP,
    ErrorConexionSMTP,
    ErrorEnvioSMTP,
    ServicioCorreo,
)
from app.tiempo import ahora_utc, programado

logger = logging.getLogger(__name__)

MAX_CORREOS_POR_CICLO = 50
REINTENTO_MAXIMO_SEGUNDOS = 3600


class PlanificadorCorreos:
    """Planificador de correos y de eventos temporales de HU-03.

    Cada ciclo es idempotente: las restricciones UNIQUE de la base de datos y
    los estados de las solicitudes impiden duplicar envíos o cargos.
    """

    def __init__(
        self,
        ruta_db: str,
        servicio_correo: ServicioCorreo,
        configuracion: ConfiguracionCorreo,
    ):
        self.ruta_db = str(ruta_db)
        self.servicio_correo = servicio_correo
        self.configuracion = configuracion
        self._tarea: asyncio.Task | None = None

    async def iniciar(self) -> None:
        if self._tarea is not None:
            return
        self._tarea = asyncio.create_task(self._bucle())

    async def detener(self) -> None:
        if self._tarea is None:
            return
        self._tarea.cancel()
        try:
            await self._tarea
        except asyncio.CancelledError:
            pass
        self._tarea = None

    async def _bucle(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self.ejecutar_ciclo)
            except Exception:
                logger.exception("El planificador de correos falló en un ciclo.")
            await asyncio.sleep(
                max(1, self.configuracion.intervalo_planificador_segundos)
            )

    def ejecutar_ciclo(self, ahora: datetime | None = None) -> dict:
        ahora = ahora or ahora_utc()
        conexion = conectar(self.ruta_db)
        try:
            recuperados = cola_correo.recuperar_enviando(
                conexion,
                ahora,
                self.configuracion.timeout_envio_segundos,
            )
            reservas = self._procesar_reservas(conexion, ahora)
            atenciones = self._procesar_atenciones(conexion, ahora)
            correos = self._procesar_correos(conexion, ahora)
        finally:
            conexion.close()
        return {
            "recuperados": recuperados,
            "reservas_procesadas": reservas,
            "atenciones_creadas": atenciones,
            "correos_procesados": correos,
        }

    # --- Eventos temporales de la reserva ---------------------------------
    def _procesar_reservas(
        self, conexion: sqlite3.Connection, ahora: datetime
    ) -> int:
        filas = list(
            conexion.execute(
                """
                SELECT r.id AS reserva_id, r.version, b.fecha, b.hora_inicio
                FROM reserva r
                JOIN bloque_horario b ON b.id = r.bloque_horario_id
                WHERE r.estado = 'Pendiente de confirmación'
                ORDER BY b.fecha, b.hora_inicio
                """
            )
        )
        procesadas = 0
        for fila in filas:
            try:
                self._procesar_reserva(conexion, fila, ahora)
            except (
                ReservaNoEncontrada,
                EstadoReservaInvalido,
                SolicitudDuplicada,
                SolicitudPendienteNoDisponible,
                SecuenciaSimulacionInvalida,
                CargoDuplicado,
            ):
                conexion.rollback()
            except Exception:
                conexion.rollback()
                logger.exception(
                    "No fue posible procesar los eventos de la reserva %s.",
                    fila["reserva_id"],
                )
            else:
                procesadas += 1
        return procesadas

    def _procesar_reserva(
        self, conexion: sqlite3.Connection, fila: sqlite3.Row, ahora: datetime
    ) -> None:
        zona = self.configuracion.zona_horaria
        fecha = date.fromisoformat(fila["fecha"])
        inicio = programado(fila["fecha"], fila["hora_inicio"], zona)
        vispera = programado(
            (fecha - timedelta(days=1)).isoformat(),
            self.configuracion.hora_vispera,
            zona,
        )
        recordatorio = programado(
            fila["fecha"], self.configuracion.hora_recordatorio, zona
        )

        if ahora >= inicio:
            marcar_hora_sin_respuesta(
                conexion,
                fila["reserva_id"],
                configuracion=self.configuracion,
                ahora=ahora,
            )
            return

        solicitudes = {
            solicitud["tipo"]: solicitud
            for solicitud in conexion.execute(
                """
                SELECT tipo, estado
                FROM solicitud_confirmacion
                WHERE reserva_id = ? AND version = ?
                """,
                (fila["reserva_id"], fila["version"]),
            )
        }

        if ahora >= recordatorio:
            if TIPO_RECORDATORIO not in solicitudes:
                if TIPO_VISPERA not in solicitudes:
                    enviar_solicitud(
                        conexion,
                        fila["reserva_id"],
                        TIPO_VISPERA,
                        configuracion=self.configuracion,
                        ahora=ahora,
                    )
                enviar_solicitud(
                    conexion,
                    fila["reserva_id"],
                    TIPO_RECORDATORIO,
                    configuracion=self.configuracion,
                    ahora=ahora,
                )
            return

        if ahora >= vispera and TIPO_VISPERA not in solicitudes:
            enviar_solicitud(
                conexion,
                fila["reserva_id"],
                TIPO_VISPERA,
                configuracion=self.configuracion,
                ahora=ahora,
            )

    def _procesar_atenciones(
        self, conexion: sqlite3.Connection, ahora: datetime
    ) -> int:
        try:
            creadas = servicio_atenciones.crear_atenciones_vencidas(
                conexion,
                ahora,
                self.configuracion.zona_horaria,
            )
        except Exception:
            conexion.rollback()
            logger.exception(
                "No fue posible originar las atenciones vencidas."
            )
            return 0
        return len(creadas)

    # --- Envío de correos -------------------------------------------------
    def _procesar_correos(
        self, conexion: sqlite3.Connection, ahora: datetime
    ) -> int:
        procesados = 0
        for _ in range(MAX_CORREOS_POR_CICLO):
            trabajo = cola_correo.reclamar_siguiente(conexion, ahora)
            if trabajo is None:
                break
            procesados += 1
            self._enviar_trabajo(conexion, trabajo, ahora)
        return procesados

    def _enviar_trabajo(
        self, conexion: sqlite3.Connection, trabajo: sqlite3.Row, ahora: datetime
    ) -> None:
        try:
            id_mensaje = self.servicio_correo.enviar(
                trabajo["destinatario"],
                trabajo["asunto"],
                trabajo["cuerpo_texto"],
                trabajo["cuerpo_html"],
            )
        except CorreoNoConfigurado as error:
            self._reintentar_o_fallar(
                conexion,
                trabajo,
                f"Servicio SMTP no configurado: {error}",
                ahora,
            )
        except ErrorAutenticacionSMTP as error:
            cola_correo.marcar_fallido(
                conexion, trabajo["id"], str(error), ahora
            )
            logger.error(
                "Correo %s no enviado: credenciales SMTP rechazadas.",
                trabajo["id"],
            )
        except (ErrorConexionSMTP, ErrorEnvioSMTP) as error:
            self._reintentar_o_fallar(conexion, trabajo, str(error), ahora)
        except Exception as error:  # fallo inesperado del adaptador
            self._reintentar_o_fallar(
                conexion,
                trabajo,
                f"Error inesperado al enviar el correo: {error}",
                ahora,
            )
        else:
            cola_correo.marcar_enviado(
                conexion, trabajo["id"], id_mensaje or "", ahora
            )

    def _reintentar_o_fallar(
        self,
        conexion: sqlite3.Connection,
        trabajo: sqlite3.Row,
        error: str,
        ahora: datetime,
    ) -> None:
        intentos = int(trabajo["intentos"]) + 1
        if intentos >= int(trabajo["max_intentos"]):
            cola_correo.marcar_fallido(conexion, trabajo["id"], error, ahora)
            logger.error(
                "Correo %s agotó sus reintentos: %s", trabajo["id"], error
            )
            return
        espera = min(
            self.configuracion.reintento_base_segundos * (2 ** (intentos - 1)),
            REINTENTO_MAXIMO_SEGUNDOS,
        )
        cola_correo.marcar_reintento(
            conexion,
            trabajo["id"],
            error,
            ahora + timedelta(seconds=espera),
            ahora,
        )
        logger.warning(
            "Correo %s reprogramado para reintento %s/%s: %s",
            trabajo["id"],
            intentos,
            trabajo["max_intentos"],
            error,
        )


def estado_planificador(planificador: PlanificadorCorreos | None) -> str:
    if planificador is None:
        return "desactivado"
    return "activo" if planificador._tarea is not None else "inactivo"



