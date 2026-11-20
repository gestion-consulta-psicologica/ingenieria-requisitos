# HU-05A — Registrar la atención y el comprobante de pago

**Estado:** lista para especificar  ·  **Confirmada por el estudiante:** 2026-11-19
**Fuente de la historia:** `04-historias-usuario.md` · **Gherkin:** `07-criterios-aceptacion.md`

## Historia
Como paciente, quiero contar con la atención registrada y registrar el comprobante de mi transferencia en la plataforma, para que la psicóloga pueda comprobar el pago de mi atención.

## Trazabilidad
- Actividad del TO-BE: **Realizar pago** (tipo: tarea de usuario). Cambio respecto del AS-IS: el comprobante de la transferencia deja de enviarse por WhatsApp y se registra en la plataforma, asociado al pago de la atención. Se agregó la fila correspondiente a la tabla «Actividades que cambian» de `02-rediseno-to-be.md` el 2026-11-19.
- Actividad de apoyo: **Comprobar pago con apoyo del sistema**, porque el comprobante registrado queda disponible para que la psicóloga lo consulte en HU-05. La comprobación y el cambio de estado del pago no se implementan en esta historia.
- Caso de uso: **CU-12 — Registrar comprobante de pago**. Actor principal: **Paciente**. Actores externos: **ninguno**.
- Relaciones: sin `include`/`extend`. La creación automática de la atención y su pago es un paso del sistema, no un objetivo del paciente. Continúa en **CU-06 — Comprobar pago** (HU-05), que solo lee, y en **CU-07 — Registrar estado de pago** (HU-06), que produce las transiciones de EST-02.
- Requisitos que cubre: **RP-23**. Contexto no funcional: **RP-17** (confidencialidad), **RP-18** y **RP-20** (transversales).
- Creación automática de la atención y del pago: se respalda en la transición de **EST-01** «Confirmada + llega la hora de la atención → (final), originar atención» y en la transición inicial de **EST-02** «(inicial) + se origina la atención → Pendiente». No se creó un requisito funcional nuevo: RP-23 cubre el registro del comprobante y la creación automática se documenta como regla de estado.
- Diagrama de secuencia: **no existe DSS-12**; el flujo se reconstruyó desde el Gherkin y CU-12 y se confirmó el 2026-11-19.
- Diagrama de estado: **EST-01 — Reserva** (transición a «(final)» conceptual) y **EST-02 — Pago** (creación en estado `Pendiente`). La clase `Atencion` tiene estados en el modelo de dominio, pero no tiene un `EST-xx`; en esta historia solo se crea en estado `programada` y no se producen sus transiciones.

## Entidades del modelo de dominio
| Entidad | Operación en esta historia | Atributos usados | Asociaciones y multiplicidades |
|---------|----------------------------|------------------|--------------------------------|
| **Reserva** | Lee; no cambia su estado en la base | `estado` (`Confirmada`), `fechaRegistro` | Paciente `1 – 0..*` Reserva; Reserva `0..* – 1` BloqueHorario; Reserva `1 – 0..1` Atencion |
| **BloqueHorario** | Lee la fecha, la hora y la modalidad de la atención | `fecha`, `horaInicio`, `horaTermino`, `modalidad` | Psicologa `1 – 0..*` BloqueHorario; Reserva `0..* – 1` BloqueHorario |
| **Paciente** | Lee para identificar al paciente de la atención | `nombreCompleto`, `rut` | Paciente `1 – 0..*` Reserva |
| **Atencion** | Crea | `tipoAtencion` (desde la modalidad del bloque), `monto`, `estado = programada`; la fecha se deriva del BloqueHorario | Reserva `1 – 0..1` Atencion; Atencion `1 – 1` Pago |
| **Pago** | Crea | `montoAtencion` = monto de la atención, `montoPagado = 0`, `estado = Pendiente` | Atencion `1 – 1` Pago; Pago `1 – 0..*` ComprobanteTransferencia |
| **ComprobanteTransferencia** | Crea uno o más | `monto`, `fechaTransferencia`, `cuentaDestino` | Pago `1 – 0..*` ComprobanteTransferencia |

