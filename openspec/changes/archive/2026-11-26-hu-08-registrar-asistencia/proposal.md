# Proposal

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-08.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## Why

La psicóloga necesita dejar constancia en la plataforma de si el paciente asistió a cada atención y aplicar el cargo por inasistencia sin justificación. Historia: **HU-08**; actividad del TO-BE: **Registrar asistencia en sistema**; caso de uso: **CU-09 — Registrar asistencia**; requisitos: **RP-15** y **RP-24**.

## What Changes

- Desde su panel, la psicóloga registra para cada atención **programada**: asistió, no asistió o inasistencia justificada (con justificación obligatoria).
- La inasistencia sin justificación crea un cargo de $5.000 asociado al paciente y a la atención.
- El pago de la atención **no se modifica** (decisión del estudiante del 2026-11-25: se mantiene el cobro completo).
- **Fuera de alcance:** cobrar los cargos, notificarlos y modificar un resultado ya registrado.

## Capabilities

### New Capabilities

- `registro-asistencia`: registro del resultado de asistencia de una atención y del cargo por inasistencia sin justificación.

### Modified Capabilities

- Ninguna.

## Impact

- Migración `011_asistencia.sql` (`atencion.justificacion_inasistencia`; `cargo.atencion_id`).
- `registrar_asistencia` en `app/servicios/atenciones.py`, ruta `POST /psicologa/atenciones/{atencion_id}/asistencia` y panel `psicologa.html`.
