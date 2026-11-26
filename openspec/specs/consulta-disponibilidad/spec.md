# consulta-disponibilidad Specification

## Purpose

Permite al Paciente consultar la disponibilidad semanal de bloques horarios de la psicóloga y conocer cuándo no hay horas disponibles ni cuál es la próxima fecha disponible.

## Requirements

### Requirement: Mostrar bloques horarios disponibles

El sistema DEBE (MUST) mostrar al Paciente únicamente los bloques horarios de la semana consultada que no tienen una reserva vigente. Una reserva es vigente mientras esté en estado "Pendiente de confirmación" o "Confirmada"; las reservas "Cancelada" y "Sin confirmar" liberan el bloque horario. Un bloque cuya reserva quedó "Finalizada" ya se consumió y NO DEBE (MUST NOT) volver a mostrarse.

#### Scenario: El paciente consulta una semana con bloques horarios libres

- **GIVEN** que la psicóloga definió su disponibilidad para la semana del 9 de noviembre
- **AND** que el bloque del martes 10 de noviembre a las 10:00 tiene una reserva vigente
- **AND** que el bloque del martes 10 de noviembre a las 11:00 está libre
- **WHEN** el paciente consulta la disponibilidad de esa semana
- **THEN** el sistema informa el bloque del martes 10 de noviembre a las 11:00 como disponible
- **AND** no informa el bloque del martes 10 de noviembre a las 10:00

### Requirement: Ofrecer solo bloques reservables

Un bloque reservable DEBE (MUST) comenzar después del instante actual y quedar completo dentro de la jornada de lunes a sábado, de 09:00 a 19:00, según la zona horaria configurada; su término DEBE (MUST) ser posterior a su inicio. El domingo permanece cerrado. La misma regla aplica a las alternativas de reagendamiento y al guardar una reserva o un reagendamiento.

#### Scenario: La semana consultada incluye bloques que ya no son reservables

- **GIVEN** que la semana consultada tiene un bloque cuyo inicio ya pasó, un bloque fuera de la jornada y un bloque futuro dentro de la jornada
- **WHEN** el paciente consulta la disponibilidad de esa semana
- **THEN** el sistema informa solo el bloque futuro dentro de la jornada
- **AND** no permite reservar los otros bloques aunque se envíe el formulario directamente

### Requirement: Informar ausencia de disponibilidad

Cuando la semana consultada no tiene bloques horarios libres, el sistema DEBE (MUST) informar que no hay horas disponibles e indicar la fecha del próximo bloque horario disponible.

#### Scenario: El paciente consulta una semana sin bloques horarios libres

- **GIVEN** que todos los bloques horarios de la semana del 16 de noviembre tienen una reserva vigente
- **WHEN** el paciente consulta la disponibilidad de esa semana
- **THEN** el sistema informa que no hay horas disponibles para esa semana
- **AND** informa la fecha del próximo bloque horario disponible
