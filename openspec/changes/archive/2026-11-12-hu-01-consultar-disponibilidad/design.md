# Design

## Context

La aplicación aún no existe: este cambio crea la base del proyecto con el stack elegido (Python 3.12, FastAPI, Jinja2, SQLite y pytest). La historia **HU-01** solo consulta datos; no crea ni modifica reservas. Ver `proposal.md` para la motivación y `specs/consulta-disponibilidad/spec.md` para los requisitos.

El modelo de dominio define **Psicologa**, **BloqueHorario** y **Reserva**. La disponibilidad no es un atributo almacenado: un bloque está disponible si no tiene una reserva vigente. La regla de vigencia confirmada en EST-01 es: **Pendiente de confirmación** o **Confirmada** bloquean el bloque; **Cancelada** y **Sin confirmar** no lo bloquean.

## Goals / Non-Goals

**Goals:**
- Consultar la disponibilidad de una semana y mostrar solo los bloques libres.
- Informar la ausencia de horas e indicar la fecha del próximo bloque disponible.
- Crear las tablas mínimas del dominio y datos de ejemplo para probar la consulta.
- Implementar una prueba automática por cada escenario Gherkin.

**Non-Goals:**
- Reservar, registrar o modificar reservas.
- Autenticación real; solo un selector de rol de demostración.
- Sistemas externos, pagos, boletas, asistencia o ficha clínica.
- Requisitos no funcionales (rendimiento, seguridad, etc.).

## Decisions

### Tablas derivadas del modelo de dominio

| Tabla | Columnas | Origen |
|-------|----------|--------|
| `psicologa` | `id`, `nombre_completo`, `rut`, `correo` | Clase Psicologa |
| `bloque_horario` | `id`, `psicologa_id`, `fecha`, `hora_inicio`, `hora_termino`, `modalidad` | Clase BloqueHorario; `psicologa_id` implementa `ofrece 1 – 0..*` |
| `reserva` | `id`, `paciente_id`, `bloque_horario_id`, `fecha_registro`, `estado` | Clase Reserva; `bloque_horario_id` implementa `ocupa 0..* – 1` |
| `paciente` | `id`, `nombre_completo`, `rut`, `fecha_nacimiento`, `direccion`, `escolaridad`, `ocupacion`, `telefono`, `correo` | Clase Paciente; se crea para la FK de Reserva y para datos de ejemplo |

`reserva.estado` se restringe a los estados de EST-01. Se crea un índice único parcial sobre `reserva(bloque_horario_id)` para los estados vigentes, de modo que un bloque no pueda tener dos reservas vigentes a la vez. La tabla `paciente` se crea porque toda reserva requiere un paciente según la multiplicidad 1 del modelo; HU-01 no muestra sus datos.

**Alternativa descartada:** guardar un atributo `disponible` en `bloque_horario`. Se descarta porque se desactualizaría al cambiar el estado de una reserva; la disponibilidad se calcula en la consulta.

### Consulta de disponibilidad

La disponibilidad se obtiene con una consulta semanal que excluye los bloques con una reserva en estado vigente. Se usa una subconsulta `NOT EXISTS` sobre `reserva` y no se persiste el resultado.

Ruta derivada de DSS-03 (mensaje «consultar disponibilidad de la semana»):

- `GET /disponibilidad?semana=AAAA-MM-DD`: muestra los bloques libres de la semana que contiene esa fecha. Si no se indica `semana`, se usa la semana actual.
- `GET /`: redirige a `/disponibilidad`.

La fecha del próximo bloque disponible se calcula como el mínimo `fecha` de los bloques futuros sin reserva vigente. Si no existe ninguno, se muestra un mensaje adicional de que no hay próximos bloques.

### Interfaz y rol

Se usa una página Jinja2 con un selector de rol de demostración en la cabecera. HU-01 se muestra para el rol **Paciente**; no se implementa autenticación. La página presenta los bloques agrupados por fecha y, si no hay disponibilidad, el mensaje y la próxima fecha.

### Migraciones y datos de ejemplo

- Migración `app/db/migrations/001_crear_tablas_base.sql` con las tablas anteriores.
- `app/db/seed.py` idempotente con una psicóloga, bloques de las semanas del 9 y 16 de noviembre y reservas de ejemplo: una vigente para el martes 10 a las 10:00 y bloques libres para las 11:00 y la semana siguiente.
- Las migraciones se registran en `schema_migrations` y se aplican al arrancar.

### Pruebas

Una prueba de integración con pytest y `TestClient` por cada escenario Gherkin, usando una base SQLite temporal o en memoria. Las pruebas preparan sus propios datos y no dependen del `seed`.

## Risks / Trade-offs

- **Fechas y zonas horarias** → usar solo `date` para `fecha` y horas locales; no convertir zonas horarias en esta historia.
- **Datos de ejemplo con fechas fijas** → las pruebas crean sus datos; el seed es solo para la demo manual y se documenta como tal.
- **Regla de vigencia duplicada en código y documentos** → centralizarla en una constante y citar EST-01 en el módulo de consulta.
- **Sin autenticación real** → el selector de rol es de demostración; se advierte en el README y en la guía de pruebas.
