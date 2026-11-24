# Criterios de aceptación (Gherkin)

> **Fuente de verdad:** los criterios de aceptación de cada historia se definen en `04-historias-usuario.md`. Este documento los deriva en escenarios Gherkin y mantiene la correspondencia CA ↔ escenario; ante una diferencia, prevalece `04-historias-usuario.md`.

## HU-01 — Consultar disponibilidad

Historia: Como paciente, quiero consultar la disponibilidad de horas en la plataforma, para conocer las opciones de atención sin depender de una coordinación por WhatsApp.

```gherkin
Característica: Consulta de disponibilidad de horas

  Escenario: El paciente consulta una semana con bloques horarios libres
    Dado que la psicóloga definió su disponibilidad para la semana del 9 de noviembre
    Y que el bloque del martes 10 de noviembre a las 10:00 tiene una reserva vigente
    Y que el bloque del martes 10 de noviembre a las 11:00 está libre
    Cuando el paciente consulta la disponibilidad de esa semana
    Entonces el sistema informa el bloque del martes 10 de noviembre a las 11:00 como disponible
    Y no informa el bloque del martes 10 de noviembre a las 10:00

  Escenario: El paciente consulta una semana sin bloques horarios libres
    Dado que todos los bloques horarios de la semana del 16 de noviembre tienen una reserva vigente
    Cuando el paciente consulta la disponibilidad de esa semana
    Entonces el sistema informa que no hay horas disponibles para esa semana
    Y informa la fecha del próximo bloque horario disponible
```

## HU-02 — Reservar una hora

Historia: Como paciente, quiero seleccionar un horario disponible, para reservar una hora de atención directamente desde la plataforma.

```gherkin
Característica: Reserva de hora de atención

  Escenario: El paciente confirma la reserva de un bloque horario disponible
    Dado que el bloque del jueves 12 de noviembre a las 16:00 está disponible
    Y que el paciente tiene registrados su nombre completo, RUT y un medio de contacto
    Cuando el paciente selecciona ese bloque horario
    Entonces el sistema muestra el horario seleccionado como opción para continuar
    Y todavía no registra la reserva
    Cuando el paciente confirma la reserva
    Entonces el sistema registra la reserva en estado "pendiente de confirmación"
    Y el bloque del jueves 12 de noviembre a las 16:00 deja de estar disponible para otros pacientes
    Y el sistema encola y envía al paciente el aviso de la reserva registrada por correo electrónico

  Escenario: Otro paciente reservó el mismo bloque horario antes
    Dado que el bloque del jueves 12 de noviembre a las 16:00 fue reservado por otro paciente
    Cuando el paciente intenta reservar ese bloque horario
    Entonces el sistema rechaza la reserva indicando que el bloque ya no está disponible
    Y informa los bloques horarios disponibles más cercanos

  Escenario: El paciente no está registrado en el sistema
    Dado que el paciente ingresa un RUT que no está registrado
    Cuando el paciente intenta reservar un bloque horario disponible
    Entonces el sistema no registra la reserva
    Y lo deriva al registro de sus datos personales
    Y al completar el registro retoma la reserva del bloque horario seleccionado
```

## HU-02A — Registrar datos del paciente

Historia: Como paciente, quiero registrar mis datos personales en la plataforma, para poder reservar una hora de atención cuando aún no estoy registrado.

```gherkin
Característica: Registro de datos del paciente

  Escenario: Un paciente nuevo se registra desde la reserva
    Dado que el paciente ingresó un RUT que no está registrado
    Cuando ingresa su nombre completo, su RUT y un medio de contacto
    Y guarda sus datos
    Entonces el sistema registra al paciente
    Y retoma la reserva del bloque horario seleccionado

  Escenario: El paciente no completa los datos obligatorios
    Dado que el paciente está registrando sus datos
    Cuando intenta guardar sin nombre completo, RUT o medio de contacto
    Entonces el sistema no registra al paciente
    Y le informa qué dato falta

  Escenario: El RUT ya está registrado
    Dado que el paciente ingresa un RUT que ya existe en el sistema
    Cuando intenta registrar sus datos
    Entonces el sistema no duplica al paciente
    Y utiliza el registro existente
```

## HU-03 — Confirmar o cancelar una hora

