# reagendamiento-cancelacion Specification

## Purpose

Permite al Paciente gestionar una reserva confirmada: cancelarla y liberar el bloque, consultar alternativas de los próximos 14 días, seleccionar un nuevo horario y actualizar la misma reserva. Conserva el bloque anterior en un historial y reinicia el ciclo de solicitudes de confirmación.

## Requirements

### Requirement: Mostrar las opciones de gestión de una reserva confirmada

El sistema DEBE (MUST) mostrar al Paciente las opciones **Reagendar hora** y **Cancelar reserva** en el detalle de una reserva en estado **Confirmada**.

#### Scenario: El paciente accede a las opciones de gestión

- **GIVEN** que el paciente tiene una reserva confirmada
- **WHEN** accede al detalle de su reserva
- **THEN** el sistema le permite elegir entre reagendar o cancelar la hora

### Requirement: Cancelar una reserva confirmada y liberar el bloque

Cuando el Paciente confirma la cancelación de una reserva **Confirmada**, el sistema DEBE (MUST) cambiar la reserva a **Cancelada**, liberar el bloque y registrar el cambio en el historial. La operación DEBE rechazarse con HTTP 409 si la reserva no está confirmada.

#### Scenario: El paciente cancela una reserva

- **GIVEN** que el paciente tiene una reserva confirmada para el viernes 13 de noviembre a las 18:00
- **WHEN** el paciente cancela la reserva
- **THEN** la reserva queda en estado "cancelada"
- **AND** se registra un cargo de $5.000 asociado al paciente y la reserva y se encola su aviso
- **AND** el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible

#### Scenario: La psicóloga cancela una reserva confirmada

- **GIVEN** que la psicóloga tiene acceso a la gestión de una reserva confirmada sin atención asociada
- **WHEN** confirma la cancelación
- **THEN** la reserva queda en estado "cancelada" y se registra el cambio en el historial
- **AND** el sistema no genera un cargo al paciente

### Requirement: Consultar alternativas de reagendamiento

Cuando el Paciente solicita reagendar una reserva **Confirmada**, el sistema DEBE (MUST) informar los bloques horarios libres de los próximos 14 días, excluyendo el bloque actual y los bloques con reservas vigentes. La reserva original DEBE mantenerse vigente mientras no se elija una alternativa.

#### Scenario: El paciente solicita reagendar y existen alternativas

- **GIVEN** que el paciente tiene una reserva confirmada para el viernes 13 de noviembre a las 18:00
- **AND** que existen bloques horarios disponibles en las dos semanas siguientes
- **WHEN** el paciente solicita reagendar la reserva
- **THEN** el sistema informa los bloques horarios disponibles como alternativas
- **AND** la reserva original se mantiene vigente mientras el paciente no elija una alternativa

#### Scenario: El paciente solicita reagendar y no existen alternativas

- **GIVEN** que el paciente tiene una reserva confirmada
- **AND** que no existen bloques horarios disponibles en las dos semanas siguientes
- **WHEN** el paciente solicita reagendar la reserva
- **THEN** el sistema informa que no hay alternativas disponibles
- **AND** la reserva original se mantiene vigente

### Requirement: Reagendar a un bloque disponible

Cuando el Paciente elige un bloque disponible, el sistema DEBE (MUST) actualizar la misma reserva al nuevo bloque, dejarla en **Pendiente de confirmación**, liberar el bloque anterior, registrar el cambio en el historial e iniciar un nuevo ciclo de confirmación. También DEBE (MUST) encolar el aviso de reserva reagendada.

#### Scenario: El paciente elige una alternativa disponible

- **GIVEN** que el paciente solicitó reagendar su reserva del viernes 13 de noviembre a las 18:00
- **AND** que el bloque del lunes 16 de noviembre a las 17:00 está disponible
- **WHEN** el paciente elige el bloque del lunes 16 de noviembre a las 17:00
- **THEN** la reserva queda asociada al lunes 16 de noviembre a las 17:00 en estado "pendiente de confirmación"
- **AND** el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible
- **AND** el sistema encola y envía al paciente el aviso de la reserva reagendada por correo electrónico

### Requirement: Rechazar un bloque que ya fue tomado

Si el bloque elegido deja de estar disponible antes de confirmar el reagendamiento, el sistema DEBE (MUST) rechazar el cambio con HTTP 409, informar que el bloque ya no está disponible y conservar la reserva original sin cambios.

#### Scenario: La alternativa elegida fue tomada por otro paciente

- **GIVEN** que el paciente solicitó reagendar su reserva
- **AND** que el bloque del lunes 16 de noviembre a las 17:00 fue reservado por otro paciente
- **WHEN** el paciente elige el bloque del lunes 16 de noviembre a las 17:00
- **THEN** el sistema rechaza el cambio indicando que el bloque ya no está disponible
- **AND** la reserva original se mantiene sin cambios

### Requirement: Mantener el historial de cambios de la reserva

Cada cancelación o reagendamiento DEBE (MUST) registrar en `reserva_historial` el estado anterior, el estado nuevo, el bloque anterior, el bloque nuevo cuando corresponda y las versiones del ciclo. El historial DEBE poder consultarse desde el detalle de la reserva.

#### Scenario: El historial conserva el bloque anterior

- **GIVEN** que el paciente reagendó una reserva confirmada a un nuevo bloque
- **WHEN** consulta el detalle de la reserva
- **THEN** el sistema muestra el cambio con el bloque anterior y el nuevo bloque
- **AND** el bloque anterior queda registrado aunque la reserva ya apunte al nuevo bloque

### Requirement: Rechazar la gestión de una reserva no confirmada

El sistema NO DEBE (MUST NOT) cancelar ni reagendar una reserva que no esté en estado **Confirmada**. La operación DEBE responder con HTTP 409 sin modificar la reserva.

#### Scenario: El paciente intenta gestionar una reserva pendiente

- **GIVEN** que el paciente tiene una reserva en estado "pendiente de confirmación"
- **WHEN** intenta cancelarla o reagendarla desde la gestión de la reserva
- **THEN** el sistema rechaza la operación con HTTP 409
- **AND** la reserva conserva su estado y su bloque sin cambios

### Requirement: Mantener las solicitudes de confirmación por ciclo

Las solicitudes de confirmación DEBEN (MUST) pertenecer al ciclo actual de la reserva. Un reagendamiento DEBE incrementar el ciclo y permitir nuevas solicitudes de víspera y recordatorio, sin eliminar las solicitudes del ciclo anterior. Las solicitudes anteriores NO DEBEN (MUST NOT) admitir nuevas respuestas.

#### Scenario: El reagendamiento inicia un nuevo ciclo

- **GIVEN** que la reserva tiene una solicitud respondida del ciclo anterior
- **WHEN** el paciente reagenda a un bloque disponible
- **THEN** la reserva queda pendiente de confirmación en un ciclo nuevo
- **AND** el sistema puede registrar la víspera y el recordatorio del ciclo nuevo
- **AND** la solicitud anterior se conserva como historial y no admite otra respuesta
