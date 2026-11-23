# Spec Delta

## Purpose

Permite a la psicóloga consultar en la plataforma la información del pago de una atención, sus comprobantes de transferencia y las atenciones con pago pendiente, sin modificar el estado del pago.

## ADDED Requirements

### Requirement: Consultar la información del pago y sus comprobantes

El sistema DEBE mostrar, para una Atencion registrada, el nombre y el RUT del paciente, el monto de la atención, el monto pagado y el estado del pago. Si existen comprobantes, DEBE mostrar de cada ComprobanteTransferencia el monto, la fecha de transferencia y la cuenta de destino. La consulta es de solo lectura y NO DEBE modificar el estado del pago.

#### Scenario: La atención tiene un comprobante de pago registrado

- **DADO** que el paciente registró un comprobante de transferencia por $30.000 para su atención del jueves 12 de noviembre
- **CUANDO** la psicóloga consulta el pago de esa atención
- **ENTONCES** el sistema informa el monto, la fecha de la transferencia y la cuenta de destino del comprobante
- **Y** el monto informado es el registrado para la atención, sin tarifas por tipo de atención
- **Y** muestra el nombre y el RUT del paciente de la atención

### Requirement: Informar la ausencia de comprobante y listar atenciones con pago pendiente

Si la Atencion no tiene ningún ComprobanteTransferencia, el sistema DEBE informar que la atención no tiene comprobante de pago. El listado de atenciones con pago pendiente DEBE incluir las atenciones cuyo Pago está en estado "Pendiente".

#### Scenario: La atención no tiene comprobante de pago

- **DADO** que el paciente no ha registrado un comprobante de pago para su atención del jueves 12 de noviembre
- **CUANDO** la psicóloga consulta el pago de esa atención
- **ENTONCES** el sistema informa que la atención no tiene comprobante de pago
- **Y** la atención aparece en el listado de atenciones con pago pendiente

### Requirement: Ofrecer la continuación al registro del estado de pago

Después de mostrar la información y los antecedentes, el sistema DEBE ofrecer la opción de continuar con el registro del estado de pago. El sistema NO DEBE determinar automáticamente el resultado de la comprobación ni modificar el estado del pago; el registro corresponde a HU-06.

#### Scenario: La psicóloga revisa la información y continúa al registro

- **DADO** que la psicóloga ha revisado la información y los antecedentes disponibles de una atención
- **CUANDO** realiza la comprobación del pago
- **ENTONCES** la plataforma le permite continuar con la actividad de registro del estado del pago
- **Y** no determina automáticamente el resultado de la comprobación
- **Y** no modifica el estado del pago
