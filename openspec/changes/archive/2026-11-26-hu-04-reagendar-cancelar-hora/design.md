# Design - HU-04 Reagendar o cancelar una hora

## Contexto

La reserva es la misma entidad antes y después de un reagendamiento. La cancelación y el reagendamiento solo se permiten desde **Confirmada**, según EST-01 y el escenario de HU-04. Las alternativas se obtienen de los bloques libres de los próximos 14 días.

## Datos

### Migración `006_reagendamiento_cancelacion.sql`

- `reserva.version`: contador del ciclo de confirmación. Inicia en `1`; cada reagendamiento lo incrementa en `1`.
- `solicitud_confirmacion.version`: ciclo al que pertenece la solicitud. Se reconstruye la tabla para eliminar `UNIQUE (reserva_id, tipo)` y reemplazarlo por `UNIQUE (reserva_id, version, tipo)`. Se conserva el índice único parcial `ux_solicitud_pendiente` para impedir más de una solicitud pendiente por reserva.
- `reserva_historial`: registra cancelaciones y reagendamientos con `tipo`, `estado_anterior`, `estado_nuevo`, `bloque_anterior_id`, `bloque_nuevo_id`, `version_anterior`, `version_nueva` y `fecha`. Es una tabla de soporte técnico, no una clase del modelo de dominio.
- La migración se ejecuta con las claves foráneas desactivadas durante la reconstrucción y las vuelve a activar antes de terminar. `correo_pendiente` y `token_confirmacion` conservan sus referencias a `solicitud_confirmacion`.

## Lógica

### Cancelación

1. Abrir transacción `BEGIN IMMEDIATE`.
2. Leer la reserva con su bloque y paciente.
3. Exigir estado **Confirmada**.
4. Actualizar la reserva a **Cancelada** con `WHERE estado = 'Confirmada'`.
5. Insertar el historial con el bloque anterior y `bloque_nuevo_id = NULL`.
6. Confirmar. El bloque queda libre porque **Cancelada** no es un estado vigente.

No se encola un correo de cancelación porque los artefactos no lo exigen.

### Alternativas

Se consultan bloques con `fecha` entre hoy y hoy + 13 días, excluyendo el bloque actual y cualquier bloque con una reserva en estado **Pendiente de confirmación** o **Confirmada**. La reserva original no se modifica al consultar.

### Reagendamiento

1. Abrir transacción `BEGIN IMMEDIATE`.
2. Leer la reserva; exigir **Confirmada**.
3. Leer el bloque nuevo; exigir que exista, que sea distinto del actual y que esté libre.
4. Actualizar la misma reserva con `bloque_horario_id = nuevo`, `estado = 'Pendiente de confirmación'`, `version = version + 1`, usando `WHERE estado = 'Confirmada' AND version = version_anterior`.
5. Insertar el historial con ambos bloques y ambas versiones.
6. Encolar el aviso de reserva reagendada con clave idempotente `aviso_reagendamiento:{reserva_id}:{version_nueva}`.
7. Confirmar la transacción.
8. Si la restricción única de reserva vigente falla por concurrencia, revertir y devolver **409** sin cambiar la reserva.

El bloque anterior se libera porque la misma fila de reserva deja de referenciarlo y el nuevo bloque queda ocupado.

### Ciclo de confirmación

- `confirmacion.py` consulta solicitudes filtrando por `reserva.version` en `_obtener_solicitud`, `_ultima_solicitud` y `_solicitud_pendiente`.
- Al reactivar la reserva en **Pendiente de confirmación**, el planificador puede crear la víspera y el recordatorio del nuevo ciclo.
- Las solicitudes del ciclo anterior se conservan como historial y sus tokens ya no son válidos porque la solicitud está respondida o cerrada.
- El índice parcial de solicitud pendiente sigue siendo global por reserva, por lo que nunca hay dos pendientes simultáneas.

### Rutas

- `GET /reservas/{id}`: muestra acciones solo si `estado == "Confirmada"` e historial si existe.
- `POST /reservas/{id}/cancelar`: cancela y redirige al detalle.
- `GET /reservas/{id}/reagendar`: muestra alternativas; si la reserva no está confirmada devuelve 409.
- `POST /reservas/{id}/reagendar` con `bloque_id`: reagenda o muestra el error con las alternativas restantes.
- Códigos: 404 reserva/bloque inexistente; 409 reserva no confirmada o bloque no disponible.

## Correo

Se agrega `aviso_reagendamiento` a `plantillas_correo.py` con fecha anterior, fecha nueva, modalidad y número de reserva. Se encola con el tipo existente `aviso_reserva` y una clave idempotente propia; la interfaz distingue el aviso por la clave. Si el paciente no tiene correo, queda `omitido`, igual que los demás avisos.

## Pruebas

- Cancelación confirmada, liberación del bloque, historial y rechazo desde **Pendiente de confirmación**.
- Alternativas: exclusión del bloque actual, bloques ocupados y fechas fuera de los 14 días.
- Sin alternativas: reserva original intacta.
- Reagendamiento exitoso: misma reserva, nueva versión, bloque anterior libre, bloque nuevo ocupado, historial y correo encolado.
- Bloque tomado: reversión total y reserva original intacta.
- Nuevo ciclo: una solicitud del ciclo 1 no impide la víspera del ciclo 2; la respuesta del ciclo 2 confirma la reserva.
- Rutas y pantallas: acciones visibles, alternativas, reagendamiento y cancelación.

## Riesgos y decisiones

- **Historial:** se implementa como tabla de soporte para conservar el bloque anterior; no se agrega una pantalla de auditoría separada ni se modifica el modelo de dominio.
- **Correo:** no se crea un nuevo tipo en `correo_pendiente` para evitar una segunda reconstrucción; la clave idempotente y el asunto identifican el aviso reagendado.
- **Reservas pendientes:** no se cancelan ni reagendan por HU-04; su cancelación sigue siendo la respuesta «no asistirá» de HU-03.
- **14 días:** se toma literalmente de los criterios de aceptación y se calcula desde la fecha local actual.
