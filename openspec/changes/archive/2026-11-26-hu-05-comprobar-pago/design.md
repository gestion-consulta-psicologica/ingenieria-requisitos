# Design

## Context

La aplicación ya usa FastAPI, Jinja2, `sqlite3` y migraciones numeradas. No existen tablas de atención ni de pago: la base llega a la migración `006` (`reserva_historial`). HU-05 es de solo lectura y necesita datos de ejemplo, porque la creación automática de la atención y el registro del comprobante corresponden a HU-05A. Ver `proposal.md - Why` y la ficha `.cin324/historias/HU-05.md`.

## Goals / Non-Goals

**Goals:**

- Consultar la atención y su pago en modo de solo lectura.
- Mostrar nombre y RUT del paciente, montos y estado del pago.
- Mostrar los comprobantes de transferencia o informar su ausencia.
- Listar las atenciones con pago pendiente.
- Dejar visible la opción de registrar el estado de pago, sin habilitarla ni calcular el resultado.

**Non-Goals:**

- Registrar el estado de pago o aplicar transiciones de EST-02 (HU-06).
- Crear automáticamente la atención o registrar comprobantes (HU-05A).
- Emitir boletas (HU-07).
- Autenticación real o permisos por rol.
- Cálculo del monto o de la cuenta de destino.

## Decisions

### 1. Tablas derivadas del modelo de dominio

Se agrega la migración `007_atencion_pago.sql`:

| Tabla | Columnas | Origen en el modelo |
|-------|----------|---------------------|
| `atencion` | `id`, `reserva_id` (único, FK), `tipo_atencion`, `monto`, `estado` | `Atencion`; `Reserva 1 – 0..1 Atencion`; estados de EST-01 |
| `pago` | `id`, `atencion_id` (único, FK), `monto_atencion`, `monto_pagado`, `estado` | `Pago`; `Atencion 1 – 1 Pago`; estados de EST-02 |
| `comprobante_transferencia` | `id`, `pago_id` (FK), `monto`, `fecha_transferencia`, `cuenta_destino` | `ComprobanteTransferencia`; `Pago 1 – 0..* ComprobanteTransferencia` |

- `atencion.reserva_id` es único y `NOT NULL`: cada atención proviene de una reserva confirmada.
- La fecha de la atención se obtiene de `reserva -> bloque_horario`; no se agrega una columna `fecha`.
- `pago.monto_pagado` inicia en `0`.
- Los estados se restringen con `CHECK` a los nombres del modelo y de EST-02.
- Alternativa considerada: guardar el paciente directamente en `atencion`. Se descartó porque el modelo obtiene al paciente desde la reserva.

### 2. Consulta de solo lectura

Un servicio `app/servicios/pagos.py` concentra las consultas:

- `listar_atenciones_con_pago_pendiente(conexion)` devuelve las atenciones cuyo pago está en estado `Pendiente`.
- `obtener_pago_de_atencion(conexion, atencion_id)` devuelve la atención, el paciente (nombre y RUT), el pago y la lista de comprobantes.

El servicio no expone funciones de escritura ni de transición de estado. El estado del pago solo se lee; cualquier cambio corresponde a HU-06. Alternativa considerada: reutilizar una función de transición de EST-02. Se descartó para no implementar comportamiento de otra historia.

### 3. Rutas y pantallas derivadas de DSS-05

| Mensaje de DSS-05 | Ruta | Pantalla |
|-------------------|------|----------|
| consultar el pago de una atención | `GET /pagos` | `pagos.html`: listado de atenciones con pago pendiente |
| consultar una atención | `GET /pagos/{atencion_id}` | `pago_detalle.html`: detalle del pago y sus comprobantes |
| atención inexistente | `GET /pagos/{atencion_id}` | responde 404 e informa que no se encontró la atención |
| ofrecer «Registrar estado de pago» | — | enlace o botón visible con `aria-disabled` y sin acción; se habilitará en HU-06 |

- El listado permite elegir una atención; el detalle muestra el nombre y el RUT del paciente, `monto_atencion`, `monto_pagado`, el estado y los comprobantes.
- Si no hay comprobantes, se muestra un aviso y la atención ya aparece en el listado de pago pendiente.
- No se agrega un formulario de escritura.

### 4. Acceso de demostración

No se implementa autenticación. La vista se accede directamente como rol Psicóloga desde `/pagos`; se mantiene la limitación documentada del prototipo. Alternativa considerada: agregar un selector de rol. Se descartó porque el resto de las historias tampoco lo exige para funcionar y la ficha confirmó el acceso directo.

### 5. Datos de ejemplo

El seed se amplía de forma idempotente con:

- Un bloque del jueves 12 de noviembre de 2026 a las 16:00 y su reserva confirmada.
- Una atención con pago pendiente y un comprobante de $30.000 (escenario «La atención tiene un comprobante de pago registrado»).
- Una atención con pago pendiente sin comprobante (escenario «La atención no tiene comprobante de pago»).

Se usan IDs fijos y `INSERT OR IGNORE`, igual que el seed actual.

### 6. Pruebas

Una prueba de integración por escenario de la especificación, con base SQLite temporal:

- `HU-05 · La atención tiene un comprobante de pago registrado`
- `HU-05 · La atención no tiene comprobante de pago`
- `HU-05 · La psicóloga revisa la información y continúa al registro`

### 7. Integraciones externas

Ninguna. HU-05 no participa de correo, SII ni otro sistema externo; no se crea adaptador ni simulación.

## Risks / Trade-offs

- **Datos inexistentes en producción** → la creación de la atención y del comprobante se implementará en HU-05A; mientras tanto, el seed y las pruebas crean los datos.
- **El listado solo muestra atenciones con pago pendiente** → el detalle por ID permite consultar una atención pagada; una vista histórica completa queda para otra historia.
- **Sin autenticación** → limitación del prototipo; el acceso es directo como rol Psicóloga.
- **La opción de registrar estado no funciona todavía** → se muestra inactiva y se documenta que se habilita en HU-06, evitando implementar comportamiento fuera de alcance.

## Migration Plan

1. Aplicar `007_atencion_pago.sql` al arrancar la aplicación; las pruebas usan una base temporal.
2. Ejecutar el seed para cargar los datos de ejemplo.
3. Rollback: al ser tablas nuevas y sin dependencias previas, se pueden eliminar sin afectar reservas, pacientes ni confirmaciones.
