# Tasks - HU-04 Reagendar o cancelar una hora

## 1. Datos y migración

- [x] 1.1 Agregar `reserva.version` para identificar el ciclo de confirmación de cada reserva.
- [x] 1.2 Reconstruir `solicitud_confirmacion` con `version` y unicidad por `(reserva_id, version, tipo)`, conservando las filas, el índice único parcial de solicitud pendiente y las referencias de tokens y correos.
- [x] 1.3 Crear `reserva_historial` con las restricciones de coherencia para cancelación y reagendamiento.
- [x] 1.4 Verificar la migración `006` sobre una base con datos históricos y `PRAGMA foreign_key_check` sin errores.

## 2. Lógica de gestión

- [x] 2.1 Implementar `obtener_alternativas` con bloques libres de los próximos 14 días, excluyendo el bloque actual y los estados vigentes.
- [x] 2.2 Implementar `cancelar_reserva` en una transacción `BEGIN IMMEDIATE`, con transición desde **Confirmada**, liberación del bloque e historial.
- [x] 2.3 Implementar `reagendar_reserva` en una transacción `BEGIN IMMEDIATE`, actualizando la misma reserva, liberando el bloque anterior, incrementando la versión, registrando historial y encolando el aviso.
- [x] 2.4 Rechazar reservas no confirmadas, bloques inexistentes, bloque actual y bloques tomados, conservando la reserva original.
- [x] 2.5 Adaptar `confirmacion.py` y el planificador para consultar solicitudes por la versión actual de la reserva.
- [x] 2.6 Agregar el aviso de reserva reagendada con fecha anterior, fecha nueva y número de reserva.

## 3. Rutas y pantallas

- [x] 3.1 Mostrar **Reagendar hora** y **Cancelar reserva** solo en reservas confirmadas.
- [x] 3.2 Agregar `GET/POST /reservas/{id}/reagendar` y `POST /reservas/{id}/cancelar` con redirección al detalle y errores 404/409.
- [x] 3.3 Crear `reagendar.html` con alternativas, confirmación por bloque y mensaje cuando no hay alternativas.
- [x] 3.4 Mostrar el historial de cambios y el ciclo de las solicitudes en el detalle de la reserva.

## 4. Pruebas

- [x] 4.1 Probar cancelación confirmada, liberación del bloque, historial y rechazo desde una reserva pendiente.
- [x] 4.2 Probar alternativas y ausencia de alternativas sin modificar la reserva original.
- [x] 4.3 Probar reagendamiento exitoso, bloque tomado, mismo bloque y nuevo ciclo de confirmación.
- [x] 4.4 Probar las rutas y pantallas de reagendamiento y cancelación.
- [x] 4.5 Ejecutar la suite completa y confirmar que las pruebas anteriores siguen pasando.

## 5. Documentación y cierre

- [x] 5.1 Alinear la numeración de `07-criterios-aceptacion.md` con `04-historias-usuario.md`, dejando la selección de nueva hora dentro de HU-04.
- [x] 5.2 Actualizar `08-modelo-dominio.md`, `10-diagramas-secuencia.md`, `11-diagramas-estado.md` y `12-trazabilidad.md` con DSS-04, el historial y el nuevo ciclo.
- [x] 5.3 Crear y exportar `diagramas/dss-04.puml/png`; actualizar `est-01.puml/png`.
- [x] 5.4 Actualizar `README.md`, `.cin324/proyecto.md`, `.cin324/historias/HU-04.md` y la propuesta OpenSpec.
- [x] 5.5 Ejecutar `openspec validate hu-04-reagendar-cancelar-hora --strict`, `git diff --check` y verificar el hash de `data/app.db` (`97E01B0E05CA75E8C42D62755D32779AA36D304A6B980CC47DA5AD83A3E60B29`, sin cambios).
