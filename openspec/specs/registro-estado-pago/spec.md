# registro-estado-pago Specification

## Purpose

Permite a la psicóloga registrar el estado del pago de una atención a partir de los comprobantes que verificó, según EST-02. También cubre el pago de los cargos de $5.000: el paciente registra sus comprobantes y la psicóloga los verifica con las mismas reglas (extensión del 2026-11-25).

## Requirements

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

### Requirement: Registrar el comprobante de un cargo

El sistema DEBE (MUST) permitir al paciente titular registrar uno o más comprobantes de transferencia para un cargo de $5.000 en estado "Pendiente" o "Pago incompleto". Registrar un comprobante NO DEBE (MUST NOT) cambiar el estado del cargo, y un cargo "Pagado" NO DEBE (MUST NOT) admitir nuevos comprobantes.

#### Scenario: El paciente registra el comprobante de un cargo

- **GIVEN** que el paciente tiene un cargo de $5.000 en estado "Pendiente" por cancelar su hora
- **WHEN** registra un comprobante por $5.000 con fecha de transferencia y cuenta de destino
- **THEN** el sistema asocia el comprobante al cargo
- **AND** el cargo sigue en estado "Pendiente" hasta que la psicóloga lo verifique

#### Scenario: El cargo ya está pagado

- **GIVEN** que el cargo está en estado "Pagado"
- **WHEN** el paciente intenta registrar otro comprobante
- **THEN** el sistema no lo registra
- **AND** le informa que el cargo ya está pagado

### Requirement: Verificar el pago de un cargo

La psicóloga DEBE (MUST) poder verificar los comprobantes de un cargo y registrar su estado con las mismas reglas que el pago de la atención: "Pagado" cuando el total comprobado iguala el monto del cargo y "Pago incompleto", con la diferencia pendiente, cuando es menor. Un cargo "Pagado" DEBE (MUST) salir del listado de cargos por cobrar.

#### Scenario: La psicóloga verifica el pago de un cargo

- **GIVEN** que el cargo tiene un comprobante por $5.000 sin verificar
- **WHEN** la psicóloga verifica el comprobante y registra el estado
- **THEN** el cargo queda en estado "Pagado"
- **AND** deja de aparecer en el listado de cargos por cobrar

#### Scenario: El paciente paga el cargo en partes

- **GIVEN** que el cargo tiene un comprobante verificado por $3.000
- **WHEN** la psicóloga registra el estado del cargo
- **THEN** el cargo queda en estado "Pago incompleto"
- **AND** el sistema informa una diferencia pendiente de $2.000