Historia: Como paciente, quiero confirmar o cancelar mi hora desde la plataforma o desde el enlace seguro del correo, para gestionar mi asistencia sin tener que responder mediante WhatsApp.

```gherkin
Característica: Confirmación de asistencia

  Escenario: El paciente confirma su asistencia
    Dado que el paciente tiene una reserva para el jueves 12 de noviembre a las 16:00 en estado "pendiente de confirmación"
    Y que el sistema le envió la solicitud de confirmación por correo electrónico el miércoles 11 de noviembre y está pendiente de respuesta
    Cuando el paciente confirma su asistencia desde la plataforma o desde el enlace del correo
    Entonces la reserva queda en estado "confirmada"
    Y la solicitud pendiente más reciente queda en estado "respondida", con la respuesta "confirma" y su fecha de respuesta
    Y el enlace utilizado queda marcado como usado
    Y la reserva queda con su estado actualizado para la psicóloga

  Escenario: El paciente cancela su hora al responder la confirmación
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Y que el sistema le envió una solicitud de confirmación por correo electrónico y está pendiente de respuesta
    Cuando el paciente responde que no asistirá
    Entonces la reserva queda en estado "cancelada"
    Y la solicitud pendiente más reciente queda en estado "respondida", con la respuesta "no asistirá" y su fecha de respuesta
    Y el sistema registra un cargo de $5.000 asociado al paciente y a la reserva
    Y el bloque horario vuelve a estar disponible para otros pacientes
    Y el aviso del cargo se encola para envío por correo electrónico

  Escenario: El enlace de correo ya fue utilizado
    Dado que el paciente ya respondió usando el enlace del correo
    Cuando vuelve a abrir o enviar el mismo enlace
    Entonces el sistema responde con HTTP 409 e informa que el enlace ya fue utilizado
    Y la respuesta registrada no cambia

  Escenario: El recordatorio reemplaza la solicitud anterior
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Y la solicitud de víspera está pendiente de respuesta
    Cuando el sistema envía el recordatorio de la mañana
    Entonces la solicitud de víspera queda en estado "reemplazada" con su fecha de cierre
    Y el recordatorio queda como la única solicitud pendiente de la reserva

  Escenario: El paciente intenta responder sin una solicitud pendiente
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Y no existe una solicitud pendiente de respuesta
    Cuando el paciente intenta confirmar su asistencia o informar que no asistirá
    Entonces el sistema responde con HTTP 409 y un mensaje claro
    Y la reserva conserva su estado y no se crean ni modifican solicitudes ni cargos

  Escenario: El paciente intenta responder una solicitud que ya tiene respuesta
    Dado que el paciente tiene una reserva en estado "confirmada"
    Y la solicitud de confirmación más reciente ya tiene respuesta "confirma"
    Cuando el paciente intenta confirmar o informar que no asistirá
    Entonces el sistema responde con HTTP 409 y un mensaje claro
    Y la respuesta registrada no cambia

  Escenario: El paciente intenta responder una solicitud reemplazada o vencida
    Dado que el paciente tiene una solicitud de confirmación en estado "reemplazada" o "vencida"
    Cuando el paciente intenta confirmar o informar que no asistirá
    Entonces el sistema responde con HTTP 409 y un mensaje claro
    Y la solicitud conserva su estado y no se registra una nueva respuesta

  Escenario: El paciente no responde la confirmación
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Y que el sistema le envió la solicitud de confirmación por correo electrónico el día anterior y el recordatorio en la mañana de la atención
    Cuando llega la hora de la atención sin respuesta del paciente
    Entonces la reserva queda en estado "sin confirmar"
    Y la solicitud pendiente más reciente queda en estado "vencida", con la respuesta "sin respuesta" y la fecha de cierre de la atención
    Y no se registra una fecha de respuesta del paciente
    Y el sistema registra un cargo de $5.000 por falta de confirmación asociado al paciente y a la reserva
    Y el aviso de cargo se encola para envío por correo electrónico

  Escenario: El servidor SMTP no está disponible
    Dado que existe un correo pendiente en la cola de notificaciones
    Y el servidor SMTP no responde
    Cuando el planificador intenta enviarlo
    Entonces el correo queda en estado "pendiente" con un nuevo intento programado y el error registrado
    Y no se marca como "enviado"

  Escenario: El paciente no tiene correo registrado
    Dado que la reserva se registra para un paciente sin correo electrónico
    Cuando el sistema intenta encolar el aviso de reserva
    Entonces el correo queda en estado "omitido" con el motivo
    Y no se registra un envío exitoso
```

