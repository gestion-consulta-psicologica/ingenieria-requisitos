# Design

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-08.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## Context

La atención se origina en estado `programada` al llegar la hora de una reserva confirmada (HU-05A). EST-04 define sus transiciones finales.

## Goals / Non-Goals

**Goals:** aplicar las transiciones de EST-04; crear el cargo por inasistencia sin justificación en la misma transacción.

**Non-Goals:** cobrar cargos, modificar el pago, editar resultados.

## Decisions

- **Cargo asociado a la atención:** la tabla `cargo` admite `reserva_id` (HU-03/HU-04) o `atencion_id` (HU-08), exactamente uno (`CHECK`).
- **Resultados finales:** solo se registra desde `programada`; un segundo registro responde 409.
- **Justificación obligatoria** para «inasistencia justificada»; su validez la decide la psicóloga.
- **Pago intacto:** el estado del pago sigue su propio ciclo (EST-02), como exige CA4.

## Risks / Trade-offs

- Ante una inasistencia, el paciente debe la sesión completa más el cargo; la atención sigue en `/pagos` hasta registrar su pago. Fue confirmado por el estudiante.
