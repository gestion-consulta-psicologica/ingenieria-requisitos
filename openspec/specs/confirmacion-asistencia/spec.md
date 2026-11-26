# confirmacion-asistencia Specification

## Purpose

Permite al Paciente confirmar o rechazar una hora reservada desde la plataforma o desde un enlace seguro recibido por correo, y deja constancia del envío real de la solicitud y el recordatorio, del reemplazo y cierre de solicitudes, del cargo por no confirmar y del estado final de la Reserva.

## Requirements

### Requirement: Enviar la solicitud de confirmación y el recordatorio por correo electrónico

El sistema DEBE (MUST) registrar y enviar por SMTP la solicitud de confirmación en la víspera de la atención y el recordatorio en la mañana, una sola vez por reserva y tipo. Cada envío DEBE quedar en una cola persistente con clave de idempotencia, estado, intentos y error. El correo DEBE incluir enlaces seguros de un solo uso para confirmar o informar que no asistirá.

#### Scenario: El sistema envía la solicitud de confirmación y el recordatorio

- **GIVEN** que el paciente tiene una reserva en estado "pendiente de confirmación" y un correo registrado
- **WHEN** llega la víspera de la atención
- **THEN** el sistema registra la solicitud de confirmación y la encola para envío por correo
- **AND** en la mañana de la atención registra y encola el recordatorio
- **AND** cada correo incluye un enlace para confirmar y otro para informar que no asistirá

### Requirement: Reemplazar la solicitud anterior al enviar el recordatorio

Al enviar el recordatorio, la solicitud pendiente anterior DEBE (MUST) pasar a estado "reemplazada" con su `fechaCierre`, su correo pendiente DEBE cancelarse y la nueva solicitud DEBE crearse en estado "pendiente". Todas las operaciones DEBEN ejecutarse en una misma transacción.

#### Scenario: El recordatorio reemplaza la solicitud anterior

- **GIVEN** que la reserva tiene la solicitud de víspera en estado "pendiente"
- **WHEN** el sistema envía el recordatorio de la mañana
- **THEN** la solicitud de víspera queda en estado "reemplazada" con su fecha de cierre
- **AND** su correo pendiente queda cancelado
- **AND** el recordatorio queda como la única solicitud pendiente de la reserva

### Requirement: No registrar envíos ficticios y reintentar los fallos

El sistema NO DEBE (MUST NOT) marcar un correo como "enviado" si el servidor SMTP no aceptó el mensaje. Si falta configuración SMTP, el correo DEBE quedar "pendiente" con el motivo. Si el paciente no tiene correo, DEBE quedar "omitido". Los errores de conexión o envío DEBEN reintentarse con espera exponencial hasta `CORREO_MAX_INTENTOS`; las credenciales rechazadas DEBEN dejar el correo "fallido" sin reintentos.

#### Scenario: El servidor SMTP no está disponible

- **GIVEN** que hay un correo pendiente en la cola
- **AND** el servidor SMTP no responde
- **WHEN** el planificador intenta enviarlo
- **THEN** el correo queda "pendiente" con un nuevo intento programado y el error registrado
- **AND** no se marca como "enviado"

#### Scenario: El paciente no tiene correo registrado

- **GIVEN** que la reserva se registra para un paciente sin correo
- **WHEN** el sistema intenta encolar el aviso de reserva
- **THEN** el correo queda en estado "omitido" con el motivo
- **AND** no se registra un envío exitoso

### Requirement: Recuperar la cola tras un reinicio

Al iniciar, el sistema DEBE (MUST) recuperar los correos que quedaron en estado "enviando" más antiguos que el timeout configurado y volver a procesarlos, sin duplicar envíos ya confirmados.

#### Scenario: El proceso se detiene durante un envío

- **GIVEN** que un correo quedó en estado "enviando"
- **WHEN** el planificador vuelve a iniciar después del timeout
- **THEN** el correo vuelve a "pendiente"
- **AND** se envía una sola vez si el servidor SMTP lo acepta
- **AND** los correos ya "enviado" no se reenvían

