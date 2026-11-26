# Tasks — HU-03 Confirmar o cancelar una hora

## 1. Datos y configuración

- [x] 1.1 Mantener las migraciones `003` y `004` (solicitudes, estados, fechas, cargo e índice único de solicitud pendiente) y verificar que se aplican sobre bases nuevas y existentes sin perder filas.
- [x] 1.2 Crear `app/db/migrations/005_notificaciones_correo.sql` con `correo_pendiente` (idempotencia, estados, intentos, backoff, `Message-ID`) y `token_confirmacion` (hash, acción, expiración, uso único), sin alterar tablas existentes.
- [x] 1.3 Definir `ConfiguracionCorreo` y `cargar_configuracion()` con variables de entorno para SMTP, URL pública, reintentos, planificador, horas de envío y zona horaria; no incluir credenciales en el repositorio.
- [x] 1.4 Agregar `tzdata` a `requirements.txt` para que `zoneinfo` funcione en Windows.

## 2. Correo real y cola

- [x] 2.1 Crear el `Protocol` `ServicioCorreo` y el adaptador `ServicioCorreoSMTP` con texto/HTML, `starttls`/`ssl`/sin cifrado, autenticación opcional y clasificación de errores de conexión, autenticación y envío.
- [x] 2.2 Crear la cola `correo_pendiente`: encolar de forma idempotente, reclamar con transacción, marcar enviado/reintento/fallido, cancelar pendientes reemplazados y recuperar `enviando`.
- [x] 2.3 Crear plantillas de correo para aviso de reserva, solicitud/recordatorio con enlaces y aviso de cargo, con texto y HTML escapado.
- [x] 2.4 Encolar el aviso de reserva al registrar una reserva y marcar `omitido` cuando el paciente no tiene correo, sin registrar un éxito ficticio.
- [x] 2.5 Verificar con un servidor SMTP falso local el envío exitoso, el error de conexión con reintento, las credenciales incorrectas, SMTP no configurado, la recuperación tras reinicio y la prevención de duplicados.

## 3. Planificador y tokens

- [x] 3.1 Implementar `PlanificadorCorreos` con ciclo inyectable, recuperación de `enviando`, eventos de reserva y envío de hasta 50 correos por ciclo; ejecutarlo en un hilo para no bloquear el event loop.
- [x] 3.2 Integrar el planificador en el lifespan de `crear_app`, respetando `PLANIFICADOR_ACTIVO` y permitiendo inyectar el servicio de correo y la configuración en pruebas.
- [x] 3.3 Enviar la víspera y el recordatorio según la hora configurada en `America/Santiago`; al enviar el recordatorio, reemplazar la solicitud anterior y cancelar su correo pendiente en la misma transacción.
- [x] 3.4 Vencer automáticamente la solicitud pendiente al llegar la hora de la atención, dejar la reserva «Sin confirmar», registrar el Cargo de $5.000 y encolar el aviso de cargo.
- [x] 3.5 Crear tokens de un solo uso por acción, guardar solo su hash, expirarlos al inicio de la atención y rechazar tokens usados, vencidos, inválidos o de la acción contraria.
- [x] 3.6 Agregar las rutas `GET/POST /respuesta/confirmar/{token}` y `/respuesta/cancelar/{token}` con página de confirmación y ejecución solo por `POST`.

## 4. Lógica de confirmación

- [x] 4.1 Mantener `enviar_solicitud` para víspera y recordatorio, con validación de reserva pendiente, secuencia y duplicados; registrar la solicitud, los tokens y el correo en una sola transacción.
- [x] 4.2 Mantener `registrar_respuesta` para «confirma»: actualizar solo la solicitud pendiente más reciente, guardar respuesta y fecha, y dejar la reserva «Confirmada».
- [x] 4.3 Mantener `registrar_respuesta` para «no asistirá»: actualizar solo la solicitud pendiente más reciente, guardar respuesta y fecha, dejar la reserva «Cancelada» y liberar el bloque.
- [x] 4.4 Implementar `registrar_respuesta_con_token` consumiendo el token en la misma transacción que registra la respuesta.
- [x] 4.5 Mantener `marcar_hora_sin_respuesta` con una solicitud pendiente, cierre como «vencida», cargo de $5.000 y aviso de cargo; impedir duplicados con restricciones y validaciones.
- [x] 4.6 Rechazar respuestas sin solicitud pendiente, sobre solicitudes respondidas, reemplazadas o vencidas, tokens inválidos y reservas que ya no están pendientes, con 404/409 y sin modificar datos.

