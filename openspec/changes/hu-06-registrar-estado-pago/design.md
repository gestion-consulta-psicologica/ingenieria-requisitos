# Design

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-06.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## Context

Las tablas `atencion`, `pago` y `comprobante_transferencia` existen desde HU-05 (migración `007`) y el paciente registra comprobantes en HU-05A. EST-02 define las transiciones del Pago.

## Goals / Non-Goals

**Goals:** aplicar las transiciones de EST-02 desde la verificación de la psicóloga; impedir estados que no coincidan con el monto comprobado; soportar varios comprobantes por pago.

**Non-Goals:** boleta, cobro de cargos, conciliación bancaria, reversión de pagos.

## Decisions

- **Verificación por comprobante** (columna `verificado`): permite la transición interna de `Pago incompleto` sin volver a sumar comprobantes ya considerados.
- **Estado elegido = estado calculado:** CA1 pide que la psicóloga seleccione el estado; el sistema lo valida contra EST-02 en vez de calcularlo en silencio, y rechaza con 409 si no coincide.
- **Transacción única** (`BEGIN IMMEDIATE`): comprobantes, `montoPagado` y `estado` cambian juntos.
- **Nombres canónicos** `Pagado` / `Pago incompleto` (EST-02), aunque el Gherkin los escribe en minúscula.
- **Acceso:** solo la psicóloga (demo: credenciales; modo con cuentas: sesión) y formulario con token CSRF.

## Risks / Trade-offs

- Un comprobante erróneo que haga superar el monto no puede verificarse; la psicóloga debe dejarlo sin seleccionar.
