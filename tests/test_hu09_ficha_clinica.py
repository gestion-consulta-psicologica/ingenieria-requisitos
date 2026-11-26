import pytest
from fastapi.testclient import TestClient

from app.db.seed import cargar_datos_ejemplo
from app.main import crear_app
from app.servicios.cifrado import PREFIJO


def test_psicologa_registra_y_paciente_no_puede_consultar_ni_modificar(
    base_temporal, conexion,
):
    cargar_datos_ejemplo(str(base_temporal))
    conexion.execute("UPDATE atencion SET estado = 'realizada' WHERE id = 1")
    conexion.commit()
    admin = ("psicologa", "clave-admin")
    paciente = ("paciente", "clave-paciente")
    app = crear_app(
        base_temporal, clave_psicologa_demo=admin[1], clave_paciente_demo=paciente[1],
    )
    url = "/psicologa/fichas/1"
    datos = {
        "atencion_id": 1, "observaciones": "Contenido clínico sintético",
        "csrf": app.state.csrf_psicologa_demo,
    }
    with TestClient(app) as cliente:
        assert url in cliente.get("/psicologa", auth=admin).text
        assert cliente.post(url, data=datos, auth=admin, follow_redirects=False).status_code == 303
        vista = cliente.get(url, auth=admin)
        assert datos["observaciones"] in vista.text
        assert vista.headers["cache-control"] == "no-store"
        assert cliente.post(url, data=datos, auth=admin).status_code == 409
        assert cliente.post("/psicologa/fichas/2", data=datos, auth=admin).status_code == 409
        intentos = (
            cliente.get(url, auth=paciente),
            cliente.post(url, data={**datos, "observaciones": "Texto rechazado"}, auth=paciente),
        )
        for intento in intentos:
            assert intento.status_code == 403
            assert intento.json() == {"detail": "Acceso denegado."}
    registros = conexion.execute("SELECT observaciones FROM registro_evolucion").fetchall()
    # RD-02: en la base queda cifrado; la aplicación lo descifra.
    assert all(fila[0].startswith(PREFIJO) for fila in registros)
    assert datos["observaciones"] not in str([fila[0] for fila in registros])
    assert [app.state.cifrador.descifrar(fila[0]) for fila in registros] == [datos["observaciones"]]
    eventos = conexion.execute("SELECT * FROM bitacora_clinica WHERE resultado = 'denegado'").fetchall()
    assert [(e["rol"], e["operacion"]) for e in eventos] == [
        ("Paciente", "lectura"), ("Paciente", "escritura"),
    ]
    # Sin contenido clínico: solo quién, qué ficha, qué operación y el resultado.
    assert set(eventos[0].keys()) == {
        "id", "fecha", "rol", "operacion", "resultado", "paciente_id", "usuario",
    }
    assert [(e["paciente_id"], e["usuario"]) for e in eventos] == [
        (1, "paciente"), (1, "paciente"),
    ]
    permitidos = conexion.execute(
        "SELECT DISTINCT paciente_id, usuario FROM bitacora_clinica WHERE resultado = 'permitido'"
    ).fetchall()
    assert [tuple(fila) for fila in permitidos] == [(1, "psicologa")]


