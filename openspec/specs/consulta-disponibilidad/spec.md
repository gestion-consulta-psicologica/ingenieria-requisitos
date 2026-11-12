# consulta-disponibilidad Specification

## Purpose

Permite al Paciente consultar la disponibilidad semanal de bloques horarios de la psicóloga y conocer cuándo no hay horas disponibles ni cuál es la próxima fecha disponible.

## Requirements

### Requirement: Mostrar bloques horarios disponibles

El sistema DEBE mostrar al Paciente únicamente los bloques horarios de la semana consultada que no tienen una reserva vigente. Una reserva es vigente mientras esté en estado "Pendiente de confirmación" o "Confirmada"; las reservas "Cancelada" y "Sin confirmar" no bloquean el bloque horario.

#### Scenario: El paciente consulta una semana con bloques horarios libres

- **DADO** que la psicóloga definió su disponibilidad para la semana del 9 de noviembre
- **Y** que el bloque del martes 10 de noviembre a las 10:00 tiene una reserva vigente
- **Y** que el bloque del martes 10 de noviembre a las 11:00 está libre
- **CUANDO** el paciente consulta la disponibilidad de esa semana
- **ENTONCES** el sistema informa el bloque del martes 10 de noviembre a las 11:00 como disponible
- **Y** no informa el bloque del martes 10 de noviembre a las 10:00

### Requirement: Informar ausencia de disponibilidad

Cuando la semana consultada no tiene bloques horarios libres, el sistema DEBE informar que no hay horas disponibles e indicar la fecha del próximo bloque horario disponible.

#### Scenario: El paciente consulta una semana sin bloques horarios libres

- **DADO** que todos los bloques horarios de la semana del 16 de noviembre tienen una reserva vigente
- **CUANDO** el paciente consulta la disponibilidad de esa semana
- **ENTONCES** el sistema informa que no hay horas disponibles para esa semana
- **Y** informa la fecha del próximo bloque horario disponible
