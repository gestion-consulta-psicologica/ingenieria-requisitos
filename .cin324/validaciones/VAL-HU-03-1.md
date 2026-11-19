# Informe de validación — HU-03 Confirmar o cancelar una hora

**Fecha de validación inicial:** 2026-11-17 · **Actualización:** 2026-11-18
**Cambio de OpenSpec:** `hu-03-confirmar-cancelar-hora`
**Estado:** observaciones resueltas; documentación y código migrados a correo real por SMTP. Pendiente: reexportar PNG de diagramas y validación final del estudiante.

## Resumen

La validación inicial detectó siete observaciones. Todas las observaciones de tipo A, B y C fueron corregidas en los artefactos y en la implementación. Las observaciones de tipo E (seguridad) quedan documentadas como limitaciones para producción, fuera del alcance del ejercicio.

| Obs. | Observación | Tipo | Estado | Dónde quedó resuelto |
|---|---|---|---|---|
| OBS-1 | Se podía confirmar o no asistir sin `SolicitudConfirmacion` | B/C | Resuelto | `04` HU-03 CA1/CA2, `07`, `spec.md`, `design.md`, `app/servicios/confirmacion.py`, pruebas |
| OBS-2 | HU-03 hablaba de pago y gestión posterior | C | Resuelto | `04` HU-03 CA3/CA4, `07`, `.cin324/historias/HU-03.md` |
| OBS-3 | Faltaba `fechaRespuesta` en el modelo | C | Resuelto | `08-modelo-dominio.md`, `diagramas/modelo-dominio.puml`, ficha HU-03 |
| OBS-4 | El Gherkin mencionaba una «agenda» inexistente | C | Resuelto | `07-criterios-aceptacion.md`, `spec.md`, pruebas |
| OBS-5 | El Cargo de $5.000 no tenía requisito propio | B | Resuelto | RP-22 en `03-requisitos.md` y `12-trazabilidad.md` |
| OBS-6 | Diagramas fuente actualizados sin PNG | C | Parcial | PNG de `dss-01`, `dss-03`, `est-01` y `casos-de-uso` reexportados con PlantUML; `TO-BE.png` pendiente de reexportar porque no hay herramienta BPMN |
| OBS-7 | Sin autenticación, CSRF, IDs secuenciales y RUT visible | E | Documentado | `README.md`, `.cin324/proyecto.md`, supuestos de HU-03 |

## Cambio principal: correo real

La implementación anterior usaba un servicio de mensajería simulado y un panel `/simular` para avanzar el tiempo. Esa simulación se eliminó y se reemplazó por:

- Cola persistente `correo_pendiente` con clave idempotente, intentos, error y fechas UTC.
- Envío real por SMTP mediante `ServicioCorreoSMTP`, con errores tipados y reintentos con espera exponencial.
- Planificador automático que procesa la cola al iniciar la aplicación y periódicamente.
- Tokens de un solo uso para confirmar y cancelar desde el correo; solo se guarda el hash.
- Recuperación de trabajos `enviando` abandonados y cancelación de correos obsoletos al reemplazar una solicitud.
- Aviso de reserva y aviso de cargo también salen por correo.

Decisiones documentadas:

- Si no existe ninguna solicitud (por ejemplo, caída del sistema), la reserva no se vence automáticamente; queda para revisión manual.
- `marcar_hora_sin_respuesta` exige al menos una solicitud pendiente, no necesariamente víspera y recordatorio a la vez.
- Los horarios de envío son configurables y provisionales hasta confirmación del cliente.
- No se envían correos reales a pacientes: las pruebas usan un servidor SMTP falso local.

## Verificación

- **72 pruebas pasan** (`pytest`), con un warning de deprecación de Starlette.
- Pruebas de HU-03 cubren envío, reintentos, recuperación, tokens usados/vencidos, respuestas por enlace, migraciones y ausencia de correo.
- `data/app.db` no fue migrada ni modificada.
- SHA256 de `data/app.db` verificado: `97E01B0E05CA75E8C42D62755D32779AA36D304A6B980CC47DA5AD83A3E60B29`.
- No se hizo commit ni se archivó HU-03.

## Limitaciones vigentes

- `TO-BE.png` no se reexportó porque no hay herramienta BPMN disponible. Las demás fuentes y PNG de diagramas están actualizados; reexportar `TO-BE.png` al abrir el BPMN en un editor compatible.
- Seguridad de producción pendiente: autenticación, autorización, CSRF, IDs no secuenciales y RUT visible (RP-17, RD-01, RD-02).
- El envío real requiere configurar SMTP; sin configuración los correos quedan pendientes con error visible y nunca se marcan como enviados.

## Estado de los artefactos

- [x] `03-requisitos.md`: RP-05, RP-06 y RP-22.
- [x] `04-historias-usuario.md`: HU-02 CA4 y HU-03 CA1–CA7.
- [x] `07-criterios-aceptacion.md`: escenarios de correo, enlace usado, SMTP no disponible y sin correo.
- [x] `08-modelo-dominio.md`: `fechaRespuesta` y entidades de soporte.
- [x] `09-casos-de-uso.md`: actor SMTP, CU-03 y extensión.
- [x] `10-diagramas-secuencia.md`: DSS-01 y DSS-03.
- [x] `11-diagramas-estado.md`: transiciones y estados de `CorreoPendiente`.
- [x] `12-trazabilidad.md`: RP-05, RP-06 y RP-22.
- [x] `README.md`: configuración, migraciones, pruebas y limitaciones.
- [x] `.cin324/proyecto.md`, `.cin324/historias/HU-02.md`, `.cin324/historias/HU-03.md`.
- [x] `openspec/changes/hu-03-confirmar-cancelar-hora` y `openspec/specs/reserva-hora`.
- [x] Fuentes de diagramas `dss-01.puml`, `dss-03.puml`, `est-01.puml` y `TO-BE.bpmn`.
- [x] PNG de `dss-01`, `dss-03`, `est-01`, `casos-de-uso` y `modelo-dominio` actualizados.
- [ ] `TO-BE.png` reexportado.
- [ ] Validación final del estudiante.

## Siguiente paso

Revisar la aplicación con SMTP configurado y un correo de prueba, reexportar los PNG cuando PlantUML esté disponible y registrar la aceptación del estudiante. No hacer commits ni archivar HU-03 sin pedido explícito.