El monto de la atención se toma de un valor configurable. **$30.000 es un valor de ejemplo**; el estudiante indicó que se cambiará en el futuro, por lo que no se modela una tarifa por tipo de atención en esta historia ni se fija como regla permanente.

## Cambios de estado
| Entidad | Estado origen | Evento | Guarda | Acción | Estado destino |
|---------|---------------|--------|--------|--------|----------------|
| **Reserva** | Confirmada | llega la hora de la atención | no existe una Atencion para la reserva | originar la atención y su pago | (final) conceptual; en la base la Reserva permanece `Confirmada` |
| **Atencion** | (inicial) | se origina la atención | existe una Reserva confirmada sin atención | registrar `tipoAtencion`, `monto` y `estado = programada` | programada |
| **Pago** | (inicial) | se origina la atención | la Atencion se creó correctamente | registrar `montoAtencion = monto de la atención`, `montoPagado = 0` y `estado = Pendiente` | Pendiente |

**Sin transiciones adicionales:** el registro de uno o más comprobantes no cambia el estado de `Pago`. Las transiciones `Pendiente → Pagado` y `Pendiente → Pago incompleto` pertenecen a HU-06. `Atencion` no tiene `EST-xx`; sus transiciones a `realizada`, `inasistencia` o `inasistencia justificada` pertenecen a HU-08. El nombre canónico del estado inicial del pago es **`Pendiente`** (con mayúscula), como en EST-02, en el modelo de dominio y en el Gherkin de `07-criterios-aceptacion.md`.

## Flujo de interacción
1. El sistema procesa automáticamente las reservas en estado **Confirmada** cuya fecha y hora de atención ya llegaron y que todavía no tienen una `Atencion`.
2. Por cada reserva que cumple la condición, el sistema crea en una misma operación una `Atencion` en estado `programada` y un `Pago` en estado `Pendiente`. El tipo de atención se toma de la modalidad del bloque, y el monto de la atención se toma del valor configurable.
3. El procesamiento es idempotente: si la reserva ya tiene una `Atencion`, no se crea otra. Las reservas `Pendiente de confirmación`, `Sin confirmar` o `Cancelada` no originan atención.
4. El paciente accede al detalle de su reserva (`/reservas/{id}`). Si la reserva ya tiene una atención con pago en estado `Pendiente` o `Pago incompleto`, el sistema muestra el enlace **«Registrar comprobante de pago»**.
5. El sistema muestra el formulario con los datos de la atención (fecha, hora, tipo y monto) y los campos **monto**, **fecha de transferencia** y **cuenta de destino**.
6. El paciente completa y guarda el formulario. Si los datos son válidos, el sistema registra el `ComprobanteTransferencia` asociado al `Pago`, conserva los comprobantes anteriores y muestra una confirmación.
7. Si falta el monto, la fecha de transferencia o la cuenta de destino, el sistema no registra el comprobante y le informa al paciente qué dato falta.
8. Si el monto no es un valor positivo o la fecha de transferencia no es válida, el sistema tampoco registra el comprobante y lo informa.
9. Si la atención no existe, no tiene pago asociado o el pago ya está en estado `Pagado`, el sistema no muestra el formulario o rechaza el registro y lo informa, sin modificar datos.
10. En todos los casos, el estado del `Pago` se mantiene sin cambios; el comprobante queda disponible para que la psicóloga lo consulte en HU-05.

**Variantes:**
- **Sin datos obligatorios:** no se registra el comprobante y se informa qué falta.
- **Monto no positivo o fecha inválida:** no se registra el comprobante y se informa el error.
- **Segundo comprobante:** se conserva el anterior y el nuevo se asocia al mismo `Pago`.
- **Atención inexistente o sin pago:** se informa el error sin modificar datos.
- **Pago ya `Pagado`:** no se habilita el registro de un nuevo comprobante.
- **Reserva ya procesada:** no se duplica la atención ni el pago.
- **Reserva no confirmada o cancelada:** no se origina atención.

