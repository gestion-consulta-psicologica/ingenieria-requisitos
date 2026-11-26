# Proposal

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-09.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## Why

La información clínica del paciente no está centralizada. HU-09 permite a la psicóloga consultar y actualizar la ficha clínica en la plataforma, protegiendo el acceso por rol. Historia: **HU-09**; actividad del TO-BE: **Actualizar ficha clínica en sistema centralizado**; caso de uso: **CU-10 — Actualizar ficha clínica**; requisito: **RP-16**; contexto: **RP-17**, **RD-01** y **RD-02**.

## What Changes

- Ficha clínica por paciente con antecedentes de anamnesis editables y conservación de las versiones anteriores.
- Registro de una evolución por cada atención **realizada**, sin edición posterior.
- Acceso exclusivo de la psicóloga; los intentos sin permiso se deniegan y quedan en una bitácora sin contenido clínico, con ficha y usuario.
- Cifrado en reposo de la información clínica (RD-02).
- **Fuera de alcance:** exportación, edición de evoluciones y acceso del paciente a su ficha.

## Capabilities

### New Capabilities

- `ficha-clinica`: consulta y actualización de la ficha clínica con control de acceso y bitácora.

### Modified Capabilities

- Ninguna.

## Impact

- Migraciones `012_ficha_clinica.sql`, `013_antecedentes_clinicos.sql`, `015_bitacora_e_historial_ficha.sql` y `017_historial_ficha_en_codigo.sql`; `app/servicios/cifrado.py`.
- `app/rutas/clinica.py` y la plantilla `ficha_clinica.html`.
