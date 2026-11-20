# Spec Delta

## Purpose

Permite originar automáticamente la Atencion y el Pago de una Reserva confirmada cuando llega la hora, y que el Paciente registre en la plataforma uno o más comprobantes de su transferencia para que la psicóloga pueda comprobarlos.

## ADDED Requirements

### Requirement: Originar automáticamente la Atencion y el Pago

El sistema DEBE procesar las Reservas en estado "Confirmada" cuya fecha y hora de atención ya llegaron y que no tienen una Atencion. Por cada una DEBE crear una Atencion en estado "programada" y un Pago en estado "Pendiente" con el monto de la atención y `montoPagado` en 0. El procesamiento DEBE ser idempotente y NO DEBE originar una segunda Atencion para la misma Reserva.

#### Scenario: La reserva confirmada llega a la hora de la atención

- **DADO** que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
- **CUANDO** llega la hora de la atención
- **ENTONCES** el sistema origina una atención en estado "programada"
- **Y** registra un pago en estado "Pendiente" con el monto registrado para la atención

#### Scenario: El sistema no duplica una atención ya originada

- **DADO** que la reserva confirmada ya tiene una atención originada
- **CUANDO** el sistema vuelve a procesar la reserva
- **ENTONCES** no crea una nueva atención ni un nuevo pago

### Requirement: Registrar el comprobante de transferencia

Cuando el Pago de una Atencion está en estado "Pendiente" o "Pago incompleto", el sistema DEBE ofrecer al Paciente el registro del comprobante desde el detalle de su Reserva. Al guardar un ComprobanteTransferencia con monto, fecha de transferencia y cuenta de destino, DEBE asociarlo al Pago, conservar los comprobantes anteriores y dejarlo disponible para la comprobación de HU-05. El registro NO DEBE modificar el estado del Pago.

#### Scenario: El paciente registra el comprobante de su transferencia

- **DADO** que el paciente tiene una atención registrada con pago pendiente
- **CUANDO** registra un comprobante por $30.000 con fecha de transferencia y cuenta de destino
- **ENTONCES** el sistema asocia el comprobante al pago de esa atención
- **Y** el comprobante queda disponible para que la psicóloga lo consulte

#### Scenario: El paciente registra un segundo comprobante

- **DADO** que la atención ya tiene un comprobante registrado
- **CUANDO** el paciente registra otro comprobante para la misma atención
- **ENTONCES** el sistema conserva el comprobante anterior
- **Y** asocia el nuevo comprobante al mismo pago

### Requirement: Validar los datos del comprobante

El sistema NO DEBE registrar el ComprobanteTransferencia si falta el monto, la fecha de transferencia o la cuenta de destino, si el monto no es positivo o si la fecha de transferencia no es válida. En esos casos DEBE informar el error al Paciente sin modificar los comprobantes existentes.

#### Scenario: El paciente no completa los datos obligatorios del comprobante

- **DADO** que el paciente está registrando un comprobante
- **CUANDO** intenta guardar sin monto, fecha de transferencia o cuenta de destino
- **ENTONCES** el sistema no registra el comprobante
- **Y** le informa qué dato falta

#### Scenario: El comprobante tiene datos inválidos

- **DADO** que el paciente está registrando un comprobante
- **CUANDO** ingresa un monto no positivo o una fecha de transferencia inválida
- **ENTONCES** el sistema no registra el comprobante
- **Y** le informa el error

### Requirement: Rechazar el registro cuando la atención o el pago no lo permiten

El sistema NO DEBE permitir el registro de un ComprobanteTransferencia si la Atencion no existe, si no tiene un Pago asociado o si el Pago está en estado "Pagado". En esos casos DEBE informar el motivo sin modificar datos.

#### Scenario: La atención no tiene pago asociado

- **DADO** que la atención no tiene un pago asociado
- **CUANDO** el paciente intenta registrar un comprobante
- **ENTONCES** el sistema no registra el comprobante
- **Y** le informa que no encontró el pago de la atención

#### Scenario: El pago ya está pagado

- **DADO** que el pago de la atención está en estado "Pagado"
- **CUANDO** el paciente intenta registrar un comprobante
- **ENTONCES** el sistema no habilita el registro
- **Y** le informa que el pago ya está pagado