## Sistemas externos (se simulan en la implementación)
| Sistema | Mensajes | Comportamiento simulado |
|---------|----------|--------------------------|
| Ninguno | — | HU-05A no envía ni recibe mensajes de sistemas externos. |

## Escenarios Gherkin (texto íntegro)
```gherkin
Característica: Registro de la atención y del comprobante de pago

  Escenario: La reserva confirmada llega a la hora de la atención
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando llega la hora de la atención
    Entonces el sistema origina una atención en estado "programada"
    Y registra un pago en estado "Pendiente" con el monto registrado para la atención

  Escenario: El paciente registra el comprobante de su transferencia
    Dado que el paciente tiene una atención registrada con pago pendiente
    Cuando registra un comprobante por $30.000 con fecha de transferencia y cuenta de destino
    Entonces el sistema asocia el comprobante al pago de esa atención
    Y el comprobante queda disponible para que la psicóloga lo consulte

  Escenario: El paciente no completa los datos obligatorios del comprobante
    Dado que el paciente está registrando un comprobante
    Cuando intenta guardar sin monto, fecha de transferencia o cuenta de destino
    Entonces el sistema no registra el comprobante
    Y le informa qué dato falta

  Escenario: El paciente registra un segundo comprobante
    Dado que la atención ya tiene un comprobante registrado
    Cuando el paciente registra otro comprobante para la misma atención
    Entonces el sistema conserva el comprobante anterior
    Y asocia el nuevo comprobante al mismo pago
```

Los escenarios anteriores se normalizan con el estado canónico **`Pendiente`**. El segundo escenario conserva el monto de ejemplo **$30.000**.

### Escenarios adicionales acordados en la validación
Estos escenarios completan las variantes del flujo confirmado y ya están incorporados en `07-criterios-aceptacion.md`:

```gherkin
  Escenario: El comprobante tiene datos inválidos
    Dado que el paciente está registrando un comprobante
    Cuando ingresa un monto no positivo o una fecha de transferencia inválida
    Entonces el sistema no registra el comprobante
    Y le informa el error

  Escenario: La atención no tiene pago asociado
    Dado que la atención no tiene un pago asociado
    Cuando el paciente intenta registrar un comprobante
    Entonces el sistema no registra el comprobante
    Y le informa que no encontró el pago de la atención

  Escenario: El pago ya está pagado
    Dado que el pago de la atención está en estado "Pagado"
    Cuando el paciente intenta registrar un comprobante
    Entonces el sistema no habilita el registro
    Y le informa que el pago ya está pagado

  Escenario: El sistema no duplica una atención ya originada
    Dado que la reserva confirmada ya tiene una atención originada
    Cuando el sistema vuelve a procesar la reserva
    Entonces no crea una nueva atención ni un nuevo pago
```

