# Spec Delta

## Purpose

Permite a la psicóloga registrar el estado del pago de una atención a partir de los comprobantes que verificó, según EST-02.

## ADDED Requirements

### Requirement: Registrar un pago verificado como Pagado

Cuando el total de los comprobantes verificados iguala el monto de la atención, el sistema DEBE (MUST) dejar el Pago en estado "Pagado", asociado al paciente y a la atención, registrar el monto pagado, mostrar una confirmación y excluir la atención del listado de pagos pendientes.

#### Scenario: La psicóloga registra un pago verificado

- **GIVEN** que la atención del jueves 12 de noviembre tiene un comprobante por $30.000
- **AND** que el monto del comprobante coincide con el monto de la atención
- **WHEN** la psicóloga registra el pago como verificado
- **THEN** el pago queda en estado "Pagado" asociado al paciente y a la atención
- **AND** la atención deja de aparecer en el listado de atenciones con pago pendiente

### Requirement: Registrar un pago parcial como Pago incompleto

Cuando el total verificado es menor que el monto de la atención, el sistema DEBE (MUST) dejar el Pago en estado "Pago incompleto" e informar la diferencia pendiente. Un nuevo comprobante verificado DEBE (MUST) sumarse al monto pagado hasta completar el monto. El sistema NO DEBE (MUST NOT) aceptar un total mayor al monto ni un estado que no corresponda al total.

#### Scenario: El monto del comprobante no coincide con el de la atención

- **GIVEN** que la atención del jueves 12 de noviembre tiene un monto de $30.000
- **AND** que el comprobante registrado es por $20.000
- **WHEN** la psicóloga revisa el pago
- **THEN** el pago queda en estado "Pago incompleto"
- **AND** el sistema informa una diferencia pendiente de $10.000
