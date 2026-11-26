# Tasks

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-06.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## 1. Datos

- [x] 1.1 Migración `010_comprobante_verificado.sql` con `comprobante_transferencia.verificado`.

## 2. Lógica

- [x] 2.1 `verificar_pago` en `app/servicios/pagos.py`: total comprobado, validación contra EST-02 y transacción única.

## 3. Rutas y pantallas

- [x] 3.1 `POST /pagos/{atencion_id}/estado` con acceso de psicóloga y CSRF; `pago_detalle.html` con selección de comprobantes, estado y diferencia pendiente.
- [x] 3.2 `/pagos` incluye Pago incompleto.

## 4. Pruebas

- [x] 4.1 `tests/test_recorrido_integrado.py::test_psicologa_verifica_pago_parcial_y_completa_el_saldo` (pago parcial, diferencia y saldo completado).
- [x] 4.2 `tests/test_hu05_comprobar_pago.py` verifica que la opción de registrar el estado está activa.

## 5. Extensión: pago de cargos (2026-11-25)

- [x] 5.0.1 Migración `018_pago_de_cargos.sql`: `cargo.estado`, `cargo.monto_pagado` y tabla `comprobante_cargo`.
- [x] 5.0.2 `app/servicios/cargos.py` y `app/rutas/cargos.py`: «Mis cargos», registro de comprobantes, «Cargos por cobrar» y verificación con CSRF.
- [x] 5.0.3 Enlaces en el menú, el panel y el detalle de la reserva; pruebas en `tests/test_hu06_pagar_cargo.py`.

## 5. Cierre

- [x] 5.1 Confirmación del estudiante de la ficha `.cin324/historias/HU-06.md`.
- [x] 5.2 Sincronizar la especificación en `openspec/specs/` y archivar el cambio (2026-11-26).