## HU-04 — Reagendar o cancelar una hora

Historia: Como paciente, quiero solicitar el reagendamiento o cancelación de una hora desde la plataforma, para modificar mi reserva sin depender del contacto con la secretaria o psicóloga.

**Trazabilidad:** los escenarios de esta sección derivan de los CA1–CA8 de HU-04 en `04-historias-usuario.md`; cada escenario indica el criterio que desarrolla. Se incorpora un escenario complementario para verificar que las cancelaciones realizadas por la psicóloga no generan cargos.

```gherkin
Característica: Reagendamiento y cancelación de una reserva

  # CA1
  Escenario: El paciente accede a las opciones de gestión
    Dado que el paciente tiene una reserva en estado "Confirmada"
    Cuando accede al detalle de su reserva
    Entonces el sistema le permite elegir entre reagendar o cancelar la hora

  # CA2
  Escenario: El paciente cancela una reserva
    Dado que el paciente tiene una reserva en estado "Confirmada" para el viernes 13 de noviembre a las 18:00
    Cuando el paciente confirma la cancelación de la reserva
    Entonces la reserva queda en estado "Cancelada"
    Y el sistema registra un cargo de $5.000 asociado al paciente y a la reserva
    Y el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible
    Y el historial de la reserva conserva el cambio de cancelación
    Y el aviso del cargo se encola para envío por correo electrónico

  Escenario complementario: La psicóloga cancela una reserva
    Dado que existe una reserva en estado "Confirmada"
    Cuando la psicóloga cancela la reserva desde la plataforma
    Entonces la reserva queda en estado "Cancelada"
    Y el bloque horario vuelve a estar disponible
    Y el historial de la reserva conserva el cambio de cancelación
    Y el sistema no genera un cargo de $5.000 al paciente

  # CA3
  Escenario: El paciente solicita reagendar y existen alternativas
    Dado que el paciente tiene una reserva en estado "Confirmada" para el viernes 13 de noviembre a las 18:00
    Y que existen bloques horarios disponibles en los próximos 14 días
    Cuando el paciente solicita reagendar la reserva
    Entonces el sistema consulta la disponibilidad de los próximos 14 días
    Y excluye el bloque actual y los bloques ocupados
    Y la reserva original se mantiene vigente mientras el paciente no elija una alternativa

  # CA4
  Escenario: El sistema muestra las alternativas disponibles
    Dado que el sistema encontró bloques disponibles para el reagendamiento
    Cuando presenta los resultados de la consulta
    Entonces el paciente puede visualizar las alternativas disponibles para seleccionar un nuevo horario

  # CA5
  Escenario: El paciente elige una alternativa disponible
    Dado que el sistema muestra alternativas disponibles
    Cuando el paciente elige el bloque del lunes 16 de noviembre a las 17:00
    Entonces el sistema identifica el bloque seleccionado
    Y lo presenta como opción para confirmar el reagendamiento

  # CA6
  Escenario: El paciente confirma el nuevo horario
    Dado que el paciente eligió el bloque del lunes 16 de noviembre a las 17:00
    Y que el bloque continúa disponible
    Cuando el paciente confirma el reagendamiento
    Entonces la reserva queda asociada al lunes 16 de noviembre a las 17:00 en estado "Pendiente de confirmación"
    Y el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible
    Y el historial de la reserva conserva el cambio de reagendamiento
    Y el sistema encola y envía al paciente el aviso de la reserva reagendada por correo electrónico para iniciar un nuevo ciclo
    Y el sistema no genera un cargo de $5.000 por el reagendamiento

  # CA7
  Escenario: La alternativa elegida fue tomada por otro paciente
    Dado que el paciente eligió el bloque del lunes 16 de noviembre a las 17:00
    Y que ese bloque fue reservado por otro paciente antes de confirmar
    Cuando el paciente intenta confirmar el cambio
    Entonces el sistema responde con conflicto (409) e indica que el bloque ya no está disponible
    Y la reserva original se mantiene sin cambios

  # CA8
  Escenario: El paciente solicita reagendar y no existen alternativas
    Dado que el paciente tiene una reserva en estado "Confirmada"
    Y que no existen bloques horarios disponibles en los próximos 14 días
    Cuando el paciente solicita reagendar la reserva
    Entonces el sistema informa que no hay alternativas disponibles
    Y la reserva original se mantiene vigente
```

