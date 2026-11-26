# registro-asistencia Specification

## Purpose

Permite a la psicóloga registrar la asistencia o inasistencia del paciente a una atención y deja constancia del cargo por inasistencia sin justificación.

## Requirements

### Requirement: Registrar la asistencia del paciente

Para una Atencion en estado "programada", el sistema DEBE (MUST) permitir registrar que el paciente asistió, dejando la atención en estado "realizada" y mostrando el resultado al consultarla.

#### Scenario: El paciente asiste a la atención

- **GIVEN** que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
- **WHEN** la psicóloga registra que el paciente asistió
- **THEN** la atención queda en estado "realizada"
- **AND** la asistencia queda en el historial de atenciones del paciente

### Requirement: Registrar la inasistencia sin justificación con cargo

Al registrar una inasistencia sin justificación, el sistema DEBE (MUST) dejar la atención en estado "inasistencia" y registrar un cargo de $5.000 asociado a la atención y al paciente, sin modificar el estado del pago.

#### Scenario: El paciente no asiste sin justificación

- **GIVEN** que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
- **WHEN** la psicóloga registra que el paciente no asistió y no justificó la inasistencia
- **THEN** la atención queda en estado "inasistencia"
- **AND** el sistema registra un cargo de $5.000 por inasistencia sin justificación, asociado a la atención y al paciente, sin modificar el estado del pago

### Requirement: Registrar la inasistencia justificada sin cargo

Al registrar una inasistencia con justificación, el sistema DEBE (MUST) dejar la atención en estado "inasistencia justificada", guardar la justificación y NO DEBE (MUST NOT) registrar el cargo.

#### Scenario: El paciente justifica la inasistencia

- **GIVEN** que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
- **WHEN** la psicóloga registra que el paciente no asistió y justificó la inasistencia
- **THEN** la atención queda en estado "inasistencia justificada"
- **AND** el sistema no registra el cargo de $5.000 por inasistencia
