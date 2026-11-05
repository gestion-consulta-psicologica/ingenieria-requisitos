# Criterios de aceptación (Gherkin)

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

  Escenario: El paciente reserva un bloque horario disponible
    Dado que el bloque del jueves 12 de noviembre a las 16:00 está disponible
    Y que el paciente tiene registrados su nombre completo, RUT y un medio de contacto
    Cuando el paciente reserva ese bloque horario
    Entonces el sistema registra la reserva en estado "pendiente de confirmación"
    Y el bloque del jueves 12 de noviembre a las 16:00 deja de estar disponible para otros pacientes
    Y el servicio de mensajería envía al paciente el aviso de la reserva registrada

  Escenario: Otro paciente reservó el mismo bloque horario antes
    Dado que el bloque del jueves 12 de noviembre a las 16:00 fue reservado por otro paciente
    Cuando el paciente intenta reservar ese bloque horario
    Entonces el sistema rechaza la reserva indicando que el bloque ya no está disponible
    Y informa los bloques horarios disponibles más cercanos

  Escenario: El paciente no tiene registrados sus datos de identificación
    Dado que el paciente no tiene registrado su RUT
    Cuando el paciente intenta reservar un bloque horario disponible
    Entonces el sistema no registra la reserva
    Y solicita completar los datos de identificación del paciente
```

## HU-03 — Confirmar o cancelar una hora
Historia: Como paciente, quiero confirmar o cancelar mi hora desde la plataforma, para gestionar mi asistencia sin tener que responder mediante WhatsApp.

```gherkin
Característica: Confirmación de asistencia

  Escenario: El paciente confirma su asistencia
    Dado que el paciente tiene una reserva para el jueves 12 de noviembre a las 16:00 en estado "pendiente de confirmación"
    Y que el servicio de mensajería le envió la solicitud de confirmación el miércoles 11 de noviembre
    Cuando el paciente confirma su asistencia
    Entonces la reserva queda en estado "confirmada"
    Y la psicóloga ve la reserva como confirmada en su agenda

  Escenario: El paciente cancela su hora al responder la confirmación
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Cuando el paciente responde que no asistirá
    Entonces la reserva queda en estado "cancelada"
    Y el bloque horario vuelve a estar disponible para otros pacientes

  Escenario: El paciente no responde la confirmación
    Dado que el paciente tiene una reserva en estado "pendiente de confirmación"
    Y que el servicio de mensajería le envió la solicitud de confirmación el día anterior y el recordatorio en la mañana de la atención
    Cuando llega la hora de la atención sin respuesta del paciente
    Entonces la reserva queda en estado "sin confirmar"
    Y el sistema registra un cargo de $5.000 por reserva de hora asociado al paciente
```

## HU-04 — Reagendar o cancelar una hora
Historia: Como paciente, quiero solicitar el reagendamiento o cancelación de una hora desde la plataforma, para modificar mi reserva sin depender del contacto con la secretaria o psicóloga.

```gherkin
Característica: Reagendamiento y cancelación de una reserva

  Escenario: El paciente cancela una reserva
    Dado que el paciente tiene una reserva confirmada para el viernes 13 de noviembre a las 18:00
    Cuando el paciente cancela la reserva
    Entonces la reserva queda en estado "cancelada"
    Y el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible

  Escenario: El paciente solicita reagendar y existen alternativas
    Dado que el paciente tiene una reserva confirmada para el viernes 13 de noviembre a las 18:00
    Y que existen bloques horarios disponibles en las dos semanas siguientes
    Cuando el paciente solicita reagendar la reserva
    Entonces el sistema informa los bloques horarios disponibles como alternativas
    Y la reserva original se mantiene vigente mientras el paciente no elija una alternativa

  Escenario: El paciente solicita reagendar y no existen alternativas
    Dado que el paciente tiene una reserva confirmada
    Y que no existen bloques horarios disponibles en las dos semanas siguientes
    Cuando el paciente solicita reagendar la reserva
    Entonces el sistema informa que no hay alternativas disponibles
    Y la reserva original se mantiene vigente
```

## HU-05 — Seleccionar una nueva hora
Historia: Como paciente, quiero seleccionar un nuevo horario disponible al reagendar, para reemplazar mi reserva anterior por una alternativa que se adapte a mi disponibilidad.

```gherkin
Característica: Selección de nueva hora al reagendar

  Escenario: El paciente elige una alternativa disponible
    Dado que el paciente solicitó reagendar su reserva del viernes 13 de noviembre a las 18:00
    Y que el bloque del lunes 16 de noviembre a las 17:00 está disponible
    Cuando el paciente elige el bloque del lunes 16 de noviembre a las 17:00
    Entonces la reserva queda asociada al lunes 16 de noviembre a las 17:00 en estado "pendiente de confirmación"
    Y el bloque del viernes 13 de noviembre a las 18:00 vuelve a estar disponible
    Y el servicio de mensajería envía al paciente el aviso de la reserva reagendada

  Escenario: La alternativa elegida fue tomada por otro paciente
    Dado que el paciente solicitó reagendar su reserva
    Y que el bloque del lunes 16 de noviembre a las 17:00 fue reservado por otro paciente
    Cuando el paciente elige el bloque del lunes 16 de noviembre a las 17:00
    Entonces el sistema rechaza el cambio indicando que el bloque ya no está disponible
    Y la reserva original se mantiene sin cambios
```

## HU-06 — Comprobar el pago
Historia: Como psicóloga, quiero consultar la información del pago asociada a una atención, para comprobar el pago sin depender únicamente de comprobantes enviados por WhatsApp.

```gherkin
Característica: Comprobación del pago de una atención

  Escenario: La atención tiene un comprobante de pago registrado
    Dado que el paciente registró un comprobante de transferencia por $30.000 para su atención del jueves 12 de noviembre
    Cuando la psicóloga consulta el pago de esa atención
    Entonces el sistema informa el monto, la fecha de la transferencia y la cuenta de destino del comprobante
    Y informa el monto que corresponde al tipo de atención

  Escenario: La atención no tiene comprobante de pago
    Dado que el paciente no ha registrado un comprobante de pago para su atención del jueves 12 de noviembre
    Cuando la psicóloga consulta el pago de esa atención
    Entonces el sistema informa que la atención no tiene comprobante de pago
    Y la atención aparece en el listado de atenciones con pago pendiente
```

## HU-07 — Registrar el estado de pago
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

## HU-08 — Emitir boleta
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
    Dado que la atención del jueves 12 de noviembre tiene su pago en estado "pendiente"
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

## HU-09 — Registrar asistencia e inasistencia
Historia: Como psicóloga, quiero registrar la asistencia o inasistencia del paciente en la plataforma, para mantener actualizado el estado de cada atención.

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
    Y el sistema registra un cargo de $5.000 por reserva de hora asociado al paciente

  Escenario: El paciente justifica la inasistencia
    Dado que el paciente tiene una reserva confirmada para el jueves 12 de noviembre a las 16:00
    Cuando la psicóloga registra que el paciente no asistió y justificó la inasistencia
    Entonces la atención queda en estado "inasistencia justificada"
    Y el sistema no registra cargo por reserva de hora
```

## HU-10 — Actualizar ficha clínica
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