def test_antecedentes_y_dos_evoluciones_conservan_historial(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    conexion.execute("UPDATE atencion SET estado = 'realizada' WHERE id = 1")
    nueva = conexion.execute(
        """
        INSERT INTO atencion (reserva_id, tipo_atencion, monto, estado)
        VALUES (2, 'presencial', 30000, 'realizada')
        """
    ).lastrowid
    conexion.commit()
    admin = ("psicologa", "clave-admin")
    paciente = ("paciente", "clave-paciente")
    app = crear_app(
        base_temporal, clave_psicologa_demo=admin[1], clave_paciente_demo=paciente[1],
    )
    csrf = app.state.csrf_psicologa_demo
    url = "/psicologa/fichas/1"
    antecedentes = {
        "csrf": csrf, "motivo_consulta": "Motivo sintético inicial",
        "antecedentes_salud_mental": "Antecedente sintético",
        "diagnosticos": "Diagnóstico sintético", "medicamentos": "Medicamento sintético",
        "datos_adulto_responsable": "Responsable sintético",
    }
    modificados = {**antecedentes, "motivo_consulta": "Motivo sintético actualizado"}
    with TestClient(app) as cliente:
        primero = cliente.post(url + "/antecedentes", data=antecedentes, auth=admin)
        assert "Los antecedentes quedaron guardados." in primero.text
        for clave in antecedentes.keys() - {"csrf"}:
            assert antecedentes[clave] in primero.text
        anterior = cliente.post(url, auth=admin, data={
            "atencion_id": 1, "observaciones": "Primera evolución", "csrf": csrf,
            "pruebas_aplicadas": "Primera prueba",
        })
        assert "Primera evolución" in anterior.text
        assert cliente.post(url + "/antecedentes", data=modificados, auth=paciente).status_code == 403
        assert cliente.post(
            url + "/antecedentes", data={**modificados, "csrf": "inválido"}, auth=admin,
        ).status_code == 403
        assert "Motivo sintético inicial" in cliente.get(url, auth=admin).text
        assert "Los antecedentes quedaron guardados." in cliente.post(
            url + "/antecedentes", data=modificados, auth=admin,
        ).text
        segunda = cliente.post(url, auth=admin, data={
            "atencion_id": nueva, "observaciones": "Segunda evolución", "csrf": csrf,
        })
        assert segunda.status_code == 200
        ficha = cliente.get(url, auth=admin)
        assert ficha.headers["cache-control"] == "no-store"
        for texto in ("Motivo sintético actualizado", "Primera evolución", "Segunda evolución", "Primera prueba"):
            assert texto in ficha.text
        assert "Motivo sintético inicial" not in ficha.text
        assert "Historial de cambios (1 versión anterior)" in ficha.text
        assert "Motivo sintético actualizado" not in cliente.get("/psicologa/fichas/2", auth=admin).text

    evoluciones = conexion.execute(
        "SELECT atencion_id, observaciones, pruebas_aplicadas FROM registro_evolucion ORDER BY atencion_id"
    ).fetchall()
    descifrar = app.state.cifrador.descifrar
    assert [(f[0], descifrar(f[1]), descifrar(f[2])) for f in evoluciones] == [
        (1, "Primera evolución", "Primera prueba"), (nueva, "Segunda evolución", ""),
    ]
    eventos = conexion.execute(
        "SELECT rol, operacion, resultado FROM bitacora_clinica WHERE resultado = 'denegado'"
    ).fetchall()
    assert [tuple(fila) for fila in eventos] == [("Paciente", "escritura", "denegado")]

    # El antecedente reemplazado no se pierde: queda en el historial.
    historial = conexion.execute(
        "SELECT paciente_id, motivo_consulta FROM ficha_clinica_historial"
    ).fetchall()
    assert [(f[0], app.state.cifrador.descifrar(f[1])) for f in historial] == [(1, "Motivo sintético inicial")]
    assert historial[0][1].startswith(PREFIJO)


def test_guardar_antecedentes_sin_cambios_no_crea_versiones(base_temporal, conexion):
    cargar_datos_ejemplo(str(base_temporal))
    admin = ("psicologa", "clave-admin")
    app = crear_app(base_temporal, clave_psicologa_demo=admin[1], clave_paciente_demo="otra-clave")
    datos = {
        "csrf": app.state.csrf_psicologa_demo, "motivo_consulta": "Motivo sintético",
        "antecedentes_salud_mental": "", "diagnosticos": "", "medicamentos": "",
        "datos_adulto_responsable": "",
    }
    with TestClient(app) as cliente:
        for _ in range(3):
            cliente.post("/psicologa/fichas/1/antecedentes", data=datos, auth=admin)

    assert conexion.execute("SELECT COUNT(*) FROM ficha_clinica_historial").fetchone()[0] == 0


def test_ficha_cifrada_en_la_base_y_datos_planos_antiguos_se_cifran_al_arrancar(base_temporal, conexion):
    """RD-02: nada clínico queda legible en SQLite; lo antiguo se cifra al arrancar."""
    from app.servicios.cifrado import Cifrador, ClaveCifradoInvalida

    cargar_datos_ejemplo(str(base_temporal))
    # Dato antiguo en texto plano (anterior al cifrado).
    conexion.execute(
        "INSERT INTO ficha_clinica (paciente_id, motivo_consulta) VALUES (1, 'Motivo antiguo en claro')"
    )
    conexion.commit()

    app = crear_app(base_temporal, clave_psicologa_demo="clave-admin", clave_paciente_demo="otra")
    guardado = conexion.execute("SELECT motivo_consulta FROM ficha_clinica WHERE paciente_id = 1").fetchone()[0]
    assert guardado.startswith(PREFIJO) and "Motivo antiguo" not in guardado
    with TestClient(app) as cliente:
        assert "Motivo antiguo en claro" in cliente.get(
            "/psicologa/fichas/1", auth=("psicologa", "clave-admin")).text

    # Con otra clave no se puede leer ni mezclar datos: la app no arranca.
    otra = Cifrador.temporal()
    otra.persistente = True
    with pytest.raises(ClaveCifradoInvalida):
        crear_app(base_temporal, cifrador=otra)


def test_modo_con_cuentas_exige_clave_de_cifrado(base_temporal, monkeypatch):
    from app.servicios.cifrado import ClaveCifradoInvalida

    monkeypatch.delenv("CONSULTA_CLAVE_CIFRADO", raising=False)
    with pytest.raises(ClaveCifradoInvalida, match="requiere CONSULTA_CLAVE_CIFRADO"):
        crear_app(base_temporal, cuentas_persistentes=True)
