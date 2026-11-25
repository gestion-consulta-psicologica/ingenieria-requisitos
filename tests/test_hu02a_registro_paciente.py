from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.conexion import aplicar_migraciones, conectar
from app.main import crear_app
from app.servicios import paciente as paciente_servicio
from app.servicios.paciente import (
    DatosPacienteInvalidos,
    registrar_paciente,
)

DIRECTORIO_MIGRACIONES = (
    Path(__file__).resolve().parent.parent / "app" / "db" / "migrations"
)


def test_migracion_002_conserva_datos_y_permite_correo_opcional(tmp_path):
    ruta = tmp_path / "migracion.db"
    conexion = conectar(ruta)
    try:
        conexion.executescript(
            (DIRECTORIO_MIGRACIONES / "001_crear_tablas_base.sql").read_text(
                encoding="utf-8"
            )
        )
        conexion.execute(
            "INSERT INTO psicologa (id, nombre_completo, rut, correo) "
            "VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')"
        )
        conexion.execute(
            "INSERT INTO paciente (id, nombre_completo, rut, correo) "
            "VALUES (1, 'Paciente Existente', '22.222.222-2', 'paciente@example.cl')"
        )
        conexion.execute(
            "INSERT INTO bloque_horario "
            "(id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad) "
            "VALUES (1, 1, '2026-11-12', '16:00', '16:50', 'presencial')"
        )
        conexion.execute(
            "INSERT INTO reserva "
            "(id, paciente_id, bloque_horario_id, fecha_registro, estado) "
            "VALUES (1, 1, 1, '2026-11-01T09:00:00', 'Confirmada')"
        )
        conexion.commit()

        aplicar_migraciones(conexion)

        paciente = conexion.execute(
            "SELECT * FROM paciente WHERE id = 1"
        ).fetchone()
        assert paciente["nombre_completo"] == "Paciente Existente"
        assert paciente["correo"] == "paciente@example.cl"

        reserva = conexion.execute("SELECT * FROM reserva WHERE id = 1").fetchone()
        assert reserva["paciente_id"] == 1

        conexion.execute(
            "INSERT INTO paciente (nombre_completo, rut, telefono) "
            "VALUES ('Solo Teléfono', '44.444.444-4', '+56 9 3333 3333')"
        )
        nuevo = conexion.execute(
            "SELECT * FROM paciente WHERE rut = '44.444.444-4'"
        ).fetchone()
        assert nuevo["correo"] is None

        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO paciente (nombre_completo, rut, telefono) "
                "VALUES ('Duplicado', '444444444', '+56 9 4444 4444')"
            )

        conexion.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO reserva "
                "(paciente_id, bloque_horario_id, fecha_registro, estado) "
                "VALUES (999, 1, '2026-11-02T09:00:00', 'Confirmada')"
            )
    finally:
        conexion.close()


