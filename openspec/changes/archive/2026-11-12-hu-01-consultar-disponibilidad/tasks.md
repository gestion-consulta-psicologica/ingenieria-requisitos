# Tasks

## 1. Estructura y dependencias

- [x] 1.1 Crear la estructura base (`app/`, `app/db/migrations/`, `app/dominio/`, `app/servicios/`, `app/rutas/`, `app/templates/`, `tests/`, `data/`) y verificar que existan las carpetas.
- [x] 1.2 Crear `requirements.txt` con FastAPI, Uvicorn, Jinja2, python-multipart, pytest y httpx; verificar que `pip install -r requirements.txt` termine sin errores en el entorno virtual.
- [x] 1.3 Crear `app/main.py` con la aplicación FastAPI y verificar que `TestClient(app)` responda sin errores de importación.

## 2. Base de datos y datos de ejemplo

- [x] 2.1 Crear la migración `app/db/migrations/001_crear_tablas_base.sql` con `psicologa`, `paciente`, `bloque_horario` y `reserva`, incluido el índice único parcial de reservas vigentes; verificar que el esquema creado contenga las tablas y el índice.
- [x] 2.2 Implementar `app/db/conexion.py` para abrir SQLite, aplicar migraciones en orden y registrar `schema_migrations`; verificar que al arrancar dos veces no se repitan migraciones.
- [x] 2.3 Implementar `app/db/seed.py` idempotente con una psicóloga, bloques de las semanas del 9 y 16 de noviembre y una reserva vigente para el martes 10 a las 10:00; verificar que ejecutarlo dos veces no duplique datos.

## 3. Lógica de consulta de disponibilidad

- [x] 3.1 Implementar el módulo de consulta que obtiene los bloques de una semana sin reserva vigente, usando la regla de EST-01; verificar con una prueba que excluya reservas Pendientes de confirmación y Confirmadas, y que incluya bloques con reservas Canceladas o Sin confirmar.
- [x] 3.2 Implementar el cálculo de la fecha del próximo bloque disponible como el mínimo de los bloques futuros sin reserva vigente; verificar con una prueba que devuelva la fecha correcta y `None` cuando no exista.
- [x] 3.3 Exponer `GET /disponibilidad?semana=AAAA-MM-DD` y `GET /` en FastAPI; verificar con `TestClient` que respondan 200 y que la semana omitida use la semana actual.

## 4. Pantalla de consulta

- [x] 4.1 Crear la plantilla Jinja2 de disponibilidad con los bloques libres agrupados por fecha y el mensaje de ausencia con la próxima fecha; verificar que el HTML renderizado muestre los bloques esperados y no muestre los ocupados.
- [x] 4.2 Agregar el selector de rol de demostración con el rol Paciente; verificar que la pantalla de disponibilidad sea accesible con ese rol y que el README advierta que no es autenticación real.

## 5. Pruebas de los escenarios Gherkin

- [x] 5.1 Crear la prueba `HU-01 · El paciente consulta una semana con bloques horarios libres` con datos propios; verificar que pase y que compruebe que se informa el bloque libre y no el bloque con reserva vigente.
- [x] 5.2 Crear la prueba `HU-01 · El paciente consulta una semana sin bloques horarios libres` con datos propios; verificar que pase y que compruebe el mensaje de ausencia y la fecha del próximo bloque disponible.
- [x] 5.3 Ejecutar `pytest` y verificar que todas las pruebas de la historia pasen.

## 6. Documentación

- [x] 6.1 Actualizar `README.md` con instalación, ejecución, pruebas, datos de ejemplo y recorrido manual de la consulta; verificar que los comandos documentados funcionen tal como están escritos.

## Workflow follow-up

- Archivar el cambio cuando el estudiante haya validado el sistema.
- Actualizar `.cin324/proyecto.md` con el estado final de HU-01.
