# Proposal

## Why

HU-05 permite consultar el pago de una atención, pero los datos de la atención y del pago solo existen como ejemplo. Falta que el sistema origine automáticamente la atención y el pago cuando llega la hora de una reserva confirmada, y que el paciente registre el comprobante de su transferencia en la plataforma en lugar de enviarlo por WhatsApp. Sin esta historia, HU-05 no tiene un flujo real que alimente la comprobación del pago.

## What Changes

- Procesar automáticamente, de forma idempotente, las reservas en estado **Confirmada** cuya fecha y hora de atención ya llegaron y que todavía no tienen una `Atencion`.
- Crear por cada reserva procesada una `Atencion` en estado `programada` y un `Pago` en estado `Pendiente`, con el monto configurable de la atención y `montoPagado = 0`.
- Mostrar en el detalle de la reserva el enlace **«Registrar comprobante de pago»** cuando exista una atención con pago en estado `Pendiente` o `Pago incompleto`.
- Permitir al paciente registrar uno o más `ComprobanteTransferencia` con monto, fecha de transferencia y cuenta de destino, conservando los comprobantes anteriores.
- Validar los datos obligatorios, el monto positivo y la fecha de transferencia; informar los errores sin registrar el comprobante.
- Mantener el estado del pago sin cambios: la verificación y las transiciones de EST-02 pertenecen a HU-06.
- Reutilizar las tablas `atencion`, `pago` y `comprobante_transferencia` creadas en la migración `007` de HU-05; no se agregan tablas de negocio nuevas.
- Agregar datos de ejemplo y pruebas de integración para los escenarios de la historia.

**Fuera de alcance:** comprobar el pago (HU-05 / CU-06), registrar el estado de pago o aplicar transiciones de EST-02 (HU-06 / CU-07), emitir boleta (HU-07 / CU-08), registrar asistencia o cambiar el estado de `Atencion` (HU-08 / CU-09), autenticación real, cálculo de tarifas por tipo de atención, integración bancaria y notificaciones por correo.

## Capabilities

### New Capabilities

- `registro-atencion-comprobante`: origen automático de la atención y su pago desde una reserva confirmada, y registro del comprobante de transferencia por el paciente, sin modificar el estado del pago.

### Modified Capabilities

- Ninguna.

## Impact

- Nueva lógica de procesamiento automático de reservas vencidas, integrada al ciclo del planificador existente.
- Nuevo servicio de registro de comprobantes y validaciones.
- Nuevas rutas y pantalla de registro de comprobante, y un enlace en el detalle de la reserva.
- Ajustes al seed para demostrar una reserva confirmada vencida sin atención y mantener los datos de ejemplo de HU-05.
- Pruebas de integración para los escenarios Gherkin de HU-05A.
- No modifica la migración `007_atencion_pago.sql` ni las tablas de reservas, pacientes, bloques, confirmaciones, cargos o correo.
- Requisito funcional: **RP-23**. Actividad TO-BE: **Realizar pago**. Caso de uso: **CU-12 — Registrar comprobante de pago**.
