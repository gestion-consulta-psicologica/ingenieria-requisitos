# Cambios de la entrega Evaluacion2 — HU-10

## Decisión funcional y alcance

Al aceptar la derivación, el médico psiquiatra pasa a ser responsable de la reserva original. Hasta ese momento, la reserva sigue su ciclo con la psicóloga. Un rechazo conserva el bloque original. Una cancelación, confirmación previa, vencimiento o cambio de ciclo impide transferir la solicitud.

El bloque de destino debe pertenecer al destinatario activo y verificado, estar libre y coincidir en fecha, inicio, término y modalidad. Conservar el horario evita cambiar la cita que eligió el paciente. La agenda de psiquiatría se gestiona desde la bandeja privada. La reserva transferida conserva ID, paciente, fecha de registro e historial y sigue pendiente de confirmación en un ciclo nuevo.

La aceptación serializa las escrituras de SQLite y registra actualización de reserva, cambio de bloque, cierre de solicitudes anteriores y aviso en una transacción. La confirmación valida el ciclo antes de crear una solicitud. El aviso por correo deja el nombre del profesional para el detalle autenticado. El historial distingue las derivaciones anteriores a 021, que se preservan sin transferencias retroactivas. Se corrigió la bitácora para registrar intentos sobre pacientes inexistentes con referencia nula.

La emisión de boletas de HU-07 sigue pendiente. Para psiquiatría falta especificar gestión de la atención, asistencia y cobro. El planificador conserva las reglas de atención y cobro para psicología.

## Implementación y archivos

| Área | Archivos | Cambios |
|---|---|---|
| Datos | `app/db/migrations/021_transferencia_psiquiatria.sql`, `app/db/derivaciones.py` | Bloques con un solo profesional, derivaciones por ciclo, historial de origen y destino y control de duplicados. Se conservan los datos de los esquemas anteriores. |
| Rutas | `app/rutas/derivaciones.py`, `app/rutas/reserva.py`, `app/rutas/clinica.py` | Agenda y respuesta por titularidad, validación del formulario, ocultamiento de agenda privada y bitácora para referencias inexistentes. |
| Servicios | `app/servicios/derivaciones.py`, `disponibilidad.py`, `reserva.py`, `reagendamiento.py`, `confirmacion.py`, `atenciones.py`, `plantillas_correo.py`, todos bajo `app/servicios/` | Transferencia transaccional, disponibilidad por profesional, historial, ciclo de confirmación y aviso. Las atenciones y cobros psicológicos conservan su alcance. |
| Interfaz | `app/templates/derivaciones.html`, `app/templates/psicologa.html`, `app/templates/reserva_confirmada.html` | Selector con horario compatible, bandeja, agenda, rechazo, mensajes de conflicto y responsable visible para el paciente. |
| Pruebas | `tests/test_hu10_derivaciones.py` | Reserva creada desde la web, aceptación, rechazo, inactividad, ocupación, cancelación, concurrencia, permisos, migraciones y reinicio. |

## Artefactos de requisitos

| Artefacto | Cambio |
|---|---|
| TO-BE y requisitos | `02-rediseno-to-be.md` y `03-requisitos.md` incorporan la actividad y RP-27. El flujo gráfico de Evaluación 3 está en DSS-06. |
| Historia y Gherkin | `04-historias-usuario.md`, `07-criterios-aceptacion.md` y `.cin324/historias/HU-10.md` documentan CA1–CA8 y ocho escenarios. |
| Modelo de dominio | `08-modelo-dominio.md` y `diagramas/modelo-dominio.puml/.png` incorporan CuentaPsiquiatra, Derivación y la pertenencia exclusiva de cada bloque. |
| Casos de uso | `09-casos-de-uso.md` y `diagramas/casos-de-uso.puml/.png` incorporan al médico psiquiatra y CU-13. |
| Secuencia | `10-diagramas-secuencia.md` y `diagramas/dss-06.puml/.png` muestran los caminos sin derivación, rechazo, aceptación y conflicto. |
| Estados | `11-diagramas-estado.md`, `diagramas/est-01.puml/.png` y `diagramas/est-05.puml/.png` reflejan la transferencia y el ciclo de Derivación. |
| Trazabilidad y demostración | `12-trazabilidad.md`, `openspec/specs/derivacion-psiquiatria/spec.md` y `README.md` enlazan artefactos, código, pruebas y arranque operativo. |

## Validación

- HU-10 con `pytest -v tests/test_hu10_derivaciones.py` — 18 aprobadas y una advertencia de deprecación de Starlette.
- Suite completa con `pytest` en `Evaluacion2` — 198 aprobadas, cero fallos y una advertencia. Los resultados y la reconciliación de artefactos constan en [HU10-VALIDACION-FINAL.md](./HU10-VALIDACION-FINAL.md).
- Migración desde 018, 019 y 020 — comparación de datos históricos, sesiones, tokens y cuentas. `PRAGMA foreign_key_check` limpio.
- CIN324 — se siguieron los procedimientos de auditoría y validación del repositorio de forma local. Se revisaron la trazabilidad, los ocho escenarios Gherkin, la estructura de OpenSpec y cinco fuentes PlantUML y sus PNG. Los dos BPMN históricos se pudieron leer. El ejecutor de comandos slash de OpenCode no está disponible en este entorno.
- Pendiente de aprobación académica — recorrido manual del evaluador en navegador. Ver [la guía de demostración](./README.md#demostrar-hu-10--transferencia-a-psiquiatría).
