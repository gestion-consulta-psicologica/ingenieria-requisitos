# registro-paciente Specification

## Purpose

Permite que un Paciente que aún no está registrado ingrese sus datos personales desde el flujo de reserva, para que pueda reservar su hora sin depender de WhatsApp ni del registro manual de la secretaria.

## Requirements

### Requirement: Registrar los datos de un Paciente nuevo

El sistema DEBE (MUST) registrar un Paciente con nombre completo, RUT y correo electrónico con formato válido (teléfono opcional) cuando el RUT no existe y los datos obligatorios están completos. El RUT se normaliza y es único. Si el registro se inició desde la reserva de HU-02, el sistema DEBE (MUST) retomar la reserva del bloque horario seleccionado con el RUT precargado; si no hay bloque seleccionado, DEBE (MUST) confirmar el registro.

#### Scenario: Un paciente nuevo se registra desde la reserva

- **GIVEN** que el paciente ingresó un RUT que no está registrado
- **WHEN** ingresa su nombre completo, su RUT y su correo electrónico
- **AND** guarda sus datos
- **THEN** el sistema registra al paciente
- **AND** retoma la reserva del bloque horario seleccionado

### Requirement: Rechazar el registro con datos obligatorios incompletos

El sistema NO DEBE (MUST NOT) registrar al Paciente si falta el nombre completo, el RUT o el correo electrónico, o si el correo no tiene formato válido, y DEBE (MUST) informar qué dato falta. El correo es obligatorio porque la solicitud de confirmación de HU-03 se envía por correo (2026-11-25).

#### Scenario: El paciente no completa los datos obligatorios

- **GIVEN** que el paciente está registrando sus datos
- **WHEN** intenta guardar sin nombre completo, RUT o correo electrónico
- **THEN** el sistema no registra al paciente
- **AND** le informa qué dato falta

### Requirement: Reutilizar el Paciente cuando el RUT ya está registrado

Si el RUT ingresado ya existe, el sistema NO DEBE (MUST NOT) duplicar al Paciente y DEBE (MUST) utilizar el registro existente. Si el registro se inició desde la reserva, DEBE (MUST) retomar la reserva del bloque horario seleccionado con ese Paciente.

#### Scenario: El RUT ya está registrado

- **GIVEN** que el paciente ingresa un RUT que ya existe en el sistema
- **WHEN** intenta registrar sus datos
- **THEN** el sistema no duplica al paciente
- **AND** utiliza el registro existente