def insertar_paciente(
    conexion,
    paciente_id: int = 1,
    nombre_completo: str = "Paciente Uno",
    rut: str = "22.222.222-2",
    telefono: str | None = "+56 9 1111 1111",
    correo: str | None = "uno@example.cl",
):
    conexion.execute(
        """
        INSERT INTO paciente (id, nombre_completo, rut, telefono, correo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (paciente_id, nombre_completo, rut, telefono, correo),
    )
    conexion.commit()


def contar_pacientes(conexion) -> int:
    return conexion.execute("SELECT COUNT(*) FROM paciente").fetchone()[0]


def preparar_psicologa(conexion):
    conexion.execute(
        """
        INSERT INTO psicologa (id, nombre_completo, rut, correo)
        VALUES (1, 'Ana Pérez', '11.111.111-1', 'ana@example.cl')
        """
    )
    conexion.commit()


def insertar_bloque(
    conexion,
    bloque_id: int,
    fecha: str,
    hora_inicio: str = "16:00",
    hora_termino: str = "16:50",
):
    conexion.execute(
        """
        INSERT INTO bloque_horario (
            id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad
        )
        VALUES (?, 1, ?, ?, ?, 'presencial')
        """,
        (bloque_id, fecha, hora_inicio, hora_termino),
    )
    conexion.commit()


def test_registrar_paciente_solo_telefono(conexion):
    resultado = registrar_paciente(
        conexion, "Paciente Nuevo", "99.999.999-9", "+56 9 1234 5678", ""
    )

    assert resultado["creado"] is True
    assert resultado["paciente"]["nombre_completo"] == "Paciente Nuevo"
    assert resultado["paciente"]["telefono"] == "+56 9 1234 5678"
    assert resultado["paciente"]["correo"] is None


def test_registrar_paciente_solo_correo(conexion):
    resultado = registrar_paciente(
        conexion, "Paciente Nuevo", "98.888.888-8", "", "nuevo@example.cl"
    )

    assert resultado["creado"] is True
    assert resultado["paciente"]["telefono"] is None
    assert resultado["paciente"]["correo"] == "nuevo@example.cl"


def test_registrar_paciente_sin_contacto_no_lo_registra(conexion):
    with pytest.raises(DatosPacienteInvalidos) as error:
        registrar_paciente(conexion, "Paciente Nuevo", "97.777.777-7", "", "  ")

    assert error.value.faltantes == [
        "un medio de contacto (teléfono o correo)"
    ]
    assert contar_pacientes(conexion) == 0


def test_registrar_paciente_sin_nombre_no_lo_registra(conexion):
    with pytest.raises(DatosPacienteInvalidos) as error:
        registrar_paciente(conexion, "   ", "97.777.777-7", "123", None)

    assert error.value.faltantes == ["nombre completo"]
    assert contar_pacientes(conexion) == 0


def test_registrar_paciente_rechaza_un_rut_con_letras_ignoradas_por_la_busqueda(conexion):
    with pytest.raises(DatosPacienteInvalidos, match="RUT"):
        registrar_paciente(conexion, "Paciente", "ab99.999.999-9", telefono="12345678")

    assert conexion.execute("SELECT COUNT(*) FROM paciente").fetchone()[0] == 0


def test_registrar_paciente_sin_rut_no_lo_registra(conexion):
    with pytest.raises(DatosPacienteInvalidos) as error:
        registrar_paciente(conexion, "Paciente Nuevo", "   ", "123", "")

    assert error.value.faltantes == ["RUT"]
    assert contar_pacientes(conexion) == 0


def test_registrar_paciente_reutiliza_rut_con_formato_distinto(conexion):
    insertar_paciente(conexion)

    resultado = registrar_paciente(conexion, "Otro Nombre", "222222222", "", "")

    assert resultado["creado"] is False
    assert resultado["paciente"]["id"] == 1
    assert resultado["paciente"]["nombre_completo"] == "Paciente Uno"
    assert contar_pacientes(conexion) == 1


def test_registrar_paciente_captura_carrera_de_rut(conexion, monkeypatch):
    insertar_paciente(conexion)
    buscar_real = paciente_servicio.buscar_paciente_por_rut
    llamadas = {"total": 0}

    def buscar_simulado(conexion_actual, rut):
        llamadas["total"] += 1
        if llamadas["total"] == 1:
            return None
        return buscar_real(conexion_actual, rut)

    monkeypatch.setattr(
        paciente_servicio, "buscar_paciente_por_rut", buscar_simulado
    )

    resultado = registrar_paciente(
        conexion, "Otro Nombre", "22.222.222-2", "+56 9 9999 9999", ""
    )

    assert resultado["creado"] is False
    assert resultado["paciente"]["id"] == 1
    assert contar_pacientes(conexion) == 1


def test_formulario_registro_conserva_bloque(base_temporal, conexion):
    preparar_psicologa(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get("/pacientes/registro?bloque_id=10")

    assert respuesta.status_code == 200
    assert 'name="bloque_id"' in respuesta.text
    assert 'value="10"' in respuesta.text
    assert 'name="nombre_completo"' in respuesta.text
    assert 'name="rut"' in respuesta.text
    assert 'name="telefono"' in respuesta.text
    assert 'name="correo"' in respuesta.text


def test_formulario_reserva_precarga_rut(base_temporal, conexion):
    preparar_psicologa(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.get("/reservar/10", params={"rut": "222222222"})

    assert respuesta.status_code == 200
    assert 'value="222222222"' in respuesta.text


def test_registro_sin_bloque_muestra_confirmacion(base_temporal, conexion):
    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post(
            "/pacientes/registro",
            data={
                "nombre_completo": "Paciente Nuevo",
                "rut": "99.999.999-9",
                "telefono": "+56 9 1234 5678",
                "correo": "",
                "bloque_id": "",
            },
            follow_redirects=False,
        )
        assert respuesta.status_code == 303
        assert respuesta.headers["location"] == "/pacientes/1"

        confirmacion = cliente.get(respuesta.headers["location"])

    assert confirmacion.status_code == 200
    assert "Paciente Nuevo" in confirmacion.text
    assert "99.999.999-9" in confirmacion.text


@pytest.mark.parametrize(
    "caso",
    [
        pytest.param(
            "paciente nuevo",
            id="HU-02A · Un paciente nuevo se registra desde la reserva",
        )
    ],
)
def test_paciente_nuevo_se_registra_desde_la_reserva(
    base_temporal, conexion, caso
):
    preparar_psicologa(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")

    with TestClient(crear_app(base_temporal)) as cliente:
        derivacion = cliente.post(
            "/reservar/10",
            data={"rut": "99.999.999-9"},
            follow_redirects=False,
        )
        assert derivacion.status_code == 303
        assert (
            derivacion.headers["location"]
            == "/pacientes/registro?bloque_id=10"
        )

        formulario = cliente.get("/pacientes/registro?bloque_id=10")
        assert formulario.status_code == 200

        registro = cliente.post(
            "/pacientes/registro",
            data={
                "nombre_completo": "Paciente Nuevo",
                "rut": "99.999.999-9",
                "telefono": "+56 9 1234 5678",
                "correo": "",
                "bloque_id": "10",
            },
            follow_redirects=False,
        )
        assert registro.status_code == 303
        assert registro.headers["location"] == "/reservar/10?rut=999999999"

        assert conexion.execute("SELECT COUNT(*) FROM reserva").fetchone()[0] == 0

        formulario_reserva = cliente.get(registro.headers["location"])
        assert formulario_reserva.status_code == 200
        assert 'value="999999999"' in formulario_reserva.text

        reserva = cliente.post(
            "/reservar/10",
            data={"rut": "999999999"},
            follow_redirects=False,
        )
        assert reserva.status_code == 303
        assert reserva.headers["location"] == "/reservas/1"

    paciente = conexion.execute(
        "SELECT * FROM paciente WHERE rut = '99.999.999-9'"
    ).fetchone()
    assert paciente is not None
    assert paciente["correo"] is None

    reserva_guardada = conexion.execute(
        "SELECT * FROM reserva WHERE bloque_horario_id = 10"
    ).fetchone()
    assert reserva_guardada["estado"] == "Pendiente de confirmación"


@pytest.mark.parametrize(
    "datos, faltante",
    [
        pytest.param(
            {
                "nombre_completo": "",
                "rut": "98.888.888-8",
                "telefono": "+56 9 1234 5678",
                "correo": "",
                "bloque_id": "",
            },
            "nombre completo",
            id="HU-02A · El paciente no completa los datos obligatorios (sin nombre)",
        ),
        pytest.param(
            {
                "nombre_completo": "Paciente Nuevo",
                "rut": "98.888.888-8",
                "telefono": "",
                "correo": "",
                "bloque_id": "",
            },
            "un medio de contacto",
            id="HU-02A · El paciente no completa los datos obligatorios (sin contacto)",
        ),
    ],
)
def test_paciente_no_completa_datos_obligatorios(
    base_temporal, conexion, datos, faltante
):
    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post("/pacientes/registro", data=datos)

    assert respuesta.status_code == 400
    assert "Falta completar" in respuesta.text
    assert faltante in respuesta.text
    assert contar_pacientes(conexion) == 0


def test_formulario_registro_sin_rut_no_crea_registros(base_temporal, conexion):
    preparar_psicologa(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")

    with TestClient(crear_app(base_temporal)) as cliente:
        respuesta = cliente.post(
            "/pacientes/registro",
            data={
                "nombre_completo": "Paciente Nuevo",
                "telefono": "+56 9 1234 5678",
                "correo": "",
                "bloque_id": "10",
            },
            follow_redirects=False,
        )

    assert respuesta.status_code == 400
    assert "Falta completar" in respuesta.text
    assert "RUT" in respuesta.text
    assert contar_pacientes(conexion) == 0
    assert conexion.execute("SELECT COUNT(*) FROM reserva").fetchone()[0] == 0


@pytest.mark.parametrize(
    "caso",
    [pytest.param("rut existente", id="HU-02A · El RUT ya está registrado")],
)
def test_rut_ya_registrado(base_temporal, conexion, caso):
    preparar_psicologa(conexion)
    insertar_paciente(conexion)
    insertar_bloque(conexion, 10, "2026-11-12")

    with TestClient(crear_app(base_temporal, clave_paciente_demo="clave-prueba")) as cliente:
        respuesta = cliente.post(
            "/pacientes/registro",
            auth=("paciente", "clave-prueba"),
            data={
                "nombre_completo": "Otro Nombre",
                "rut": "222222222",
                "telefono": "",
                "correo": "",
                "bloque_id": "10",
            },
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/reservar/10?rut=222222222"
    assert contar_pacientes(conexion) == 1

    paciente = conexion.execute("SELECT * FROM paciente").fetchone()
    assert paciente["nombre_completo"] == "Paciente Uno"
