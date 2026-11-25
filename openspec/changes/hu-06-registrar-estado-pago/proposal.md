# Proposal

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-06.md` y del código, para completar la trazabilidad. Queda pendiente la confirmación del estudiante.

## Why

Tras comprobar el pago (HU-05), la psicóloga registra hoy el resultado fuera de la plataforma. HU-06 permite registrar en la plataforma el estado del pago de una atención según los comprobantes verificados, siguiendo EST-02. Historia: **HU-06**; actividad del TO-BE: **Registrar estado de pago en sistema**; caso de uso: **CU-07 — Registrar estado de pago**; requisito: **RP-13**.

## What Changes

- La psicóloga selecciona los comprobantes que verificó y guarda el estado del pago desde `/pagos/{atencion_id}`.
- El sistema calcula el total comprobado y solo acepta el estado que corresponde: **Pagado** (total = monto) o **Pago incompleto** (total < monto); un total mayor se rechaza.
- Cada comprobante se marca como verificado para no sumarlo dos veces; se actualiza `montoPagado` y se informa la diferencia pendiente.
- El listado `/pagos` incluye los pagos en **Pago incompleto**.
- **Fuera de alcance:** boleta (HU-07), cobro de cargos, integración bancaria y reversión de un pago Pagado.

## Capabilities

### New Capabilities

- `registro-estado-pago`: registro del estado del pago de una atención a partir de los comprobantes verificados.

### Modified Capabilities

- `comprobacion-pago` (HU-05): la opción «Registrar estado de pago» pasa de inactiva a activa y el listado incluye Pago incompleto.

## Impact

- Migración `010_comprobante_verificado.sql` (`comprobante_transferencia.verificado`).
- `app/servicios/pagos.py` (`verificar_pago`), ruta `POST /pagos/{atencion_id}/estado` y plantilla `pago_detalle.html`.