## HU-05 — Comprobar el pago

Historia: Como psicóloga, quiero consultar la información del pago asociada a una atención, para comprobar el pago sin depender únicamente de comprobantes enviados por WhatsApp.

```gherkin
Característica: Comprobación del pago de una atención

  Escenario: La atención tiene un comprobante de pago registrado
    Dado que el paciente registró un comprobante de transferencia por $30.000 para su atención del jueves 12 de noviembre
    Cuando la psicóloga consulta el pago de esa atención
    Entonces el sistema informa el monto, la fecha de la transferencia y la cuenta de destino del comprobante
    Y el monto informado es el registrado para la atención, sin tarifas por tipo de atención

  Escenario: La atención tiene un pago pendiente sin comprobante
    Dado que la atención tiene un pago en estado "Pendiente" y el paciente no ha registrado un comprobante de pago
    Cuando la psicóloga consulta el pago de esa atención
    Entonces el sistema informa que la atención no tiene comprobante de pago
    Y la atención aparece en el listado de atenciones con pago pendiente
```

## HU-05A — Registrar la atención y el comprobante de pago

Historia: Como paciente, quiero contar con la atención registrada y registrar el comprobante de mi transferencia en la plataforma, para que la psicóloga pueda comprobar el pago de mi atención.

**Trazabilidad:** los escenarios de esta sección derivan de los CA1–CA6 de HU-05A en `04-historias-usuario.md`. CA1 y CA6 → escenario de la reserva que llega a la hora; CA2 y CA5 → escenario del registro del comprobante; CA3 → escenario de datos obligatorios; CA4 → escenario del segundo comprobante. Los demás escenarios cubren validaciones y rechazos.

```gherkin
Característica: Registro de la atención y del comprobante de pago

  Escenario: La reserva confirmada llega a la hora de la atención
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando llega la hora de la atención
    Entonces el sistema origina una atención en estado "programada"
    Y registra un pago en estado "Pendiente" con el monto registrado para la atención
    Y la reserva queda en estado "Finalizada"

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

  Escenario: El comprobante tiene datos inválidos
    Dado que el paciente está registrando un comprobante
    Cuando ingresa un monto no positivo o una fecha de transferencia inválida
    Entonces el sistema no registra el comprobante
    Y le informa el error

  Escenario: La atención tiene un pago pendiente sin comprobante
    Dado que la atención tiene un pago en estado "Pendiente" y no tiene comprobantes registrados
    Cuando el paciente registra un comprobante
    Entonces el sistema asocia el comprobante al pago
    Y el pago sigue en estado "Pendiente"

  Escenario: El pago ya está pagado
    Dado que el pago de la atención está en estado "Pagado"
    Cuando el paciente intenta registrar un comprobante
    Entonces el sistema no habilita el registro
    Y le informa que el pago ya está pagado

  Escenario: El sistema no duplica una atención ya originada
    Dado que la reserva confirmada ya tiene una atención originada
    Cuando el sistema vuelve a procesar la reserva
    Entonces no crea una nueva atención ni un nuevo pago
    Y la reserva permanece en estado "Finalizada"
```

## HU-06 — Registrar el estado de pago

Historia: Como psicóloga, quiero registrar el estado de pago de una atención en la plataforma, para mantener actualizada la información administrativa del paciente.

```gherkin
Característica: Registro del estado de pago

  Escenario: La psicóloga registra un pago verificado
    Dado que la atención del jueves 12 de noviembre tiene un comprobante por $30.000
    Y que el monto del comprobante coincide con el monto de la atención
    Cuando la psicóloga registra el pago como verificado
    Entonces el pago queda en estado "pagado" asociado al paciente y a la atención
    Y la atención deja de aparecer en el listado de atenciones con pago pendiente

  Escenario: El monto del comprobante no coincide con el de la atención
    Dado que la atención del jueves 12 de noviembre tiene un monto de $30.000
    Y que el comprobante registrado es por $20.000
    Cuando la psicóloga revisa el pago
    Entonces el pago queda en estado "pago incompleto"
    Y el sistema informa una diferencia pendiente de $10.000
```

