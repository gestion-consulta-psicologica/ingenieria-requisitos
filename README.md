# Gestión de consulta psicológica

Aplicación web sencilla del curso **CIN 324 — Ingeniería de Requisitos**, generada desde la documentación del repositorio. En esta primera historia se implementa **HU-01 — Consultar disponibilidad**: el paciente consulta los bloques horarios libres de una semana y, si no hay horas, el sistema informa la próxima fecha disponible.

## Requisitos

- Python 3.11 o superior (probado con Python 3.12).
- SQLite (incluido con Python).
- Git.
- OpenSpec es opcional para ejecutar la aplicación; se usa para gestionar las especificaciones del cambio.

## Instalación

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si `python` no se reconoce en la terminal, usa el ejecutable instalado o el Python del entorno virtual:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, puedes usar directamente `.\.venv\Scripts\python.exe` en los comandos siguientes.

## Datos de ejemplo

```powershell
python -m app.db.seed
```

El comando crea `data/app.db` (si no existe), aplica las migraciones y carga datos de ejemplo de forma idempotente:

- Psicóloga **Ana Pérez**.
- Semana del **9 de noviembre de 2026**:
  - martes 10 a las 10:00: reserva vigente en estado **Pendiente de confirmación** (no debe mostrarse).
  - martes 10 a las 11:00: bloque libre (debe mostrarse).
- Semana del **16 de noviembre de 2026**:
  - martes 17 a las 10:00: reserva vigente en estado **Confirmada** (no debe mostrarse).
  - no hay otros bloques esa semana.
  - lunes 24 a las 10:00: próximo bloque libre, en modalidad online.

Ejecutar el seed varias veces no duplica los datos.

## Ejecutar la aplicación

Con el entorno virtual activado:

```powershell
uvicorn app.main:app --reload
```

También puedes ejecutarlo sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abre <http://localhost:8000/disponibilidad>.

La raíz <http://localhost:8000/> redirige a la consulta de disponibilidad.

## Recorrido manual de HU-01

1. Abre <http://localhost:8000/disponibilidad?semana=2026-11-09>.
   - Debes ver el bloque del **martes 10 de noviembre a las 11:00** como disponible.
   - **No** debe aparecer el bloque de las 10:00, porque tiene una reserva vigente.
2. Abre <http://localhost:8000/disponibilidad?semana=2026-11-16>.
   - Debes ver el mensaje **«No hay horas disponibles para esa semana.»**
   - Debes ver que la fecha del próximo bloque disponible es el **24 de noviembre de 2026**.
3. Cambia la fecha del formulario y pulsa **Consultar** para repetir la consulta con otra semana.

El selector de rol de la cabecera es **solo de demostración**: no hay autenticación real. En esta historia se usa el rol **Paciente**.

## Pruebas

```powershell
pytest
```

o, sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Las pruebas cubren:

- `HU-01 · El paciente consulta una semana con bloques horarios libres`.
- `HU-01 · El paciente consulta una semana sin bloques horarios libres`.
- La regla de vigencia de EST-01 (Pendiente de confirmación y Confirmada bloquean; Cancelada y Sin confirmar no).
- El cálculo del próximo bloque disponible cuando no hay alternativas.
- La redirección de `/` a `/disponibilidad` y la consulta sin parámetro de semana.

## Estructura

```text
app/
  main.py                  # aplicación FastAPI y filtros de fechas
  db/
    conexion.py            # SQLite y migraciones
    migrations/            # migraciones SQL numeradas
    seed.py                # datos de ejemplo idempotentes
  servicios/
    disponibilidad.py      # lógica de consulta y regla de vigencia
  rutas/
    disponibilidad.py      # GET /disponibilidad
  templates/
    disponibilidad.html    # pantalla de consulta
tests/
  test_hu01_disponibilidad.py
data/app.db                # base local (se crea con el seed)
```

## Fuera de alcance

Esta historia es de solo lectura. No se implementan reservas, avisos, confirmación o cancelación, reagendamiento, pagos, boletas, asistencia, ficha clínica, autenticación real ni requisitos no funcionales. Tampoco participan sistemas externos.
