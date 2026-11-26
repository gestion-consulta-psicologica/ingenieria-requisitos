# Proposal — HU-03 Confirmar o cancelar una hora

## Why

Después de reservar, el paciente debe confirmar si mantiene la hora; hoy esa confirmación depende de WhatsApp y la reserva queda en «Pendiente de confirmación» sin un mecanismo en la plataforma. HU-03 automatiza la solicitud y el recordatorio, registra la respuesta del paciente y, si no responde, deja la reserva «Sin confirmar» y genera el cargo de $5.000 definido en el proceso.

La primera implementación usaba un servicio de mensajería simulado y un panel de demostración para avanzar el tiempo. Esta etapa reemplaza ese mecanismo por **correo electrónico real por SMTP**, una **cola persistente con reintentos**, un **planificador automático** y **enlaces seguros de un solo uso**, sin modificar la base de datos original ni registrar envíos ficticios como exitosos.

## What Changes

- Enviar por **SMTP** el **aviso de reserva registrada**, la **solicitud de confirmación** (víspera) y el **recordatorio** (mañana de la atención), además del **aviso de cargo**.
- Registrar cada envío en una **cola persistente** (`correo_pendiente`) con clave de idempotencia, estado, intentos, próximo intento, error y `Message-ID`; los correos sin destinatario quedan `omitido`, nunca `enviado`.
- **Planificador automático** en el arranque de la aplicación: envía la solicitud en la víspera y el recordatorio en la mañana según la zona `America/Santiago`; al llegar la hora de la atención sin respuesta, vence la solicitud y registra el cargo.
- **Recuperación tras reinicio:** los trabajos `enviando` más antiguos que el timeout vuelven a `pendiente`; los `pendiente` se reintentan sin duplicar envíos.
- **Reintentos con espera exponencial** ante errores de conexión o envío; error de autenticación SMTP deja el trabajo `fallido` sin reintentos; si SMTP no está configurado el trabajo permanece `pendiente` con el motivo y **nunca** se marca `enviado`.
- **Tokens de un solo uso** para responder desde el correo: dos enlaces (confirmar / no asistirá), guardados solo como hash SHA-256, con expiración al inicio de la atención y rechazo de tokens usados, vencidos o de otra acción.
- Al enviar el recordatorio, la solicitud anterior pasa a **reemplazada** con `fechaCierre` y su correo pendiente se cancela, en la misma transacción que crea la nueva solicitud y sus tokens.
- Mantener como máximo **una solicitud pendiente por reserva** y **un cargo por reserva** mediante restricciones de integridad.
- Mostrar en `/reservas/{id}` el estado real de cada correo (pendiente, enviando, enviado, fallido, omitido, cancelado), destinatario, `Message-ID`, intentos, error y próximos hitos; quitar el panel de simulación.
- Agregar la migración `005_notificaciones_correo.sql` con `correo_pendiente` y `token_confirmacion`, sin alterar las tablas existentes.
- Mantener las respuestas desde la plataforma (`POST /reservas/{id}/confirmar` y `/no-asistir`) y agregar las rutas de enlace seguro (`GET/POST /respuesta/confirmar/{token}` y `/respuesta/cancelar/{token}`).
- Rechazar con **HTTP 409** las respuestas sin solicitud pendiente, sobre solicitudes respondidas, reemplazadas o vencidas, o sobre una reserva que ya no está pendiente, sin modificar datos.
- Mantener coherentes BPMN, DSS-01, EST-01, modelo de dominio, requisitos, historias, criterios y README.

**Fuera de alcance:** WhatsApp real, procesar pagos, comprobantes o boletas (HU-05 a HU-07); reagendar o cancelar desde la gestión posterior (HU-04); autenticación real; guardar credenciales SMTP en el repositorio; usar datos personales reales en pruebas.

## Capabilities

### New Capabilities

- `confirmacion-asistencia`: envío real por SMTP con cola persistente, planificador, reintentos y recuperación; tokens seguros de un solo uso; reemplazo y cierre de solicitudes; respuesta del paciente; transiciones de la Reserva; Cargo cuando no hay respuesta; rechazo de operaciones inválidas sin modificar datos.

### Modified Capabilities

- `reserva-hora`: el aviso de reserva registrada deja de ser simulado y se encola para envío real por SMTP, sin cambiar el comportamiento de reserva ni la disponibilidad.
- `registro-paciente`: sin cambios funcionales; el correo del paciente pasa a ser el destino de las notificaciones cuando está registrado.

## Impact

- **Código:** `app/configuracion.py`, `app/tiempo.py`, `app/main.py`, `app/rutas/reserva.py`, `app/servicios/confirmacion.py`, `app/servicios/notificaciones.py`, `app/servicios/cola_correo.py`, `app/servicios/correo.py`, `app/servicios/plantillas_correo.py`, `app/servicios/tokens.py`, `app/servicios/planificador.py`, plantillas `reserva_confirmada.html` y `respuesta_token.html`; se elimina `app/servicios/mensajeria.py`.
- **Base de datos:** migración `005` con `correo_pendiente` y `token_confirmacion`. La base `data/app.db` no se modifica durante esta etapa; las migraciones se aplican al arrancar o en bases temporales de prueba.
- **Configuración:** variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USUARIO`, `SMTP_CLAVE`, `SMTP_REMITENTE`, `SMTP_SEGURIDAD`, `SMTP_TIMEOUT`, `CORREO_URL_PUBLICA`, `CORREO_MAX_INTENTOS`, `CORREO_REINTENTO_BASE_SEGUNDOS`, `PLANIFICADOR_ACTIVO`, `PLANIFICADOR_INTERVALO_SEGUNDOS`, `PLANIFICADOR_TIMEOUT_ENVIO_SEGUNDOS`, `CONFIRMACION_HORA_VISPERA`, `CONFIRMACION_HORA_RECORDATORIO` y `ZONA_HORARIA`. Las credenciales no se versionan.
- **Pruebas:** suite completa con base temporal y un servidor SMTP falso local; envío exitoso, error de conexión y reintento, credenciales rechazadas, SMTP no configurado, recuperación tras reinicio, prevención de duplicados, tokens, planificador, UI e integridad.
- **Documentación:** `README.md`, `03-requisitos.md`, `04-historias-usuario.md`, `07-criterios-aceptacion.md`, `08-modelo-dominio.md`, `09-casos-de-uso.md`, `10-diagramas-secuencia.md`, `11-diagramas-estado.md`, `12-trazabilidad.md`, `.cin324/proyecto.md` y `.cin324/historias/HU-03.md`; diagramas `.puml` y sus exportaciones.
- **Sistemas externos:** proveedor SMTP real en producción; en pruebas, servidor SMTP falso local. No se envían correos a pacientes reales.
- **Trazabilidad:** HU-03, actividades «Enviar solicitud de confirmación automática» y «Confirmar o cancelar hora en plataforma», CU-03, RP-05, RP-06 y RP-22, DSS-01 y EST-01.
