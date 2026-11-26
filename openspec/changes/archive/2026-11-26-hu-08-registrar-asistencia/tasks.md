# Tasks

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-08.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## 1. Datos

- [x] 1.1 Migración `011_asistencia.sql`: `atencion.justificacion_inasistencia` y `cargo.atencion_id` con `CHECK` de asociación única.

## 2. Lógica

- [x] 2.1 `registrar_asistencia` en `app/servicios/atenciones.py`: transiciones de EST-04 y cargo en una transacción.

## 3. Rutas y pantallas

- [x] 3.1 `POST /psicologa/atenciones/{atencion_id}/asistencia` con acceso de psicóloga y CSRF; formulario y confirmación en `psicologa.html`.

## 4. Pruebas

- [x] 4.1 `tests/test_recorrido_integrado.py::test_psicologa_registra_asistencia_sin_cambiar_el_pago` (tres resultados, cargo y pago sin cambios).

## 5. Cierre

- [x] 5.1 Regla del pago ante inasistencia decidida por el estudiante (2026-11-25): se mantiene el cobro completo.
- [x] 5.2 Confirmación del estudiante de la ficha `.cin324/historias/HU-08.md`.
- [x] 5.3 Sincronizar la especificación en `openspec/specs/` y archivar el cambio (2026-11-26).