## HU-07 — Emitir boleta

Historia: Como psicóloga, quiero emitir la boleta con apoyo de la plataforma, para reducir el tiempo destinado a tareas administrativas.

```gherkin
Característica: Emisión de boleta de honorarios

  Escenario: La psicóloga emite la boleta de una atención pagada
    Dado que la atención del jueves 12 de noviembre tiene su pago en estado "pagado" por $30.000
    Y que el paciente tiene registrados su nombre completo y RUT
    Cuando la psicóloga solicita emitir la boleta de esa atención
    Entonces el sistema prepara la boleta con el nombre y RUT del paciente, la fecha de la atención y el monto de $30.000
    Y el SII registra la boleta de honorarios electrónica
    Y la boleta queda asociada a la atención con su número de folio

  Escenario: La atención no tiene el pago verificado
    Dado que la atención del jueves 12 de noviembre tiene su pago en estado "Pendiente"
    Cuando la psicóloga solicita emitir la boleta de esa atención
    Entonces el sistema no prepara la boleta
    Y informa que la atención no tiene el pago verificado

  Escenario: El SII no está disponible
    Dado que la atención del jueves 12 de noviembre tiene su pago en estado "pagado"
    Y que el SII no responde a la solicitud de emisión
    Cuando la psicóloga solicita emitir la boleta de esa atención
    Entonces la boleta queda en estado "pendiente de emisión"
    Y la atención aparece en el listado de boletas pendientes
```

## HU-08 — Registrar asistencia e inasistencia

Historia: Como psicóloga, quiero registrar la asistencia o inasistencia del paciente en la plataforma, para mantener actualizado el estado de cada atención.

**Trazabilidad:** los escenarios de inasistencia derivan de los CA4 y CA5 de HU-08 en `04-historias-usuario.md`.

```gherkin
Característica: Registro de asistencia a la atención

  Escenario: El paciente asiste a la atención
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando la psicóloga registra que el paciente asistió
    Entonces la atención queda en estado "realizada"
    Y la asistencia queda en el historial de atenciones del paciente

  Escenario: El paciente no asiste sin justificación
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando la psicóloga registra que el paciente no asistió y no justificó la inasistencia
    Entonces la atención queda en estado "inasistencia"
    Y el sistema registra un cargo de $5.000 por inasistencia sin justificación, asociado a la atención y al paciente, sin modificar el estado del pago

  Escenario: El paciente justifica la inasistencia
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando la psicóloga registra que el paciente no asistió y justificó la inasistencia
    Entonces la atención queda en estado "inasistencia justificada"
    Y el sistema no registra el cargo de $5.000 por inasistencia
```

## HU-09 — Actualizar ficha clínica

Historia: Como psicóloga, quiero actualizar la ficha clínica del paciente en una plataforma centralizada, para mantener la información clínica organizada y disponible para el seguimiento de sus atenciones.

```gherkin
Característica: Actualización de la ficha clínica

  Escenario: La psicóloga registra la evolución de una atención realizada
    Dado que la atención del jueves 12 de noviembre está en estado "realizada"
    Y que la psicóloga inició sesión con su cuenta
    Cuando la psicóloga registra la evolución de esa atención en la ficha clínica del paciente
    Entonces la ficha clínica conserva el registro con la fecha de la atención
    Y los registros anteriores de la ficha clínica se mantienen sin cambios

  Escenario: La secretaria intenta acceder a una ficha clínica
    Dado que la secretaria inició sesión con su cuenta
    Cuando la secretaria intenta consultar la ficha clínica de un paciente
    Entonces el sistema niega el acceso a la ficha clínica
    Y registra el intento de acceso en la bitácora de accesos
```

## HU-10 - Derivación a psiquiatra

Historia: Como psicologa, quiero poder derivar a un paciente a un psiquiatra registrado en el sistema si es que el paciente necesita una atencion mas especializada.

```gherkin
Característica:

  Escenario: La psicóloga deriva al paciente a psiquiatra
  Dado que la psicóloga lo deriva
  Y que el paciente confirmo la hora
  Cuando el paciente vea la confirmación saldrá "asignado a psiquiatra"
  Entonces el sistema pone al paciente a cargo del psiquiatra.
```
