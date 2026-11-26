import sqlite3
from pathlib import Path

import pytest

from app.db import conexion as db
from app.db.derivaciones import historial, psiquiatras
from app.servicios.cuentas import CuentaInvalida, verificar_clave
from app.servicios.derivaciones import (
    DerivacionInvalida,
    DerivacionNoEncontrada,
    SolicitudNoEncontrada,
    aceptar_derivacion,
    cambiar_disponibilidad,
    crear_derivacion,
    registrar_psiquiatra,
)
from tests.test_cuentas_persistentes import (
    ADMIN, CLAVE, BuzonPrueba, _app, _cliente, _csrf, _ingresar, _preparar,
)

PANEL = "/psicologa/derivaciones"
BANDEJA = "/psiquiatra/derivaciones"
CORREO = "psiquiatra@example.test"


@pytest.fixture
def escenario(base_temporal, conexion):
    _preparar(base_temporal)
    cuenta = conexion.execute("SELECT id FROM cuenta WHERE rol = 'psicologa'").fetchone()
    reserva = conexion.execute(
        "SELECT id, paciente_id FROM reserva WHERE estado = 'Pendiente de confirmación' ORDER BY id",
    ).fetchone()
    return cuenta["id"], reserva


def test_directorio_y_registro_validan_cuenta(conexion):
    receptor = registrar_psiquiatra(conexion, "  Médica de prueba  ", CORREO.upper(), CLAVE)
    cuenta = conexion.execute("SELECT * FROM cuenta WHERE id = ?", (receptor,)).fetchone()
    assert (cuenta["rol"], cuenta["nombre_psiquiatra"], cuenta["correo"]) == (
        "psiquiatra", "Médica de prueba", CORREO,
    )
    assert verificar_clave(CLAVE, cuenta["clave_hash"])
    with pytest.raises(CuentaInvalida, match="ya está registrado"):
        registrar_psiquiatra(conexion, "Otra persona", CORREO, CLAVE)
    cambiar_disponibilidad(conexion, receptor, False)
    assert not psiquiatras(conexion, solo_disponibles=True)
    assert psiquiatras(conexion, solo_disponibles=False)[0]["activo"] == 0


@pytest.mark.parametrize("tipo", ["inexistente", "psicologa", "paciente", "inactivo", "sin verificar"])
def test_servicio_rechaza_destinos_no_disponibles(conexion, escenario, tipo):
    emisora, reserva = escenario
    receptor = 9999
    if tipo == "psicologa":
        receptor = emisora
    elif tipo == "paciente":
        with conexion:
            receptor = conexion.execute(
                "INSERT INTO cuenta (rol, correo, clave_hash) VALUES ('paciente', ?, 'hash')",
                ("paciente@example.test",),
            ).lastrowid
    elif tipo in ("inactivo", "sin verificar"):
        receptor = registrar_psiquiatra(conexion, "Médica de prueba", CORREO, CLAVE)
        with conexion:
            if tipo == "inactivo":
                cambiar_disponibilidad(conexion, receptor, False)
            else:
                conexion.execute("UPDATE cuenta SET identidad_verificada_en = NULL WHERE id = ?", (receptor,))
    with pytest.raises(DerivacionInvalida, match="activo y registrado"):
        crear_derivacion(conexion, reserva["id"], emisora, receptor)
    assert not historial(conexion, emisora, recibidas=False)


def test_solicitud_fuera_de_agenda_o_cancelada_y_aceptacion_ajena(conexion, escenario):
    emisora, reserva = escenario
    receptor = registrar_psiquiatra(conexion, "Médica receptora", CORREO, CLAVE)
    otro = registrar_psiquiatra(conexion, "Otro médico", "otro@example.test", CLAVE)
    with conexion:
        conexion.execute("INSERT INTO psicologa VALUES (97, 'Otra psicóloga', '97-1', 'agenda@example.test')")
        bloque = conexion.execute(
            """
            INSERT INTO bloque_horario (psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
            VALUES (97, '2026-11-20', '09:00', '09:50', 'presencial')
            """
        ).lastrowid
        ajena = conexion.execute(
            """
            INSERT INTO reserva (paciente_id, bloque_horario_id, fecha_registro, estado)
            VALUES (?, ?, '2026-11-13', 'Pendiente de confirmación')
            """, (reserva["paciente_id"], bloque),
        ).lastrowid
    with pytest.raises(SolicitudNoEncontrada):
        crear_derivacion(conexion, ajena, emisora, receptor)
    crear_derivacion(conexion, reserva["id"], emisora, receptor)
    derivacion = historial(conexion, emisora, recibidas=False)[0]
    with pytest.raises(DerivacionNoEncontrada):
        aceptar_derivacion(conexion, derivacion["id"], otro)
    assert not historial(conexion, otro, recibidas=True)
    with conexion:
        conexion.execute("UPDATE reserva SET estado = 'Cancelada' WHERE id = ?", (reserva["id"],))
    with pytest.raises(SolicitudNoEncontrada):
        crear_derivacion(conexion, reserva["id"], emisora, otro)
    assert historial(conexion, emisora, recibidas=False)[0]["estado"] == "Pendiente"


