# Tasks

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-09.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## 1. Datos

- [x] 1.1 Migraciones `012` (ficha, evolución, bitácora) y `013` (antecedentes de anamnesis).
- [x] 1.2 Migración `015`: usuario y ficha en la bitácora; `ficha_clinica_historial` y trigger de versiones.

## 2. Rutas y pantallas

- [x] 2.1 `app/rutas/clinica.py`: consulta, antecedentes y evolución, con `autorizar_ficha` y CSRF.
- [x] 2.2 `ficha_clinica.html`: antecedentes, historial de cambios (fechas) y evoluciones.

## 3. Pruebas

- [x] 3.1 `tests/test_hu09_ficha_clinica.py`: registro y denegación con bitácora (ficha y usuario), conservación de evoluciones, historial de antecedentes y guardado sin cambios.

## 4. Cierre

- [x] 4.1 Confirmación del estudiante de la ficha `.cin324/historias/HU-09.md`.
- [ ] 4.2 RD-02 — cifrado de la información sensible (pendiente).
- [ ] 4.3 Sincronizar la especificación en `openspec/specs/` y archivar el cambio.
