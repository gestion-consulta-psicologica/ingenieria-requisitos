"""Arranque local con una base sintética nueva y sin SMTP externo."""

from argparse import ArgumentParser
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

import uvicorn

from app.configuracion import cargar_configuracion
from app.db.conexion import conectar
from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.confirmacion import TIPO_VISPERA, enviar_solicitud
from app.servicios.disponibilidad import crear_bloques_por_hora
from app.tiempo import ahora_local


def main(*, bloques_por_hora: bool = False) -> None:
    configuracion = replace(
        cargar_configuracion(), smtp_host=None, smtp_remitente=None,
        planificador_activo=True,
    )
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
            ruta, configuracion=configuracion, clave_psicologa_demo=clave,
            clave_paciente_demo=clave_paciente,
        )
        print(f"Panel local /psicologa · Usuario psicologa · Clave {clave}", flush=True)
        print(f"Paciente de ejemplo · Usuario paciente · Clave {clave_paciente}", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    argumentos = ArgumentParser(description=__doc__)
    argumentos.add_argument(
        "--bloques-por-hora", action="store_true",
        help="Cargar la agenda sintética de esta semana y la siguiente con inicios cada hora.",
    )
    main(bloques_por_hora=argumentos.parse_args().bloques_por_hora)
