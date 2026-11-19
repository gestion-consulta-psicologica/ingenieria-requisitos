# Proposal — HU-02 Reservar una hora

## Why

El paciente ya puede consultar la disponibilidad (HU-01), pero todavía no puede reservar: la coordinación de la hora sigue dependiendo de WhatsApp y del registro manual en Excel. HU-02 cierra ese paso para que el paciente seleccione un bloque disponible y obtenga su reserva desde la plataforma.

## What Changes

- Agregar el flujo de reserva desde la consulta de disponibilidad: el Paciente elige un bloque, ingresa su RUT y confirma la reserva.
- Registrar la **Reserva** en estado **Pendiente de confirmación** solo si el bloque sigue disponible y el RUT está registrado.
- Actualizar la disponibilidad: el bloque reservado deja de mostrarse como disponible para otros pacientes.
- Enviar al Paciente el **aviso de reserva registrada** mediante el Servicio de mensajería (simulado).
- Rechazar la reserva si otro paciente tomó el bloque antes e informar los bloques disponibles más cercanos.
- Si el RUT no está registrado, no registrar la reserva y derivar a `/pacientes/registro`; la página de registro se implementa en **HU-02A**.
- **Historia:** HU-02 — Reservar una hora. **Actividad del TO-BE:** Seleccionar horario disponible + Registrar reserva automáticamente. **Caso de uso:** CU-02 — Reservar hora (incluye CU-01 Consultar disponibilidad; actor externo: Servicio de mensajería, simulado).

**Fuera de alcance:** registrar los datos del paciente (HU-02A / CU-11); enviar la solicitud de confirmación, confirmar o cancelar la hora y registrar el cargo por no confirmar (HU-03); reagendar o cancelar la reserva (HU-04); pagos, boletas, asistencia y ficha clínica (HU-05 a HU-09); autenticación real y requisitos no funcionales.

## Capabilities

### New Capabilities
- `reserva-hora`: registrar una reserva de un bloque horario disponible para un paciente registrado, actualizar la disponibilidad, avisar al paciente y manejar el bloque ya tomado o el RUT no registrado.

### Modified Capabilities
- Ninguna. `consulta-disponibilidad` mantiene sus requisitos; HU-02 solo reutiliza su lógica.

## Impact

- **Código nuevo:** `app/servicios/reserva.py`, `app/rutas/reserva.py`, `app/servicios/mensajeria.py` (adaptador simulado) y las plantillas `reserva.html` y `reserva_confirmada.html`.
- **Código modificado:** `app/main.py` (incluir el router), `app/templates/disponibilidad.html` (enlace para reservar cada bloque) y `README.md`.
- **Base de datos:** sin cambios de esquema; se reutilizan `paciente`, `bloque_horario` y `reserva` de la migración `001`. El índice único de reserva vigente de EST-01 evita dos reservas vigentes para el mismo bloque.
- **Sistemas externos:** Servicio de mensajería simulado mediante adaptador; no se envían mensajes reales.
- **Dependencia:** la derivación por RUT no registrado apunta a `/pacientes/registro`, que se implementa en HU-02A.
- **Pruebas:** una prueba por cada escenario Gherkin de HU-02.