### Requirement: Mantener una sola solicitud pendiente por reserva

El sistema DEBE (MUST) impedir que exista más de una `SolicitudConfirmacion` en estado "pendiente" para la misma Reserva. La restricción DEBE estar protegida por una restricción de integridad en la base de datos, además de las validaciones del servicio.

#### Scenario: Se intenta crear una segunda solicitud pendiente

- **GIVEN** que la reserva ya tiene una solicitud en estado "pendiente"
- **WHEN** el sistema intenta registrar otra solicitud pendiente para la misma reserva
- **THEN** la operación falla y no se crea una segunda solicitud pendiente
- **AND** la solicitud pendiente existente se conserva sin cambios

### Requirement: Confirmar la asistencia de una reserva

Cuando el paciente confirma su asistencia desde la plataforma o desde el enlace de correo y existe una solicitud de confirmación pendiente, el sistema DEBE (MUST) registrar la respuesta y `fechaRespuesta` en la solicitud pendiente más reciente, marcarla como "respondida" y dejar la Reserva en estado "confirmada". El enlace de correo DEBE ser de un solo uso. Las acciones de respuesta no DEBEN mostrarse si no existe una solicitud pendiente.

#### Scenario: El paciente confirma su asistencia

- **GIVEN** que el paciente tiene una reserva para el jueves 12 de noviembre a las 16:00 en estado "pendiente de confirmación"
- **AND** que el sistema le envió la solicitud de confirmación el miércoles 11 de noviembre y está pendiente de respuesta
- **WHEN** el paciente confirma su asistencia desde la plataforma o desde el enlace del correo
- **THEN** la reserva queda en estado "confirmada"
- **AND** la solicitud pendiente más reciente queda en estado "respondida", con la respuesta "confirma" y su fecha de respuesta
- **AND** el enlace utilizado queda marcado como usado

#### Scenario: El enlace de correo ya fue utilizado

- **GIVEN** que el paciente ya respondió usando el enlace del correo
- **WHEN** vuelve a abrir o enviar el mismo enlace
- **THEN** el sistema responde con HTTP 409 e informa que el enlace ya fue utilizado
- **AND** la respuesta registrada no cambia

### Requirement: Cancelar la reserva cuando el paciente responde que no asistirá

Cuando el paciente responde que no asistirá desde la plataforma o desde el enlace de correo y existe una solicitud de confirmación pendiente, el sistema DEBE (MUST) registrar la respuesta y `fechaRespuesta` en la solicitud pendiente más reciente, marcarla como "respondida", dejar la Reserva en estado "cancelada" y liberar el bloque horario para otros pacientes.

#### Scenario: El paciente cancela su hora al responder la confirmación

- **GIVEN** que el paciente tiene una reserva en estado "pendiente de confirmación"
- **AND** que el sistema le envió una solicitud de confirmación y está pendiente de respuesta
- **WHEN** el paciente responde que no asistirá
- **THEN** la reserva queda en estado "cancelada"
- **AND** la solicitud pendiente más reciente queda en estado "respondida", con la respuesta "no asistirá" y su fecha de respuesta
- **AND** se registra un cargo de $5.000 asociado al paciente y la reserva y se encola su aviso
- **AND** el bloque horario vuelve a estar disponible para otros pacientes

### Requirement: Cerrar la solicitud sin respuesta

Si llega la hora de la atención sin respuesta del paciente y existe una solicitud pendiente, el sistema DEBE (MUST) marcar la solicitud pendiente más reciente como "vencida", conservar `respuesta = "sin respuesta"`, dejar `fechaRespuesta` nula y registrar `fechaCierre` con la fecha y hora de la atención. Además, DEBE dejar la Reserva en estado "sin confirmar".

#### Scenario: El paciente no responde la confirmación

