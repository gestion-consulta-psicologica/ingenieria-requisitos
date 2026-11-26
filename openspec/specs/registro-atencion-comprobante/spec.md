# registro-atencion-comprobante Specification

## Purpose

Permite originar automáticamente la Atencion y el Pago de una Reserva confirmada cuando llega la hora, y que el Paciente registre en la plataforma uno o más comprobantes de su transferencia para que la psicóloga pueda comprobarlos.

## Requirements

### Requirement: Originar automáticamente la Atencion y el Pago

El sistema DEBE (MUST) procesar las Reservas en estado "Confirmada" cuya fecha y hora de atención ya llegaron y que no tienen una Atencion. Por cada una DEBE (MUST) crear una Atencion en estado "programada", un Pago en estado "Pendiente" con el monto de la atención y `montoPagado` en 0, y DEBE (MUST) dejar la Reserva en estado "Finalizada". El procesamiento DEBE (MUST) ser idempotente y NO DEBE (MUST NOT) originar una segunda Atencion para la misma Reserva.

#### Scenario: La reserva confirmada llega a la hora de la atención

- **GIVEN** que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
- **WHEN** llega la hora de la atención
- **THEN** el sistema origina una atención en estado "programada"
- **AND** registra un pago en estado "Pendiente" con el monto registrado para la atención
- **AND** la reserva queda en estado "Finalizada"

#### Scenario: El sistema no duplica una atención ya originada

- **GIVEN** que la reserva confirmada ya tiene una atención originada
- **WHEN** el sistema vuelve a procesar la reserva
- **THEN** no crea una nueva atención ni un nuevo pago
- **AND** la reserva permanece en estado "Finalizada"

### Requirement: Registrar el comprobante de transferencia

Cuando el Pago de una Atencion está en estado "Pendiente" o "Pago incompleto", el sistema DEBE (MUST) ofrecer al Paciente el registro del comprobante desde el detalle de su Reserva. Al guardar un ComprobanteTransferencia con monto, fecha de transferencia y cuenta de destino, DEBE (MUST) asociarlo al Pago, conservar los comprobantes anteriores y dejarlo disponible para la comprobación de HU-05. El registro NO DEBE (MUST NOT) modificar el estado del Pago.

#### Scenario: El paciente registra el comprobante de su transferencia

- **GIVEN** que el paciente tiene una atención registrada con pago pendiente
- **WHEN** registra un comprobante por $30.000 con fecha de transferencia y cuenta de destino
- **THEN** el sistema asocia el comprobante al pago de esa atención
- **AND** el comprobante queda disponible para que la psicóloga lo consulte

#### Scenario: El paciente registra un segundo comprobante

- **GIVEN** que la atención ya tiene un comprobante registrado
- **WHEN** el paciente registra otro comprobante para la misma atención
- **THEN** el sistema conserva el comprobante anterior
- **AND** asocia el nuevo comprobante al mismo pago

#### Scenario: La atención tiene un pago pendiente sin comprobante

- **GIVEN** que la atención tiene un pago en estado "Pendiente" y no tiene comprobantes registrados
- **WHEN** el paciente registra un comprobante
- **THEN** el sistema asocia el comprobante al pago
- **AND** el pago sigue en estado "Pendiente"

### Requirement: Validar los datos del comprobante

El sistema NO DEBE (MUST NOT) registrar el ComprobanteTransferencia si falta el monto, la fecha de transferencia o la cuenta de destino, si el monto no es positivo o si la fecha de transferencia no es válida. En esos casos DEBE (MUST) informar el error al Paciente sin modificar los comprobantes existentes.

#### Scenario: El paciente no completa los datos obligatorios del comprobante

- **GIVEN** que el paciente está registrando un comprobante
- **WHEN** intenta guardar sin monto, fecha de transferencia o cuenta de destino
- **THEN** el sistema no registra el comprobante
- **AND** le informa qué dato falta

#### Scenario: El comprobante tiene datos inválidos

- **GIVEN** que el paciente está registrando un comprobante
- **WHEN** ingresa un monto no positivo o una fecha de transferencia inválida
- **THEN** el sistema no registra el comprobante
- **AND** le informa el error

### Requirement: Rechazar el registro cuando la atención o el pago no lo permiten

El sistema NO DEBE (MUST NOT) permitir el registro de un ComprobanteTransferencia si la Atencion no existe o si el Pago está en estado "Pagado". En esos casos DEBE (MUST) informar el motivo sin modificar datos. Un pago inexistente se considera una inconsistencia de datos, no un caso de negocio: toda Atencion tiene un Pago.

#### Scenario: La atención no existe

- **GIVEN** que el paciente intenta registrar un comprobante para una atención inexistente
- **WHEN** envía los datos del comprobante
- **THEN** el sistema no registra el comprobante
- **AND** le informa que no encontró la atención

#### Scenario: El pago ya está pagado

- **GIVEN** que el pago de la atención está en estado "Pagado"
- **WHEN** el paciente intenta registrar un comprobante
- **THEN** el sistema no habilita el registro
- **AND** le informa que el pago ya está pagado
