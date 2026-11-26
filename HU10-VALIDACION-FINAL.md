# HU-10 — Validación final en Evaluacion2

Validación realizada el 26 de noviembre de 2026 sobre `Evaluacion2`, después de integrar `main` con el commit local `d489b5d`. La suite se ejecutó desde el directorio de trabajo integrado.

## Decisiones y comportamiento verificado

- La psicóloga recibe en el panel las reservas pendientes. Puede mantener la cita con ella o derivarla a un psiquiatra activo y verificado con un bloque propio libre de la misma fecha, inicio, término y modalidad.
- El psiquiatra publica sus bloques en su agenda privada. Puede aceptar o rechazar las derivaciones que le pertenecen. Si se rechaza o queda sin respuesta, el bloque de la reserva no cambia.
- Una aceptación vigente cambia el bloque de la reserva original dentro de una transacción. Conserva ID, paciente, fecha de registro e historial. Libera el bloque de psicología, incrementa la versión y deja la cita pendiente de confirmación con psiquiatría. El detalle de paciente muestra el cambio de responsable y de ciclo.
- La aceptación vuelve a comprobar cuenta, bloque, estado y versión. Una reserva cancelada no se transfiere. Dos aceptaciones concurrentes producen un éxito y un conflicto, con un solo traslado.
- El acceso es por rol y titularidad. La agenda privada no se ofrece para reservas públicas. Las derivaciones no conceden acceso a fichas clínicas. La bitácora de un paciente inexistente registra la denegación con referencia nula.

## Datos y trazabilidad

La migración [021](./app/db/migrations/021_transferencia_psiquiatria.sql) incorpora bloques de psiquiatra y registra los bloques de origen y destino. Conserva los datos de las derivaciones previas como historial, sin ejecutar traslados retroactivos. Las pruebas pasan desde las versiones 018, 019 y 020, comparan cuentas, sesiones, tokens y registros históricos y comprueban `PRAGMA foreign_key_check`.

La implementación sigue **RP-27 → HU-10 CA1–CA8 → CU-13 → DSS-06 y EST-01/EST-05 → código y pruebas**. Se comprobaron ocho escenarios Gherkin vigentes y la estructura de OpenSpec, con tres requisitos y ocho escenarios. La redacción inicial de HU-10 y sus criterios permanecen en `04` y `07` como antecedentes. La regla vigente sitúa la transferencia después de la aceptación del destinatario y antes del nuevo ciclo de confirmación del paciente.

El [Draw.io original de Evaluacion2](./diagramas/casosdeusonuevo.drawio.png) coincide byte a byte con el archivo de la rama antes del merge. El diagrama PlantUML de casos de uso añade CU-13. Se verificaron las 14 fuentes PlantUML y sus PNG mediante una nueva exportación y comparación de SHA-256. El [TO-BE textual y su extensión gráfica](./02-rediseno-to-be.md) muestran el flujo de transferencia. El BPMN base y su imagen conservan el proceso original.

## Pruebas ejecutadas

| Comando en la rama integrada | Resultado | Duración |
|---|---|---|
| `pytest -v tests/test_hu10_derivaciones.py` | 18 aprobadas, 0 fallos, 1 advertencia | 32,85 s |
| `pytest` | 198 aprobadas, 0 fallos, 1 advertencia | 150,86 s |

Se usó Python portátil 3.11.9 con pytest 8.4.2 y las dependencias del proyecto. La advertencia de ambas corridas es la deprecación de `httpx` para `starlette.testclient`. La [prueba web](./tests/test_hu10_derivaciones.py) cubre reserva, selección, aceptación, transferencia sin duplicar, nuevo ciclo e historial después de reiniciar. Los casos adicionales cubren rechazo, cancelación, ocupación, inactividad, permisos, migración y concurrencia.

## Demostración manual

Usar una base aislada y cuentas persistentes por HTTPS. Seguir el [arranque operativo y los ocho pasos del README](./README.md#demostrar-hu-10--transferencia-a-psiquiatría) con tres sesiones separadas.

1. Crear un bloque futuro como psicóloga y registrar al psiquiatra.
2. Publicar un bloque equivalente desde la cuenta del psiquiatra.
3. Reservar con la psicóloga como paciente y anotar el ID.
4. Abrir el panel de la psicóloga y derivar la cita pendiente.
5. Aceptar y transferir desde la bandeja del psiquiatra.
6. Comparar la reserva original, el nuevo profesional y la disponibilidad del bloque liberado.
7. Verificar el nuevo ciclo de confirmación con planificador y SMTP configurados y comprobar que una solicitud anterior ya no admita respuestas.
8. Abrir **Historial de cambios** y reiniciar con la misma base para comprobar la conservación de datos.

## Pendientes conocidos

Queda pendiente el recorrido manual en un navegador con las cuentas de evaluación. El alcance implementado llega a transferencia y confirmación de la reserva. La atención, asistencia y facturación psiquiátricas y la emisión de boletas requieren reglas adicionales. La demo sin cuentas deshabilita las rutas de HU-10.

## Archivos de la integración de HU-10

El inventario siguiente se calcula sobre el commit del merge y comprende código, documentación, diagramas, migración y pruebas.

- `.cin324/historias/HU-10.md`
- `02-rediseno-to-be.md`
- `03-requisitos.md`
- `04-historias-usuario.md`
- `07-criterios-aceptacion.md`
- `08-modelo-dominio.md`
- `09-casos-de-uso.md`
- `10-diagramas-secuencia.md`
- `11-diagramas-estado.md`
- `12-trazabilidad.md`
- `app/db/derivaciones.py`
- `app/db/migrations/021_transferencia_psiquiatria.sql`
- `app/rutas/clinica.py`
- `app/rutas/derivaciones.py`
- `app/rutas/reserva.py`
- `app/servicios/atenciones.py`
- `app/servicios/confirmacion.py`
- `app/servicios/derivaciones.py`
- `app/servicios/disponibilidad.py`
- `app/servicios/plantillas_correo.py`
- `app/servicios/reagendamiento.py`
- `app/servicios/reserva.py`
- `app/templates/derivaciones.html`
- `app/templates/psicologa.html`
- `app/templates/reserva_confirmada.html`
- `CAMBIOS.md`
- `diagramas/casos-de-uso.png`
- `diagramas/casos-de-uso.puml`
- `diagramas/dss-01.png`
- `diagramas/dss-05.png`
- `diagramas/dss-06.png`
- `diagramas/dss-06.puml`
- `diagramas/est-01.png`
- `diagramas/est-01.puml`
- `diagramas/est-02.png`
- `diagramas/est-03.png`
- `diagramas/est-05.png`
- `diagramas/est-05.puml`
- `diagramas/modelo-dominio.png`
- `diagramas/modelo-dominio.puml`
- `diagramas/README.md`
- `diagramas/to-be-hu-10.png`
- `diagramas/to-be-hu-10.puml`
- `HU10-VALIDACION-FINAL.md`
- `openspec/specs/derivacion-psiquiatria/spec.md`
- `README.md`
- `tests/test_hu10_derivaciones.py`
