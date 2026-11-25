# Tasks

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-06.md` y del código, para completar la trazabilidad. Queda pendiente la confirmación del estudiante.

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

## 5. Cierre

- [ ] 5.1 Confirmación del estudiante de la ficha `.cin324/historias/HU-06.md`.
- [ ] 5.2 Sincronizar la especificación en `openspec/specs/` y archivar el cambio.
