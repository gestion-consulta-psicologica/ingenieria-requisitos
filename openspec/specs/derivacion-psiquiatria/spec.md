# Derivación a psiquiatría

## Purpose

Especificar RP-27 y HU-10 para transferir una reserva original a un médico psiquiatra con una cuenta registrada.

## Requirements

### Requirement: Revisión de la reserva y destinatario disponible

El sistema MUST permitir a la psicóloga responsable derivar una reserva futura pendiente de confirmación a un psiquiatra activo y verificado con bloque propio libre para la misma fecha, horas y modalidad. La agenda psiquiátrica MUST estar excluida de las reservas públicas.

#### Scenario: La psicóloga conserva la solicitud

- **GIVEN** que el paciente registra una reserva con la psicóloga
- **WHEN** no se deriva o el destinatario aún no responde
- **THEN** la reserva conserva su bloque y responsable

#### Scenario: Envío a un destinatario registrado

- **GIVEN** que la reserva es elegible y existe un bloque equivalente libre
- **WHEN** la psicóloga selecciona al psiquiatra activo y registra la derivación
- **THEN** este ve la solicitud pendiente en su bandeja
- **AND** solo puede existir una derivación pendiente para ese ciclo

### Requirement: Transferencia atómica y seguimiento

La aplicación MUST actualizar la reserva original y registrar la transferencia en una transacción. MUST conservar identificador, paciente, fecha de registro e historial y reiniciar el ciclo de confirmación.

#### Scenario: El destinatario acepta

- **GIVEN** una derivación vigente y un bloque libre del destinatario
- **WHEN** el destinatario acepta
- **THEN** la reserva cambia al bloque del psiquiatra y libera el bloque anterior
- **AND** la reserva sigue pendiente de confirmación con una versión nueva
- **AND** quedan registrados ambos bloques, la aceptación y los responsables
- **AND** se conserva la información después de reiniciar la aplicación

#### Scenario: El destinatario rechaza

- **GIVEN** una derivación vigente
- **WHEN** el destinatario la rechaza
- **THEN** se registra el rechazo y la reserva permanece en el bloque original

#### Scenario: Conflicto durante la aceptación

- **GIVEN** que se canceló la reserva, cambió su ciclo, se ocupó el bloque o se desactivó la cuenta
- **WHEN** se trata de aceptar la derivación
- **THEN** el sistema impide la transferencia
- **AND** no crea otra reserva ni cambia su bloque

#### Scenario: Dos aceptaciones concurrentes

- **GIVEN** una derivación vigente
- **WHEN** se reciben dos aceptaciones simultáneas
- **THEN** solo una petición transfiere la reserva y registra el cambio

### Requirement: Permisos y auditoría

El sistema MUST restringir el historial y las operaciones al rol autorizado y a la titularidad. La recepción de una derivación MUST NOT conceder acceso a la ficha clínica.

#### Scenario: Acceso ajeno

- **GIVEN** una cuenta de paciente u otro psiquiatra
- **WHEN** intenta aceptar una derivación ajena
- **THEN** el sistema deniega la operación

#### Scenario: Acceso clínico denegado con paciente inexistente

- **GIVEN** una cuenta de psiquiatra sin permiso clínico
- **WHEN** solicita una ficha para un identificador de paciente inexistente
- **THEN** recibe la misma denegación que para un paciente existente
- **AND** la bitácora registra rol, operación y usuario con referencia de paciente nula