## 5. Rutas y pantalla

- [x] 5.1 Quitar el panel de simulación y la ruta `/reservas/{id}/simular`; conservar `GET /reservas/{id}`, confirmar y no asistir desde la plataforma.
- [x] 5.2 Mostrar en el detalle el estado real de cada correo (pendiente, enviando, enviado, fallido, omitido, cancelado), destinatario, fecha, intentos, error, `Message-ID`, solicitudes y cargo.
- [x] 5.3 Mostrar los hitos programados (víspera, recordatorio, vencimiento), la zona horaria, el estado del SMTP y del planificador, y un aviso cuando el correo no está configurado.
- [x] 5.4 Crear la página `respuesta_token.html` para los enlaces de correo, con mensajes claros para token inválido, usado o vencido.

## 6. Pruebas

- [x] 6.1 Crear `tests/smtp_falso.py` con un servidor SMTP local que soporte EHLO, AUTH LOGIN/PLAIN, MAIL, RCPT, DATA y QUIT.
- [x] 6.2 Crear `tests/test_hu03_correo.py` con envío exitoso, error de conexión y reintento, credenciales rechazadas, SMTP no configurado, recuperación de `enviando`/`pendiente`, duplicados e integridad.
- [x] 6.3 Actualizar `tests/test_hu03_confirmacion.py` con solicitudes, tokens, respuestas por enlace y plataforma, reemplazo, vencimiento, cargo, planificador, UI y errores 409/404.
- [x] 6.4 Actualizar `tests/test_hu02_reserva.py` para verificar el aviso de reserva en la cola y eliminar las referencias a la mensajería simulada.
- [x] 6.5 Aislar las pruebas con base temporal, `PLANIFICADOR_ACTIVO=0` y variables SMTP vacías; verificar que `data/app.db` no cambia.
- [x] 6.6 Ejecutar `pytest` completo y confirmar que pasan las pruebas de HU-01, HU-02, HU-02A y HU-03.

## 7. Documentación y cierre

- [x] 7.1 Actualizar `README.md` con SMTP, variables de entorno, migración `005`, planificador, cola, tokens, rutas y recorrido manual sin simulación.
- [x] 7.2 Actualizar `03-requisitos.md`, `04-historias-usuario.md` y `07-criterios-aceptacion.md` para mencionar el envío real por correo y los enlaces seguros.
- [x] 7.3 Actualizar `08-modelo-dominio.md`, `09-casos-de-uso.md`, `10-diagramas-secuencia.md`, `11-diagramas-estado.md` y `12-trazabilidad.md` con la cola, los tokens y el canal de correo.
- [x] 7.4 Actualizar `diagramas/dss-01.puml`, `diagramas/dss-03.puml`, `diagramas/est-01.puml`, `diagramas/casos-de-uso.puml` y `diagramas/TO-BE.bpmn`; la exportación PNG queda pendiente por falta de PlantUML.
- [x] 7.5 Actualizar `.cin324/proyecto.md` y `.cin324/historias/HU-03.md` con el estado real, las decisiones pendientes y las limitaciones.
- [x] 7.6 Ejecutar `openspec validate`, `git diff --check` y verificar el hash de `data/app.db` antes de cerrar.

## Workflow follow-up

- Revisar las especificaciones y el código generado con el estudiante antes de cerrar el cambio.
- Completar la validación manual del sistema con una base aislada antes de archivar.
- Archivar el cambio con `openspec archive` solo cuando el estudiante apruebe el cierre.
- No archivar HU-03 ni hacer commits mientras la validación manual esté pendiente.
