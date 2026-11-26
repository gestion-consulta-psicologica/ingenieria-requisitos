import sqlite3
from secrets import compare_digest

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasicCredentials

from app.rutas.disponibilidad import obtener_conexion
from app.rutas.psicologa import autenticacion, verificar_formulario_psicologa
from app.servicios.cifrado import ClaveCifradoInvalida

router = APIRouter(prefix="/psicologa/fichas")
CAMPOS_ANTECEDENTES = (
    ("motivo_consulta", "Motivo de consulta"),
    ("antecedentes_salud_mental", "Antecedentes de salud mental"),
    ("diagnosticos", "Diagnósticos"),
    ("medicamentos", "Medicamentos"),
    ("datos_adulto_responsable", "Datos del adulto responsable y convivientes"),
)


def registrar_acceso(conexion, rol, operacion, resultado, paciente_id=None, usuario=None):
    """Bitácora sin contenido clínico: rol, usuario, ficha, operación y resultado."""
    conexion.execute(
        """
        INSERT INTO bitacora_clinica (rol, operacion, resultado, paciente_id, usuario)
        VALUES (?, ?, ?, ?, ?)
        """,
        (rol, operacion, resultado, paciente_id, usuario),
    )


def _ficha_solicitada(request: Request) -> int | None:
    valor = request.path_params.get("paciente_id")
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def autorizar_ficha(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
    credenciales: HTTPBasicCredentials | None = Depends(autenticacion),
):
    paciente_id = _ficha_solicitada(request)
    operacion = "lectura" if request.method == "GET" else "escritura"
    if paciente_id is not None and (
        not 1 <= paciente_id <= 2**63 - 1
        or conexion.execute("SELECT 1 FROM paciente WHERE id = ?", (paciente_id,)).fetchone() is None
    ):
        paciente_id = None
    if request.app.state.cuentas_persistentes:
        cuenta = request.state.cuenta
        usuario = f"cuenta:{cuenta['id']}" if cuenta else None
        if cuenta and cuenta["rol"] == "psicologa":
            request.state.usuario_clinico = usuario
            return
        registrar_acceso(
            conexion, {"paciente": "Paciente", "psiquiatra": "Psiquiatra"}.get(cuenta["rol"]) if cuenta else None,
            operacion, "denegado",
            paciente_id, usuario,
        )
        conexion.commit()
        raise HTTPException(403 if cuenta else 401, detail="Acceso denegado.")
    claves = {
        "psicologa": (request.app.state.clave_psicologa_demo, "Psicóloga"),
        "paciente": (request.app.state.clave_paciente_demo, "Paciente"),
    }
    if not all(clave for clave, _ in claves.values()):
        raise HTTPException(404)
    clave, rol = claves.get(credenciales.username, (None, None)) if credenciales else (None, None)
    if clave is None or not compare_digest(clave.encode(), credenciales.password.encode()):
        rol = None
    usuario = credenciales.username if rol else None

    if rol == "Psicóloga":
        request.state.usuario_clinico = usuario
        return
    registrar_acceso(conexion, rol, operacion, "denegado", paciente_id, usuario)
    conexion.commit()
    if rol is None:
        raise HTTPException(401, headers={"WWW-Authenticate": 'Basic realm="Psicologa"'})
    raise HTTPException(403, detail="Acceso denegado.")


