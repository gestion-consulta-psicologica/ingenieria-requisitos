# Design

## Context

La aplicación ya tiene las tablas `atencion`, `pago` y `comprobante_transferencia` de la migración `007`, creadas por HU-05. También tiene un `PlanificadorCorreos` que se ejecuta al iniciar y periódicamente, y rutas de consulta de pagos en `app/rutas/pagos.py`. HU-05 solo lee esos datos; esta historia agrega su origen y el registro del comprobante. Ver `proposal.md - Why` y la ficha `.cin324/historias/HU-05A.md`.

## Goals / Non-Goals

**Goals:**

- Originar automáticamente `Atencion` y `Pago` desde reservas confirmadas vencidas, sin duplicados.
- Registrar uno o más `ComprobanteTransferencia` desde el detalle de la reserva.
- Validar los datos del comprobante y mantener el estado del pago sin cambios.
- Reutilizar las tablas y el planificador existentes.

**Non-Goals:**

- Comprobar el pago o mostrar el detalle a la psicóloga (HU-05).
- Registrar el estado del pago o aplicar transiciones de EST-02 (HU-06).
- Emitir boletas (HU-07) o registrar asistencia y estados de `Atencion` (HU-08).
- Autenticación real, cálculo de tarifas, integración bancaria o notificaciones.
- Crear nuevas tablas o modificar la migración `007`.

## Decisions

### 1. Origen automático desde el planificador existente

Se agrega un servicio `app/servicios/atenciones.py` con `crear_atenciones_vencidas(conexion, ahora, zona_horaria)`.

- Consulta las `Reserva` en estado `Confirmada` que no tengan una `Atencion` y cuyo `BloqueHorario` ya haya comenzado.
- Por cada una inserta una `Atencion` (`tipo_atencion` = modalidad del bloque, `monto` = monto configurable, `estado = programada`), un `Pago` (`monto_atencion` = mismo monto, `monto_pagado = 0`, `estado = Pendiente`) y actualiza la `Reserva` a `Finalizada`, todo en una misma transacción.
- La idempotencia se apoya en `atencion.reserva_id UNIQUE`: si otra ejecución ya creó la atención, la inserción falla y se ignora sin duplicar.
- El planificador llama al servicio en cada ciclo, después de procesar las reservas pendientes de confirmación. Así se cumple el inicio y la ejecución periódica sin agregar otro proceso.
- Alternativa considerada: crear la atención desde la ruta de confirmación. Se descartó porque la atención se origina cuando llega la hora, no cuando el paciente confirma.

### 2. Monto configurable

El monto se lee de la variable de entorno `MONTO_ATENCION_CLP`, con **$30.000** como valor por defecto. Se agrega una función en `app/configuracion.py` para centralizar la lectura. No se crea una tabla de tarifas: el estudiante confirmó que $30.000 es un ejemplo que se cambiará en el futuro.

### 3. Servicio de registro y validaciones

`app/servicios/atenciones.py` expone `registrar_comprobante(conexion, atencion_id, monto, fecha_transferencia, cuenta_destino)`.

- Busca la `Atencion` y su `Pago`. Si no existe la atención o no hay pago, lanza un error de negocio.
- Rechaza el registro si el pago está en estado `Pagado`.
- Valida monto entero positivo, fecha ISO válida y cuenta de destino no vacía; devuelve mensajes claros por campo.
- Inserta un nuevo `ComprobanteTransferencia` asociado al `Pago`. No actualiza `pago.estado` ni `pago.monto_pagado`.
- Alternativa considerada: actualizar `monto_pagado` al registrar. Se descartó porque el cálculo y las transiciones de EST-02 pertenecen a HU-06.

### 4. Rutas y pantallas

Se agregan en `app/rutas/pagos.py`:

| Mensaje / caso | Ruta | Comportamiento |
|----------------|------|----------------|
| Mostrar el formulario | `GET /pagos/{atencion_id}/comprobante` | Si la atención y el pago existen y el pago está `Pendiente` o `Pago incompleto`, muestra el formulario. Si no, informa con 404 o 409. |
| Registrar el comprobante | `POST /pagos/{atencion_id}/comprobante` | Valida y guarda; en éxito redirige con 303 al mismo formulario con confirmación. Errores de datos: 400; atención/pago inexistente: 404; pago `Pagado`: 409. |

- Se crea `app/templates/pago_comprobante.html` con los datos de la atención, el formulario (`monto`, `fecha_transferencia`, `cuenta_destino`), los comprobantes ya registrados y los mensajes de éxito o error.
- El detalle de la reserva (`GET /reservas/{id}`) muestra el enlace **«Registrar comprobante de pago»** solo cuando existe una atención con pago en estado `Pendiente` o `Pago incompleto`.
- `app/templates/reserva_confirmada.html` recibe desde la ruta el identificador de la atención y el estado del pago; no calcula reglas de negocio en la plantilla.
- Alternativa considerada: usar `/atenciones/{id}/comprobante`. Se descartó para mantener la ruta junto a las demás rutas de pago y porque el comprobante se asocia al pago.

### 5. Acceso de demostración

No se implementa autenticación. El paciente accede desde el detalle de su reserva, como en el resto del prototipo, y el formulario indica que es un acceso de demostración. La ruta directa por `atencion_id` también queda disponible para pruebas manuales.

### 6. Integraciones externas

Ninguna. No hay banco, pasarela de pago ni correo en esta historia; no se crea adaptador ni simulación.

### 7. Datos de ejemplo y pruebas

- Se reutiliza la reserva `2` del seed (`2026-11-17 10:00`, `Confirmada`, sin atención) como caso vencido para la creación automática. Los datos de HU-05 se mantienen.
- Se agregan pruebas en `tests/test_hu05a_atencion_comprobante.py`:
  - creación automática e idempotencia sobre una reserva confirmada vencida;
  - registro de un comprobante y conservación de uno anterior;
  - datos obligatorios y datos inválidos;
  - pago inexistente por datos inconsistentes y pago `Pagado`;
  - enlace visible en el detalle de la reserva y formulario disponible.
- Las pruebas de rutas usan `crear_app(..., planificador_activo=False)` para que la creación automática no altere los datos de ejemplo durante la prueba; la creación automática se prueba llamando al servicio con un `ahora` controlado.

## Risks / Trade-offs

- **El planificador está desactivado en pruebas o en un entorno con `PLANIFICADOR_ACTIVO=0`** → no se crean atenciones automáticamente; se documenta que el proceso depende del planificador activo.
- **El seed tiene atenciones creadas manualmente para HU-05** → la creación automática las detecta y no las duplica; la reserva `2` sirve como caso nuevo.
- **El monto cambia en el futuro** → se lee de `MONTO_ATENCION_CLP`; las atenciones ya creadas conservan su monto.
- **Sin autenticación** → limitación del prototipo; el acceso es por el detalle de la reserva y por ID de atención.
- **Pago `Pago incompleto`** → el formulario sigue disponible para nuevos comprobantes; el estado solo cambia en HU-06.

## Migration Plan

1. No se requiere una migración nueva: se reutilizan las tablas de `007_atencion_pago.sql`.
2. Al arrancar con el planificador activo, el primer ciclo crea las atenciones de reservas confirmadas vencidas.
3. Rollback: detener el planificador y eliminar las atenciones y pagos creados por esta historia si fuera necesario; las tablas son las mismas de HU-05.
