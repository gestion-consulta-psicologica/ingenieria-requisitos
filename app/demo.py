"""Arranque local con una base sintética nueva y sin SMTP externo."""

from argparse import ArgumentParser
from dataclasses import replace
from datetime import timedelta
from email.utils import make_msgid
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Lock

import uvicorn

from app.configuracion import cargar_configuracion
from app.db.conexion import conectar
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.confirmacion import TIPO_VISPERA, enviar_solicitud
from app.servicios.cifrado import Cifrador
from app.servicios.disponibilidad import crear_bloques_por_hora
from app.tiempo import ahora_local

URL_DEMO = "http://127.0.0.1:8000"


class ServicioCorreoDemo:
    """Correo local de demostración: acepta cada mensaje y lo muestra en consola.

    Ningún correo sale del equipo. Cumple el mismo contrato que
    ``ServicioCorreoSMTP``, de modo que la cola registra el envío como aceptado
    y el paciente puede responder la solicitud de confirmación (HU-03).
    """

    def __init__(self) -> None:
        self._candado = Lock()

    def configurado(self) -> bool:
        return True

    def motivo_no_configurado(self) -> str | None:
        return None

    def enviar(
        self, destinatario: str, asunto: str, cuerpo_texto: str,
        cuerpo_html: str | None = None,
    ) -> str:
        id_mensaje = make_msgid(domain="demo.local")
        separador = "=" * 72
        with self._candado:
            print(
                f"\n{separador}\n[CORREO DEMO · no enviado fuera del equipo]\n"
                f"Para: {destinatario}\nAsunto: {asunto}\n\n{cuerpo_texto}\n{separador}\n",
                flush=True,
            )
        return id_mensaje


def main(*, bloques_por_hora: bool = False, correo_real: bool = False) -> None:
    base = cargar_configuracion()
    if correo_real:
        # Usa el SMTP del entorno (por ejemplo Gmail, ver configuracion/gmail.env.example).
        if not base.configurado:
            raise SystemExit(
                f"--correo-real requiere SMTP configurado: {base.motivo_no_configurado} "
                "Carga primero tus variables (ver configuracion/gmail.env.example)."
            )
        configuracion = replace(
            base, planificador_activo=True, intervalo_planificador_segundos=10,
            url_publica=URL_DEMO,
        )
        servicio_correo = None
    else:
        configuracion = replace(
            base, smtp_host=None, smtp_remitente=None,
            planificador_activo=True, intervalo_planificador_segundos=10,
            url_publica=URL_DEMO,
        )
        servicio_correo = ServicioCorreoDemo()
    ahora = ahora_local(configuracion.zona_horaria)
    hoy = ahora.date()
    lunes = hoy + timedelta(days=7 - hoy.weekday())
    with TemporaryDirectory(prefix="consulta-demo-") as directorio:
        ruta = Path(directorio) / "demo.db"
        cargar_datos_ejemplo(str(ruta))
        conexion = conectar(ruta)
        try:
            conexion.executemany(
                "UPDATE bloque_horario SET fecha = ? WHERE id = ?",
                (
                    (lunes.isoformat(), 1),
                    (lunes.isoformat(), 2),
                    ((lunes - timedelta(days=9)).isoformat(), 3),
                    ((lunes + timedelta(days=1)).isoformat(), 4),
                ),
            )
            conexion.commit()
            enviar_solicitud(conexion, 1, TIPO_VISPERA, configuracion=configuracion)
            if bloques_por_hora:
                with conexion:
                    for semana in (hoy, lunes):
                        crear_bloques_por_hora(
                            conexion, 1, semana, "presencial", ahora, configuracion.zona_horaria,
                        )
        finally:
            conexion.close()
        clave = token_urlsafe(18)
        clave_paciente = token_urlsafe(18)
        app = crear_app(
            ruta, configuracion=configuracion, servicio_correo=servicio_correo,
            # La base de la demo es temporal: basta una clave de cifrado temporal.
            cifrador=Cifrador.temporal(),
            clave_psicologa_demo=clave, clave_paciente_demo=clave_paciente,
        )
        if correo_real:
            print(
                f"Correo REAL por {configuracion.smtp_host}: los correos llegan a las "
                "direcciones de los pacientes. Usa solo direcciones tuyas o de prueba.",
                flush=True,
            )
        else:
            print("Correo de demostración: los mensajes se muestran en esta consola.", flush=True)
        print(f"Panel local /psicologa · Usuario psicologa · Clave {clave}", flush=True)
        print(f"Paciente de ejemplo · Usuario paciente · Clave {clave_paciente}", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    argumentos = ArgumentParser(description=__doc__)
    argumentos.add_argument(
        "--bloques-por-hora", action="store_true",
        help="Cargar la agenda sintética de esta semana y la siguiente con inicios cada hora.",
    )
    argumentos.add_argument(
        "--correo-real", action="store_true",
        help="Enviar los correos por el SMTP configurado en el entorno (p. ej. Gmail) en vez de mostrarlos en consola.",
    )
    opciones = argumentos.parse_args()
    main(bloques_por_hora=opciones.bloques_por_hora, correo_real=opciones.correo_real)