@router.get("/{paciente_id}", response_class=HTMLResponse, dependencies=[Depends(autorizar_ficha)])
def ficha(
    paciente_id: int, request: Request,
    antecedentes_guardados: bool = False,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    paciente = conexion.execute(
        "SELECT nombre_completo FROM paciente WHERE id = ?", (paciente_id,),
    ).fetchone()
    if paciente is None:
        raise HTTPException(404)
    antecedentes = conexion.execute(
        "SELECT * FROM ficha_clinica WHERE paciente_id = ?", (paciente_id,),
    ).fetchone()
    atenciones = conexion.execute(
        """
        SELECT a.id, b.fecha, e.observaciones, e.pruebas_aplicadas
        FROM atencion a
        JOIN reserva r ON r.id = a.reserva_id
        JOIN bloque_horario b ON b.id = r.bloque_horario_id
        LEFT JOIN registro_evolucion e ON e.atencion_id = a.id
        WHERE r.paciente_id = ? AND a.estado = 'realizada'
        ORDER BY b.fecha DESC, b.hora_inicio DESC, a.id DESC
        """,
        (paciente_id,),
    ).fetchall()
    cifrador = request.app.state.cifrador
    try:
        if antecedentes is not None:
            antecedentes = {
                "fecha_apertura": antecedentes["fecha_apertura"],
                **{clave: cifrador.descifrar(antecedentes[clave]) for clave, _ in CAMPOS_ANTECEDENTES},
            }
        atenciones = [
            {
                "id": fila["id"], "fecha": fila["fecha"],
                "observaciones": cifrador.descifrar(fila["observaciones"]),
                "pruebas_aplicadas": cifrador.descifrar(fila["pruebas_aplicadas"]),
            }
            for fila in atenciones
        ]
    except ClaveCifradoInvalida as error:
        raise HTTPException(500, detail=str(error)) from error
    versiones_anteriores = conexion.execute(
        """
        SELECT fecha_reemplazo FROM ficha_clinica_historial
        WHERE paciente_id = ? ORDER BY id DESC
        """,
        (paciente_id,),
    ).fetchall()
    registrar_acceso(
        conexion, "Psicóloga", "lectura", "permitido",
        paciente_id, request.state.usuario_clinico,
    )
    conexion.commit()
    return request.app.state.templates.TemplateResponse(
        request=request, name="ficha_clinica.html",
        context={
            "paciente": paciente, "paciente_id": paciente_id, "atenciones": atenciones,
            "versiones_anteriores": versiones_anteriores,
            "antecedentes": antecedentes, "campos_antecedentes": CAMPOS_ANTECEDENTES,
            "antecedentes_guardados": antecedentes_guardados and antecedentes is not None,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/{paciente_id}/antecedentes", dependencies=[Depends(autorizar_ficha)])
def guardar_antecedentes(
    paciente_id: int, request: Request,
    csrf: str = Form(),
    motivo_consulta: str = Form(default=""),
    antecedentes_salud_mental: str = Form(default=""),
    diagnosticos: str = Form(default=""),
    medicamentos: str = Form(default=""),
    datos_adulto_responsable: str = Form(default=""),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    valores = (
        motivo_consulta.strip(), antecedentes_salud_mental.strip(),
        diagnosticos.strip(), medicamentos.strip(), datos_adulto_responsable.strip(),
    )
    cifrador = request.app.state.cifrador
    campos = [clave for clave, _ in CAMPOS_ANTECEDENTES]
    conexion.execute("BEGIN IMMEDIATE")
    try:
        actual = conexion.execute(
            f"SELECT {', '.join(campos)} FROM ficha_clinica WHERE paciente_id = ?",
            (paciente_id,),
        ).fetchone()
        try:
            anteriores = tuple(cifrador.descifrar(actual[c]) for c in campos) if actual else None
        except ClaveCifradoInvalida as error:
            raise HTTPException(500, detail=str(error)) from error
        if anteriores == valores:
            # Guardado sin cambios: no se crea una versión nueva ni se reescribe.
            registrar_acceso(
                conexion, "Psicóloga", "escritura", "permitido",
                paciente_id, request.state.usuario_clinico,
            )
            conexion.commit()
            return RedirectResponse(
                f"/psicologa/fichas/{paciente_id}?antecedentes_guardados=1#antecedentes",
                status_code=303,
            )
        if anteriores is not None and any(anteriores):
            # Se conserva la versión anterior (cifrada) antes de reemplazarla.
            conexion.execute(
                f"""
                INSERT INTO ficha_clinica_historial (paciente_id, {', '.join(campos)})
                VALUES (?, {', '.join('?' for _ in campos)})
                """,
                (paciente_id, *(cifrador.cifrar(v) for v in anteriores)),
            )
        resultado = conexion.execute(
            """
            INSERT INTO ficha_clinica (
                paciente_id, motivo_consulta, antecedentes_salud_mental,
                diagnosticos, medicamentos, datos_adulto_responsable
            )
            SELECT id, ?, ?, ?, ?, ? FROM paciente WHERE id = ?
            ON CONFLICT (paciente_id) DO UPDATE SET
                motivo_consulta = excluded.motivo_consulta,
                antecedentes_salud_mental = excluded.antecedentes_salud_mental,
                diagnosticos = excluded.diagnosticos,
                medicamentos = excluded.medicamentos,
                datos_adulto_responsable = excluded.datos_adulto_responsable
            """,
            (*(cifrador.cifrar(v) for v in valores), paciente_id),
        )
        if not resultado.rowcount:
            raise HTTPException(404)
        registrar_acceso(
            conexion, "Psicóloga", "escritura", "permitido",
            paciente_id, request.state.usuario_clinico,
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    return RedirectResponse(
        f"/psicologa/fichas/{paciente_id}?antecedentes_guardados=1#antecedentes",
        status_code=303,
    )


@router.post("/{paciente_id}", dependencies=[Depends(autorizar_ficha)])
def guardar_evolucion(
    paciente_id: int, request: Request,
    atencion_id: int = Form(), observaciones: str = Form(),
    pruebas_aplicadas: str = Form(default=""), csrf: str = Form(),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    verificar_formulario_psicologa(request, csrf)
    observaciones = observaciones.strip()
    if not observaciones:
        raise HTTPException(400, detail="Ingresa las observaciones de evolución.")
    conexion.execute("BEGIN IMMEDIATE")
    try:
        atencion = conexion.execute(
            """
            SELECT 1 FROM atencion a JOIN reserva r ON r.id = a.reserva_id
            WHERE a.id = ? AND r.paciente_id = ? AND a.estado = 'realizada'
            """,
            (atencion_id, paciente_id),
        ).fetchone()
        if atencion is None:
            raise HTTPException(409, detail="Selecciona una atención realizada de este paciente.")
        conexion.execute(
            "INSERT INTO ficha_clinica (paciente_id) VALUES (?) ON CONFLICT DO NOTHING",
            (paciente_id,),
        )
        resultado = conexion.execute(
            """
            INSERT INTO registro_evolucion
                (atencion_id, paciente_id, observaciones, pruebas_aplicadas)
            VALUES (?, ?, ?, ?) ON CONFLICT (atencion_id) DO NOTHING
            """,
            (
                atencion_id, paciente_id,
                request.app.state.cifrador.cifrar(observaciones),
                request.app.state.cifrador.cifrar(pruebas_aplicadas.strip()),
            ),
        )
        if not resultado.rowcount:
            raise HTTPException(409, detail="La atención ya tiene una evolución registrada.")
        registrar_acceso(
            conexion, "Psicóloga", "escritura", "permitido",
            paciente_id, request.state.usuario_clinico,
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    return RedirectResponse(f"/psicologa/fichas/{paciente_id}#evolucion-{atencion_id}", status_code=303)