## Decisiones tomadas en la validación
- **I1 — Alcance:** HU-05A cubre la creación automática de `Atencion` y `Pago` y el registro del `ComprobanteTransferencia` por el paciente. Quedan fuera la comprobación del pago (HU-05), las transiciones de EST-02 (HU-06), la boleta (HU-07) y las transiciones de `Atencion` (HU-08). Confirmado el 2026-11-19.
- **I2 — Actividad del TO-BE:** se agregó la fila **«Realizar pago»** a la tabla «Actividades que cambian» de `02-rediseno-to-be.md`, con el cambio de WhatsApp a la plataforma. El nombre de la actividad se mantiene igual al del BPMN. Confirmado el 2026-11-19.
- **I3 — Caso de uso:** se mantiene **CU-12 — Registrar comprobante de pago**, actor Paciente, sin actores externos ni `include`/`extend`. La creación automática de la atención es un paso del sistema y no cambia el nombre del caso de uso. Confirmado el 2026-11-19.
- **I4 — Monto:** **$30.000 es un ejemplo configurable** que se cambiará en el futuro; no se modela una tarifa por tipo de atención en esta historia. La atención y el pago registran el monto usado al momento de la creación. Confirmado el 2026-11-19.
- **I5 — Estados:** se usa **`Pendiente`** como nombre canónico del estado inicial del pago; `programada` es el estado inicial de `Atencion` según el modelo de dominio. No se crea un `EST-04` para `Atencion` en esta historia. La Reserva no cambia de estado en la base: el estado `(final)` de EST-01 es conceptual y la atención existente marca el fin del ciclo. Confirmado el 2026-11-19.
- **I6 — Disparo automático:** el sistema procesa las reservas vencidas de forma automática al iniciar y periódicamente, de manera idempotente, sin una acción manual del paciente o de la psicóloga. Confirmado el 2026-11-19.
- **I7 — Acceso y disponibilidad del formulario:** el paciente accede desde el detalle de su reserva (`/reservas/{id}`); el enlace «Registrar comprobante de pago» se muestra solo si el pago está en `Pendiente` o `Pago incompleto`. Si el pago está `Pagado`, no se habilita. Confirmado el 2026-11-19.
- **I8 — Flujo sin DSS:** al no existir DSS-12, el flujo se reconstruyó desde el Gherkin y CU-12, incluyendo las variantes de error, y el estudiante lo confirmó. Confirmado el 2026-11-19.
- **I9 — Nombres del Gherkin:** se normalizó `"pendiente"` a **`"Pendiente"`** en esta ficha y en `07-criterios-aceptacion.md` para alinearlo con EST-02 y el modelo de dominio. Confirmado el 2026-11-19.
- **I10 — Escenarios adicionales:** se incorporaron a `07-criterios-aceptacion.md` los escenarios para datos inválidos, atención sin pago, pago ya pagado y no duplicación de la atención. Confirmado el 2026-11-19.

## Supuestos
- El monto de la atención es un valor configurable; **$30.000** se usa como ejemplo inicial y se cambiará en el futuro. No se calcula a partir de una tabla de tarifas en esta historia.
- La fecha de la atención se deriva del `BloqueHorario` de la reserva; no se agrega un atributo `fecha` a `Atencion`.
- `cuentaDestino` es un dato de texto libre; la historia solo exige que no esté vacío. No se valida contra un catálogo de cuentas ni se integra con un banco.
- La fecha de transferencia debe ser una fecha válida; la historia no define una restricción adicional sobre fechas futuras.
- La creación automática se ejecuta al iniciar la aplicación y en cada ciclo periódico del planificador. El intervalo exacto no está definido en los requisitos.
- El procesamiento es idempotente mediante la relación `Reserva 1 – 0..1 Atencion`; no se agrega un atributo `procesada` a `Reserva`.
- No hay autenticación real; el acceso del paciente se hace desde el detalle de la reserva como en el resto del prototipo (limitación coherente con RD-01). Confirmado el 2026-11-19.
- La base de datos existente de HU-05 (`atencion`, `pago`, `comprobante_transferencia`) se reutiliza; HU-05A no requiere nuevas tablas de negocio.
- No se envían correos ni notificaciones por el registro del comprobante; no están en la historia.

## Fuera de alcance de esta historia
- Comprobar el pago y mostrar los antecedentes a la psicóloga (HU-05 / CU-06).
- Registrar el estado de pago y producir las transiciones de EST-02 (HU-06 / CU-07).
- Emitir la boleta (HU-07 / CU-08, EST-03).
- Registrar la asistencia y producir las transiciones de `Atencion` (HU-08 / CU-09).
- Autenticación y autorización reales por rol.
- Cálculo del monto de la atención, tarifas por tipo de atención o integración bancaria.
- Crear un DSS-12 o un EST-04; no se consideran necesarios para esta historia.
- Notificaciones por correo electrónico u otros canales.
- Requisitos no funcionales RP-17, RP-18 y RP-20, que son contexto.
