# Proposal - HU-04 Reagendar o cancelar una hora

## Why

El paciente ya puede reservar y confirmar una hora, pero todavía no puede cancelarla ni cambiarla desde la plataforma. HU-04 agrega la gestión posterior de una reserva confirmada: cancelar y liberar el bloque, consultar alternativas de los próximos 14 días, seleccionar un nuevo horario y actualizar la misma reserva, conservando el bloque anterior en el historial y reiniciando el ciclo de confirmación.

## What Changes

- Mostrar en `/reservas/{id}` las acciones **Reagendar hora** y **Cancelar reserva** cuando la reserva está en estado **Confirmada**.
- Implementar `POST /reservas/{id}/cancelar`: la reserva pasa a **Cancelada**, el bloque se libera y se registra el cambio en el historial.
- Implementar `GET /reservas/{id}/reagendar`: consulta y muestra bloques libres de los próximos 14 días, excluyendo el bloque actual y los ocupados.
- Implementar `POST /reservas/{id}/reagendar` con `bloque_id`: actualiza la misma reserva al nuevo bloque, la deja en **Pendiente de confirmación**, libera el bloque anterior, registra el historial e inicia un nuevo ciclo de solicitudes.
- Rechazar el reagendamiento si el bloque fue tomado, si no existe o si la reserva no está confirmada; en esos casos la reserva original no cambia.
- Encolar por correo el aviso de reserva reagendada, con la fecha anterior y la nueva.
- Agregar la migración `006_reagendamiento_cancelacion.sql` con la versión de la reserva, el ciclo de las solicitudes, el historial de cambios y las restricciones de integridad necesarias.
- Mantener una sola solicitud pendiente por reserva y permitir un nuevo ciclo de víspera/recordatorio después de cada reagendamiento.
- Mantener coherentes HU-04, Gherkin, requisitos, casos de uso, EST-01, DSS-04, trazabilidad y README.

**Fuera de alcance:** pagos, comprobantes, boletas, ficha clínica, autenticación real, agenda de la psicóloga, cancelación de reservas pendientes de confirmación (esa cancelación sigue en HU-03) y cálculo de cargos por cancelación no definidos en los requisitos.

## Capabilities

### New Capabilities

- `reagendamiento-cancelacion`: gestión de una reserva confirmada, consulta de alternativas, cancelación, reagendamiento transaccional, historial de cambios y nuevo ciclo de confirmación.

### Modified Capabilities

- `confirmacion-asistencia`: las solicitudes ahora pertenecen a un ciclo de la reserva; el reagendamiento inicia un ciclo nuevo sin borrar el historial del anterior.
- `reserva-hora`: la reserva conserva su identidad al reagendar y libera el bloque anterior.

## Impact

- **Código:** `app/servicios/reagendamiento.py`, `app/servicios/confirmacion.py`, `app/servicios/planificador.py`, `app/servicios/reserva.py`, `app/servicios/plantillas_correo.py`, `app/rutas/reserva.py`, `app/templates/reserva_confirmada.html`, `app/templates/reagendar.html`.
- **Base de datos:** migración `006` con `reserva.version`, `solicitud_confirmacion.version`, `reserva_historial` y la reconstrucción de `solicitud_confirmacion` para eliminar la unicidad por tipo y permitir ciclos. No se modifica `data/app.db` durante el desarrollo.
- **Pruebas:** `tests/test_hu04_reagendamiento.py` y la suite existente con base temporal aislada.
- **Documentación:** `04-historias-usuario.md`, `07-criterios-aceptacion.md`, `08-modelo-dominio.md`, `10-diagramas-secuencia.md`, `11-diagramas-estado.md`, `12-trazabilidad.md`, `README.md`, `.cin324/proyecto.md`, `.cin324/historias/HU-04.md`, `diagramas/dss-04.puml`, `diagramas/dss-04.png` y `diagramas/est-01.puml/png`.
- **Trazabilidad:** HU-04, CU-04, CU-05, RP-07 a RP-11, DSS-04 y EST-01.
