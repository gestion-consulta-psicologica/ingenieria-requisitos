# Spec Delta — registro-paciente

## Purpose

Permite que un Paciente que aún no está registrado ingrese sus datos personales desde el flujo de reserva, para que pueda reservar su hora sin depender de WhatsApp ni del registro manual de la secretaria.

## ADDED Requirements

### Requirement: Registrar los datos de un Paciente nuevo

El sistema DEBE registrar un Paciente con nombre completo, RUT y al menos uno de teléfono o correo cuando el RUT no existe y los datos obligatorios están completos. El RUT se normaliza y es único. Si el registro se inició desde la reserva de HU-02, el sistema DEBE retomar la reserva del bloque horario seleccionado con el RUT precargado; si no hay bloque seleccionado, DEBE confirmar el registro.

#### Scenario: Un paciente nuevo se registra desde la reserva

- **DADO** que el paciente ingresó un RUT que no está registrado
- **CUANDO** ingresa su nombre completo, su RUT y un medio de contacto
- **Y** guarda sus datos
- **ENTONCES** el sistema registra al paciente
- **Y** retoma la reserva del bloque horario seleccionado

### Requirement: Rechazar el registro con datos obligatorios incompletos

El sistema NO DEBE registrar al Paciente si falta el nombre completo, el RUT o el medio de contacto, y DEBE informar qué dato falta.

#### Scenario: El paciente no completa los datos obligatorios

- **DADO** que el paciente está registrando sus datos
- **CUANDO** intenta guardar sin nombre completo, RUT o medio de contacto
- **ENTONCES** el sistema no registra al paciente
- **Y** le informa qué dato falta

### Requirement: Reutilizar el Paciente cuando el RUT ya está registrado

Si el RUT ingresado ya existe, el sistema NO DEBE duplicar al Paciente y DEBE utilizar el registro existente. Si el registro se inició desde la reserva, DEBE retomar la reserva del bloque horario seleccionado con ese Paciente.

#### Scenario: El RUT ya está registrado

- **DADO** que el paciente ingresa un RUT que ya existe en el sistema
- **CUANDO** intenta registrar sus datos
- **ENTONCES** el sistema no duplica al paciente
- **Y** utiliza el registro existente
