# reserva-hora Specification

## Purpose

Permite al Paciente reservar un bloque horario disponible de la psicóloga, dejando registrada una Reserva y avisando al paciente, sin depender de WhatsApp ni del registro manual en Excel.

## Requirements

### Requirement: Registrar una reserva de un bloque horario disponible

El sistema DEBE (MUST) registrar una Reserva en estado "Pendiente de confirmación" cuando el Paciente selecciona un bloque horario que sigue disponible e ingresa un RUT registrado. Al registrarla, el bloque deja de estar disponible para otros pacientes y el sistema DEBE (MUST) encolar el aviso de reserva registrada para su envío por correo electrónico. Si el paciente no tiene correo, el aviso queda omitido y no se registra un envío exitoso.

#### Scenario: El paciente reserva un bloque horario disponible

- **GIVEN** que el bloque del jueves 12 de noviembre a las 16:00 está disponible
- **AND** que el paciente tiene registrados su nombre completo, RUT y un medio de contacto
- **WHEN** el paciente reserva ese bloque horario
- **THEN** el sistema registra la reserva en estado "pendiente de confirmación"
- **AND** el bloque del jueves 12 de noviembre a las 16:00 deja de estar disponible para otros pacientes
- **AND** el sistema encola y envía al paciente el aviso de la reserva registrada por correo electrónico

### Requirement: Rechazar la reserva de un bloque que ya no está disponible

Si el bloque seleccionado ya tiene una reserva vigente o deja de estar disponible antes de confirmar, el sistema NO DEBE (MUST NOT) registrar la reserva y DEBE (MUST) informar que ya no está disponible junto con los bloques horarios disponibles más cercanos.

#### Scenario: Otro paciente reservó el mismo bloque horario antes

- **GIVEN** que el bloque del jueves 12 de noviembre a las 16:00 fue reservado por otro paciente
- **WHEN** el paciente intenta reservar ese bloque horario
- **THEN** el sistema rechaza la reserva indicando que el bloque ya no está disponible
- **AND** informa los bloques horarios disponibles más cercanos

### Requirement: Derivar al registro cuando el RUT no está registrado

Si el RUT ingresado no corresponde a un Paciente registrado, el sistema NO DEBE (MUST NOT) registrar la reserva y DEBE (MUST) derivar al registro de los datos del paciente.

#### Scenario: El paciente no está registrado en el sistema

- **GIVEN** que el paciente ingresa un RUT que no está registrado
- **WHEN** el paciente intenta reservar un bloque horario disponible
- **THEN** el sistema no registra la reserva
- **AND** lo deriva al registro de sus datos personales
- **AND** al completar el registro retoma la reserva del bloque horario seleccionado
