# Proposal

## Why

La historia **HU-01 — Consultar disponibilidad** busca que el paciente conozca las horas disponibles sin depender de la coordinación manual por WhatsApp. Hoy la disponibilidad se revisa en Excel y se informa por mensajería, lo que genera demoras y errores. Este cambio implementa la actividad del TO-BE **Consultar disponibilidad en plataforma** y el caso de uso **CU-01 — Consultar disponibilidad**.

## What Changes

- Agregar una consulta semanal de disponibilidad para el rol **Paciente**.
- Mostrar únicamente los bloques horarios que no tienen una reserva vigente.
- Ocultar los bloques ocupados por reservas en estado **Pendiente de confirmación** o **Confirmada**.
- Informar cuando no hay horas disponibles en la semana consultada e indicar la fecha del próximo bloque disponible.
- Incorporar datos de ejemplo de **Psicologa**, **BloqueHorario** y **Reserva** para poder probar la consulta.
- No se modifica el estado de ninguna reserva: esta historia es de solo lectura.
- **Fuera de alcance:** reservar un bloque, registrar reservas, enviar avisos, confirmar o cancelar horas, reagendar, pagos, boletas, asistencia y ficha clínica.

## Capabilities

### New Capabilities
- `consulta-disponibilidad`: consulta de la disponibilidad semanal de bloques horarios de la psicóloga, excluyendo los bloques con reserva vigente y mostrando la próxima fecha disponible cuando no hay alternativas.

### Modified Capabilities
- Ninguna.

## Impact

- Nuevas rutas y pantallas para consultar la disponibilidad semanal y el mensaje de ausencia de horas.
- Tablas SQLite para **Psicologa**, **BloqueHorario** y **Reserva**, con datos de ejemplo.
- Pruebas automáticas para los escenarios Gherkin de HU-01.
- No participan sistemas externos ni se implementan requisitos no funcionales.