def test_flujo_web_desde_reserva_hasta_aceptacion_y_reinicio(base_temporal, conexion, escenario):
    emisora, reserva = escenario
    nueva = f"{PANEL}/nueva/{reserva['id']}"
    app = _app(base_temporal, BuzonPrueba())
    with _cliente(app) as admin, _cliente(app) as doctora, _cliente(app) as otro:
        assert _ingresar(admin, ADMIN).headers["location"] == "/psicologa"
        panel = admin.get("/psicologa")
        assert f'href="{PANEL}"' in panel.text and f'href="{nueva}"' in panel.text
        assert "No hay médicos psiquiatras activos" in admin.get(nueva).text
        for nombre, correo in [("Médica receptora", CORREO), ("Otro médico", "otro@example.test")]:
            respuesta = admin.post(
                PANEL + "/psiquiatras",
                data={"nombre": nombre, "correo": correo, "clave": CLAVE, "csrf": _csrf(admin, PANEL)},
                follow_redirects=False,
            )
            assert respuesta.headers["location"] == PANEL + "#psiquiatras"

        receptor = conexion.execute("SELECT id FROM cuenta WHERE correo = ?", (CORREO,)).fetchone()[0]
        formulario = admin.get(nueva)
        assert f'action="{nueva}"' in formulario.text
        assert f'<option value="{receptor}">Médica receptora' in formulario.text
        assert admin.post(nueva, data={"psiquiatra_id": receptor}).status_code == 403
        datos = {"psiquiatra_id": receptor, "csrf": _csrf(admin, nueva)}
        assert admin.post(nueva, data={**datos, "psiquiatra_id": emisora}).status_code == 409
        assert admin.post(nueva, data=datos, follow_redirects=False).headers["location"] == PANEL
        assert admin.post(nueva, data=datos).status_code == 409
        fila = conexion.execute("SELECT * FROM derivacion").fetchone()
        assert (fila["reserva_id"], fila["paciente_id"], fila["psicologa_cuenta_id"],
                fila["psiquiatra_cuenta_id"], fila["estado"]) == (
            reserva["id"], reserva["paciente_id"], emisora, receptor, "Pendiente",
        )

        aceptar = f"{BANDEJA}/{fila['id']}/aceptar"
        assert _ingresar(otro, "otro@example.test").headers["location"] == BANDEJA
        assert "Sin derivaciones registradas" in otro.get(BANDEJA).text
        assert otro.post(aceptar, data={"csrf": _csrf(otro, BANDEJA)}).status_code == 404
        assert _ingresar(doctora, CORREO).headers["location"] == BANDEJA
        recibidas = doctora.get(BANDEJA)
        assert f'action="{aceptar}"' in recibidas.text
        assert "Pendiente" in recibidas.text and recibidas.headers["cache-control"] == "no-store"
        assert "/psicologa/fichas" not in recibidas.text
        ficha = f"/psicologa/fichas/{fila['paciente_id']}"
        assert doctora.get(ficha).status_code == 403
        assert doctora.post(
            f"{ficha}/antecedentes", data={"csrf": _csrf(doctora, BANDEJA)},
        ).status_code == 403
        eventos = conexion.execute(
            """
            SELECT rol, operacion, resultado, paciente_id, usuario
            FROM bitacora_clinica ORDER BY id
            """,
        ).fetchall()
        assert [tuple(evento) for evento in eventos] == [
            ("Psiquiatra", operacion, "denegado", fila["paciente_id"], f"cuenta:{receptor}")
            for operacion in ("lectura", "escritura")
        ]
        assert doctora.get(f"/reservas/{reserva['id']}").status_code == 403
        assert doctora.get("/pagos").status_code == 403
        assert doctora.get(PANEL).status_code == 403
        assert doctora.post(nueva, data={"csrf": _csrf(doctora, BANDEJA), "psiquiatra_id": receptor}).status_code == 403
        assert admin.get(BANDEJA).status_code == 403
        datos = {"csrf": _csrf(doctora, BANDEJA)}
        assert doctora.post(aceptar, data=datos, follow_redirects=False).headers["location"] == BANDEJA
        assert doctora.post(aceptar, data=datos).status_code == 409
        assert "Aceptada" in admin.get(PANEL).text
        assert admin.post(
            f"{PANEL}/psiquiatras/{receptor}/disponibilidad",
            data={"activo": "false", "csrf": _csrf(admin, PANEL)},
        ).status_code == 200
        assert doctora.get(BANDEJA).status_code == 401
        assert _ingresar(doctora, CORREO).status_code == 403
        assert "Médica receptora" not in admin.get(nueva).text
        assert admin.post(nueva, data={"psiquiatra_id": receptor, "csrf": _csrf(admin, nueva)}).status_code == 409

    with _cliente(_app(base_temporal, BuzonPrueba())) as admin:
        assert admin.get(PANEL).status_code == 401
        assert admin.get(BANDEJA).status_code == 401
        assert _ingresar(admin, ADMIN).status_code == 303
        assert "Aceptada" in admin.get(PANEL).text
        assert "Médica receptora" in admin.get(PANEL).text


