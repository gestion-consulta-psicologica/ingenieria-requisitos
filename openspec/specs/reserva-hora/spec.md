# reserva-hora Specification

## Purpose

Permite al Paciente reservar un bloque horario disponible de la psicóloga, dejando registrada una Reserva y avisando al paciente, sin depender de WhatsApp ni del registro manual en Excel.

## Requirements

### Requirement: Registrar una reserva de un bloque horario disponible

El sistema DEBE registrar una Reserva en estado "Pendiente de confirmación" cuando el Paciente selecciona un bloque horario que sigue disponible e ingresa un RUT registrado. Al registrarla, el bloque deja de estar disponible para otros pacientes y el sistema DEBE encolar el aviso de reserva registrada para su envío por correo electrónico. Si el paciente no tiene correo, el aviso queda omitido y no se registra un envío exitoso.

#### Scenario: El paciente reserva un bloque horario disponible

- **DADO** que el bloque del jueves 12 de noviembre a las 16:00 está disponible
- **Y** que el paciente tiene registrados su nombre completo, RUT y un medio de contacto
- **CUANDO** el paciente reserva ese bloque horario
- **ENTONCES** el sistema registra la reserva en estado "pendiente de confirmación"
- **Y** el bloque del jueves 12 de noviembre a las 16:00 deja de estar disponible para otros pacientes
- **Y** el sistema encola y envía al paciente el aviso de la reserva registrada por correo electrónico

### Requirement: Rechazar la reserva de un bloque que ya no está disponible

Si el bloque seleccionado ya tiene una reserva vigente o deja de estar disponible antes de confirmar, el sistema NO DEBE registrar la reserva y DEBE informar que ya no está disponible junto con los bloques horarios disponibles más cercanos.

#### Scenario: Otro paciente reservó el mismo bloque horario antes

- **DADO** que el bloque del jueves 12 de noviembre a las 16:00 fue reservado por otro paciente
- **CUANDO** el paciente intenta reservar ese bloque horario
- **ENTONCES** el sistema rechaza la reserva indicando que el bloque ya no está disponible
- **Y** informa los bloques horarios disponibles más cercanos

### Requirement: Derivar al registro cuando el RUT no está registrado

Si el RUT ingresado no corresponde a un Paciente registrado, el sistema NO DEBE registrar la reserva y DEBE derivar al registro de los datos del paciente.

#### Scenario: El paciente no está registrado en el sistema

- **DADO** que el paciente ingresa un RUT que no está registrado
- **CUANDO** el paciente intenta reservar un bloque horario disponible
- **ENTONCES** el sistema no registra la reserva
- **Y** lo deriva al registro de sus datos personales
- **Y** al completar el registro retoma la reserva del bloque horario seleccionado
