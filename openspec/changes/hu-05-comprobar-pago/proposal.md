# Proposal

## Why

La psicóloga comprueba hoy los pagos revisando comprobantes enviados por WhatsApp, sin una vista centralizada de la atención y su pago. HU-05 permite consultar en la plataforma la información del pago y los comprobantes asociados, manteniendo la verificación como responsabilidad de la psicóloga.

## What Changes

- Nueva consulta de pago por atención para el rol Psicóloga (CU-06 — Comprobar pago).
- Muestra el nombre y el RUT del paciente (identificador único), el monto de la atención, el monto pagado y el estado del pago.
- Muestra los comprobantes de transferencia disponibles (monto, fecha de transferencia y cuenta de destino) o informa que la atención no tiene comprobante.
- Incluye un listado de atenciones con pago pendiente.
- Ofrece la opción «Registrar estado de pago» visible e inactiva hasta HU-06; no calcula ni modifica el estado del pago.
- Agrega las tablas y datos de ejemplo de `Atencion`, `Pago` y `ComprobanteTransferencia` necesarios para consultar.
- **Fuera de alcance:** registrar el estado de pago (HU-06), emitir boleta (HU-07), crear automáticamente la atención y registrar el comprobante (HU-05A), autenticación real y cálculo de montos o cuentas de destino.

## Capabilities

### New Capabilities

- `comprobacion-pago`: consulta de la información del pago de una atención, sus comprobantes de transferencia y el listado de atenciones con pago pendiente, sin modificar el estado del pago.

### Modified Capabilities

- Ninguna.

## Impact

- Nuevas tablas `atencion`, `pago` y `comprobante_transferencia`, con una migración nueva.
- Nuevas rutas y pantallas de consulta para el rol Psicóloga.
- Datos de ejemplo en el seed para una atención con comprobante y otra sin comprobante.
- Pruebas de integración para los escenarios Gherkin de HU-05.
- No modifica reservas, pacientes, confirmaciones, cargos ni correo.