def test_paciente_y_demo_no_pueden_consultar_ni_crear(base_temporal, conexion, escenario):
    from app.main import crear_app
    from app.servicios.cuentas import hash_clave

    _, reserva = escenario
    with conexion:
        conexion.execute(
            """
            INSERT INTO cuenta (rol, correo, clave_hash, paciente_id,
                                correo_verificado_en, identidad_verificada_en)
            VALUES ('paciente', 'paciente@example.test', ?, ?, 1, 1)
            """, (hash_clave(CLAVE), reserva["paciente_id"]),
        )
    with _cliente(_app(base_temporal, BuzonPrueba())) as paciente:
        assert _ingresar(paciente, "paciente@example.test").status_code == 303
        assert paciente.get(PANEL).status_code == paciente.get(BANDEJA).status_code == 403
        assert paciente.post(
            f"{PANEL}/nueva/{reserva['id']}",
            data={"psiquiatra_id": 1, "csrf": _csrf(paciente, "/disponibilidad")},
        ).status_code == 403
    with _cliente(crear_app(base_temporal, clave_psicologa_demo="demo")) as demo:
        assert demo.get(PANEL, auth=("psicologa", "demo")).status_code == 404
        assert demo.get(BANDEJA).status_code == 404


@pytest.mark.parametrize("version_anterior", [18, 19])
def test_migracion_preserva_cuentas_sesiones_tokens_y_datos(tmp_path, monkeypatch, version_anterior):
    migraciones = db.DIRECTORIO_MIGRACIONES
    previas = tmp_path / f"migraciones_{version_anterior:03}"
    previas.mkdir()
    for archivo in sorted(migraciones.glob("*.sql")):
        if int(archivo.name.split("_", 1)[0]) <= version_anterior:
            (previas / archivo.name).write_bytes(archivo.read_bytes())
    monkeypatch.setattr(db, "DIRECTORIO_MIGRACIONES", previas)
    ruta = tmp_path / "existente.db"
    _preparar(ruta)
    conexion = db.conectar(ruta)
    try:
        with conexion:
            conexion.execute("INSERT INTO sesion VALUES ('sesion', 1, 9999999999)")
            conexion.execute("INSERT INTO token_cuenta VALUES ('token', 1, 'restablecer', 9999999999)")
            conexion.execute(
                "INSERT INTO cuenta (rol, correo, clave_hash, verificada_por) VALUES ('paciente', ?, 'hash', 1)",
                ("pendiente@example.test",),
            )
            paciente = conexion.execute("SELECT id FROM paciente ORDER BY id").fetchone()[0]
            conexion.executemany(
                """
                INSERT INTO bitacora_clinica (id, fecha, rol, operacion, resultado, paciente_id, usuario)
                VALUES (?, '2026-11-20 12:30:00', ?, ?, ?, ?, ?)
                """,
                [
                    (4, "Psicóloga", "escritura", "permitido", paciente, "cuenta:1"),
                    (8, "Paciente", "lectura", "denegado", paciente, "paciente"),
                    (12, None, "lectura", "denegado", None, None),
                ],
            )
        if version_anterior == 19:
            receptor = registrar_psiquiatra(conexion, "Médica de prueba", CORREO, CLAVE)
            reserva = conexion.execute(
                "SELECT id FROM reserva WHERE estado = 'Pendiente de confirmación' ORDER BY id",
            ).fetchone()[0]
            crear_derivacion(conexion, reserva, 1, receptor)
        tablas = [r[0] for r in conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        columnas = [r[1] for r in conexion.execute("PRAGMA table_info(cuenta)")]
        consultas = {
            tabla: ("SELECT " + ", ".join(columnas) if tabla == "cuenta" else "SELECT *")
            + f" FROM {tabla} ORDER BY rowid"
            for tabla in tablas if tabla != "schema_migrations"
        }
        antes = {tabla: conexion.execute(sql).fetchall() for tabla, sql in consultas.items()}
        monkeypatch.setattr(db, "DIRECTORIO_MIGRACIONES", migraciones)
        db.aplicar_migraciones(conexion)
        db.aplicar_migraciones(conexion)
        assert {tabla: conexion.execute(sql).fetchall() for tabla, sql in consultas.items()} == antes
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conexion.execute("SELECT count(*) FROM derivacion").fetchone()[0] == (version_anterior == 19)
        assert "idx_bitacora_clinica_paciente" in {
            fila["name"] for fila in conexion.execute("PRAGMA index_list(bitacora_clinica)")
        }
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute("INSERT INTO sesion VALUES ('sin cuenta', 99, 9999999999)")
    finally:
        conexion.close()
