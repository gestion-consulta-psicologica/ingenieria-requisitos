# Design — HU-02 Reservar una hora

## Context

La aplicación ya tiene la consulta de disponibilidad (HU-01) sobre FastAPI + Jinja2 + SQLite, con las tablas `psicologa`, `paciente`, `bloque_horario` y `reserva` creadas en la migración `001_crear_tablas_base.sql`. La reserva ya tiene el estado inicial y el índice único `idx_reserva_vigente`, que impide dos reservas vigentes para el mismo bloque. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Reservar un bloque disponible para un Paciente registrado y dejarlo en estado "Pendiente de confirmación".
- Reutilizar la regla de vigencia de EST-01 y el índice único existente para evitar dobles reservas.
- Simular el Servicio de mensajería mediante un adaptador sustituible.
- Cubrir los tres escenarios Gherkin con pruebas automáticas.

**Non-Goals:**
- Registrar pacientes nuevos: la página `/pacientes/registro` y el retorno a la reserva se implementan en HU-02A.
- Confirmar, cancelar o reagendar reservas (HU-03 y HU-04).
- Crear `SolicitudConfirmacion`; el aviso de HU-02 no es la solicitud de confirmación.
- Autenticación real y requisitos no funcionales.

## Decisions

- **Sin migración nueva:** las tablas y restricciones de `001` ya cubren la historia. La reserva usa `fecha_registro` con la fecha y hora actuales y `estado = 'Pendiente de confirmación'`. Se descarta crear una migración solo para la historia.
- **Unicidad y concurrencia:** se reutiliza el índice parcial `idx_reserva_vigente` de EST-01. La comprobación previa de disponibilidad da el mensaje amigable; si el bloque se toma entre la comprobación y el `INSERT`, la violación de unicidad se captura y se responde igual que «bloque ya no está disponible». Así se cubre la variante de DSS-03 sin bloqueos explícitos.
- **RUT normalizado:** la búsqueda del Paciente normaliza el RUT (sin puntos ni guion, con K mayúscula) tanto en la entrada como en la comparación. Se descarta exigir un formato exacto porque el seed y los datos de ejemplo usan puntos y guion.
- **Rutas derivadas de DSS-03:** `GET /reservar/{bloque_id}` muestra el formulario con el bloque y el campo RUT; `POST /reservar/{bloque_id}` procesa la reserva; `GET /reservas/{reserva_id}` muestra la confirmación y el aviso enviado. Se usa el patrón POST-Redirect-GET para evitar reenvíos.
- **Bloque tomado:** se vuelve a renderizar el formulario con el mensaje «El bloque ya no está disponible» y la lista de los bloques disponibles más cercanos. Se agrega `obtener_bloques_cercanos` al servicio de disponibilidad reutilizando su consulta.
- **RUT no registrado:** se responde `303` a `/pacientes/registro?bloque_id=<id>`. La ruta destino se implementa en HU-02A; en este cambio solo se verifica la derivación y que no se crea la reserva.
- **Mensajería simulada:** `ServicioMensajeria` es una interfaz con `enviar_aviso_reserva(...)`; `ServicioMensajeriaSimulado` registra el aviso con `logging` y devuelve éxito. `crear_app` acepta un `servicio_mensajeria` opcional para inyectar un doble de prueba; por defecto usa el simulado. Alternativa descartada: tabla de log de integraciones, innecesaria para esta historia.
- **Estados:** solo se implementa la transición inicial de EST-01 (`(inicial) → Pendiente de confirmación`) con la acción «ocupar bloque y enviar aviso de reserva». Las demás transiciones quedan para sus historias.
- **Vocabulario:** se mantienen `Reserva`, `BloqueHorario` y `Paciente`, y los textos «Pendiente de confirmación», «aviso de reserva registrada» y «bloque ya no está disponible».

## Risks / Trade-offs

- **El destino `/pacientes/registro` no existe hasta HU-02A** → la prueba de HU-02 verifica el `303` y que no se creó la reserva; el retorno completo se prueba en HU-02A.
- **Condición de carrera entre dos pacientes** → el índice único parcial garantiza que solo una reserva vigente quede registrada; la otra recibe el mensaje de bloque no disponible.
- **RUT con formatos distintos** → se normaliza antes de comparar; un RUT con dígito verificador incorrecto no se valida en esta historia (no está en el Gherkin).
- **Bloques de ejemplo en fechas pasadas** → las pruebas crean sus propios bloques en una base temporal; los datos de ejemplo no condicionan la reserva.

## Migration Plan

No hay cambios de esquema. Al arrancar, la migración `001` ya existente crea las tablas. Para volver atrás basta con retirar el router y las plantillas nuevas; los datos de reserva creados pueden eliminarse con la base local.

## Open Questions

Ninguna que afecte las especificaciones. El texto exacto de los mensajes de error se define en las plantillas y se puede ajustar en la revisión, sin cambiar el comportamiento.
