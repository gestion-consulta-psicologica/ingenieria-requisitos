# Proposal — HU-02A Registrar datos del paciente

## Why

HU-02 ya deriva a `/pacientes/registro` cuando el RUT no está registrado, pero esa página todavía no existe: el paciente no puede completar su registro ni retomar la reserva. HU-02A cierra ese hueco para que un paciente nuevo se registre desde el flujo de reserva y el bloque seleccionado no se pierda.

## What Changes

- Crear la página `/pacientes/registro` con un formulario de nombre completo, RUT y medio de contacto (teléfono o correo).
- Registrar un **Paciente** nuevo si el RUT no existe; si el RUT ya existe, reutilizar el registro existente sin duplicarlo.
- Exigir nombre completo, RUT y al menos uno de teléfono o correo; si faltan datos, no registrar y volver al formulario indicando qué falta.
- Al registrarse correctamente desde HU-02, redirigir con `303` a `/reservar/<bloque_id>?rut=<rut>` con el RUT precargado para que el paciente confirme la reserva; si no viene `bloque_id`, mostrar una confirmación de registro.
- Agregar la migración `002` para que `paciente.correo` sea opcional, porque el paciente puede registrarse solo con teléfono; la regla de «al menos un contacto» queda en la aplicación.
- Aceptar el parámetro `rut` en `GET /reservar/<bloque_id>` para precargar el campo del formulario de reserva.
- Agregar pruebas automáticas para los tres escenarios Gherkin de HU-02A.
- **Historia:** HU-02A — Registrar datos del paciente. **Actividad del TO-BE:** Registrar datos del paciente. **Caso de uso:** CU-11 — Registrar datos del paciente (extiende CU-02 Reservar hora cuando el RUT no está registrado; actor principal: Paciente; sin actores externos).

**Fuera de alcance:** crear la reserva (HU-02 / CU-02); confirmar, cancelar o reagendar reservas (HU-03 y HU-04); editar o eliminar datos del paciente; autenticación real; ficha clínica (HU-09); requisitos no funcionales.

## Capabilities

### New Capabilities
- `registro-paciente`: registrar los datos personales de un Paciente desde el flujo de reserva, reutilizar el registro cuando el RUT ya existe, validar los datos obligatorios y retomar la reserva del bloque seleccionado.

### Modified Capabilities
- Ninguna. `reserva-hora` y `consulta-disponibilidad` mantienen sus requisitos; HU-02A solo agrega la página de registro y la precarga del RUT en el formulario de reserva.

## Impact

- **Código nuevo:** `app/servicios/paciente.py`, `app/rutas/paciente.py`, las plantillas `registro_paciente.html` y `registro_confirmado.html`.
- **Código modificado:** `app/main.py` (incluir el router), `app/rutas/reserva.py` (`GET /reservar/{id}` acepta `?rut=`), `README.md`.
- **Base de datos:** migración `002_paciente_correo_opcional.sql` para reconstruir `paciente` con `correo` opcional; se conserva la unicidad del RUT.
- **Sistemas externos:** ninguno.
- **Pruebas:** una prueba por cada escenario Gherkin de HU-02A, más pruebas unitarias de normalización y validación de datos.