- **GIVEN** que el paciente tiene una reserva en estado "pendiente de confirmación"
- **AND** que el sistema le envió la solicitud de confirmación el día anterior y el recordatorio en la mañana de la atención
- **WHEN** llega la hora de la atención sin respuesta del paciente
- **THEN** la reserva queda en estado "sin confirmar"
- **AND** la solicitud pendiente más reciente queda en estado "vencida", con la respuesta "sin respuesta" y la fecha de cierre de la atención
- **AND** no se registra una fecha de respuesta del paciente

### Requirement: Registrar el cargo por no confirmar

Cuando el paciente no responde hasta la hora de la atención, el sistema DEBE (MUST) registrar un Cargo de $5.000 por reserva de hora con motivo "sin confirmar", asociado al paciente y a la reserva, y encolar el aviso de cargo por correo.

#### Scenario: Se registra el cargo al vencer la solicitud

- **GIVEN** que la solicitud de confirmación vence sin respuesta
- **WHEN** el sistema cierra la solicitud como "vencida"
- **THEN** registra un cargo de $5.000 por reserva de hora asociado al paciente y a la reserva
- **AND** el aviso de cargo se encola para envío por correo
- **AND** no se duplica el cargo si la operación se repite

### Requirement: Rechazar operaciones inválidas sin modificar los datos

El sistema DEBE (MUST) responder con HTTP 404 cuando la reserva o el token no existen y con HTTP 409 y un mensaje claro, sin modificar la Reserva, las Solicitudes de confirmación, los Cargos ni los tokens, cuando la operación ya fue registrada, no existe solicitud pendiente, la solicitud no está pendiente, la reserva no está pendiente o el token es inválido, usado, vencido o de otra acción.

#### Scenario: Se repite el envío de una solicitud

- **GIVEN** que la reserva está en estado "pendiente de confirmación" y ya tiene registrada la solicitud de víspera
- **WHEN** se intenta enviar de nuevo la solicitud de víspera
- **THEN** el sistema responde con HTTP 409 y un mensaje claro
- **AND** no registra otra solicitud ni encola otro correo

#### Scenario: El paciente responde sin una solicitud pendiente

- **GIVEN** que la reserva está en estado "pendiente de confirmación"
- **AND** no existe una solicitud en estado "pendiente"
- **WHEN** el paciente intenta confirmar o responder que no asistirá
- **THEN** el sistema responde con HTTP 409 y un mensaje claro
- **AND** la reserva conserva su estado y no se crean solicitudes ni cargos nuevos

#### Scenario: El paciente responde una solicitud ya respondida

- **GIVEN** que la solicitud pendiente más reciente ya fue respondida
- **WHEN** el paciente intenta confirmar o responder que no asistirá
- **THEN** el sistema responde con HTTP 409 y un mensaje claro
- **AND** la respuesta registrada no cambia

#### Scenario: El paciente responde una solicitud reemplazada o vencida

- **GIVEN** que la solicitud más reciente está en estado "reemplazada" o "vencida"
- **WHEN** el paciente intenta confirmar o responder que no asistirá
- **THEN** el sistema responde con HTTP 409 y un mensaje claro
- **AND** la solicitud conserva su estado y no se registra una nueva respuesta

#### Scenario: El paciente responde una reserva que ya no está pendiente

- **GIVEN** que la reserva está en estado "confirmada"
- **WHEN** el paciente intenta confirmar o responder que no asistirá
- **THEN** el sistema responde con HTTP 409 y un mensaje claro
- **AND** la reserva conserva su estado y no se crean solicitudes ni cargos nuevos

#### Scenario: El enlace de correo venció

- **GIVEN** que llegó la hora de la atención
- **WHEN** el paciente abre el enlace de confirmación recibido por correo
- **THEN** el sistema responde con HTTP 409 e informa que el enlace venció
- **AND** la reserva y la solicitud conservan el estado de vencimiento
