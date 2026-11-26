# Design

> **Cambio documentado de forma retroactiva (2026-11-25).** La implementación se integró en el commit `cec5538` antes de abrir este cambio. Este cambio registra la propuesta, el diseño y la especificación a partir de la ficha `.cin324/historias/HU-09.md` y del código, para completar la trazabilidad. El estudiante confirmó la ficha el 2026-11-25.

## Context

Las atenciones realizadas provienen de HU-08. No hay un diagrama de estado para la ficha.

## Goals / Non-Goals

**Goals:** consultar y actualizar antecedentes; registrar evoluciones de atenciones realizadas sin alterar las anteriores; restringir el acceso por rol (RD-01) con bitácora.

**Non-Goals:** exportación, roles distintos de psicóloga y paciente.

## Decisions

- **Evolución inmutable:** clave primaria `registro_evolucion.atencion_id`; una por atención.
- **Historial de antecedentes:** cada cambio real copia la versión anterior (cifrada) a `ficha_clinica_historial`. Primero lo hacía un trigger (migración `015`); con el cifrado, la comparación pasó al código (migración `017`), que compara el texto descifrado. Los guardados sin cambios no generan versiones.
- **Bitácora sin contenido clínico:** fecha, rol, usuario, `paciente_id`, operación y resultado; se registran lecturas y escrituras permitidas y denegadas.
- **Autorización como dependencia** (`autorizar_ficha`) común a las tres rutas.

## Risks / Trade-offs

- **RD-02:** la ficha se cifra en reposo con Fernet y una clave fuera de la base. Si la clave se pierde, la información clínica no se recupera; debe respaldarse por separado.
