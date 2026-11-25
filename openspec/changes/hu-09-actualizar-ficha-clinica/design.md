# Design

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-09.md` y del código, para completar la trazabilidad. Queda pendiente la confirmación del estudiante.

## Context

Las atenciones realizadas provienen de HU-08. No hay un diagrama de estado para la ficha.

## Goals / Non-Goals

**Goals:** consultar y actualizar antecedentes; registrar evoluciones de atenciones realizadas sin alterar las anteriores; restringir el acceso por rol (RD-01) con bitácora.

**Non-Goals:** cifrado de datos (RD-02), exportación, roles distintos de psicóloga y paciente.

## Decisions

- **Evolución inmutable:** clave primaria `registro_evolucion.atencion_id`; una por atención.
- **Historial de antecedentes por trigger** (`trg_ficha_clinica_historial`): cada cambio copia la versión anterior a `ficha_clinica_historial`, sin depender del código de la ruta. Los guardados sin cambios no generan versiones.
- **Bitácora sin contenido clínico:** fecha, rol, usuario, `paciente_id`, operación y resultado; se registran lecturas y escrituras permitidas y denegadas.
- **Autorización como dependencia** (`autorizar_ficha`) común a las tres rutas.

## Risks / Trade-offs

- Sin RD-02, la ficha se guarda en texto plano en SQLite; solo deben usarse datos sintéticos hasta implementar el cifrado.
