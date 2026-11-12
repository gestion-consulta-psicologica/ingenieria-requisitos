# Historias de usuario

## HU-01 — Consultar disponibilidad

Como paciente, quiero consultar la disponibilidad de horas en la plataforma, para conocer las opciones de atención sin depender de una coordinación por WhatsApp.

Actividad TO-BE asociada: Consultar disponibilidad en plataforma.

Criterios de aceptación

- CA1 — Acceso a la consulta: Dado que el paciente ingresa a la plataforma, cuando accede a la opción de consultar disponibilidad, entonces el sistema muestra los horarios disponibles para reservar una atención.

- CA2 — Visualización de horarios disponibles: Dado que existen horarios disponibles y registrados en el sistema, cuando el paciente consulta la disponibilidad, entonces la plataforma muestra únicamente los horarios que se encuentran disponibles para reserva.

- CA3 — Correspondencia de la información: Dado que la disponibilidad de horarios está registrada en el sistema, cuando el paciente consulta los horarios, entonces la información mostrada debe coincidir con los datos de disponibilidad registrados.

- CA4 — Ausencia de disponibilidad: Dado que no existen horarios disponibles para reservar, cuando el paciente consulta la disponibilidad, entonces la plataforma informa que no hay horarios disponibles para reserva.

- CA5 — Próximo bloque disponible: Dado que no existen horarios disponibles para la semana consultada, cuando el paciente consulta la disponibilidad, entonces la plataforma informa que no hay horas disponibles e indica la fecha del próximo bloque horario disponible.

## HU-02 — Reservar una hora

Como paciente, quiero seleccionar un horario disponible, para reservar una hora de atención directamente desde la plataforma.

**Actividad TO-BE asociada:** Seleccionar horario disponible

**Criterios de aceptación:**

- CA1 — Selección de horario: dado que el sistema muestra horarios disponibles, cuando el paciente selecciona uno de ellos, entonces el sistema muestra el horario seleccionado como opción para continuar con la reserva.

- CA2 — Registro de la reserva:  Dado que el paciente ha seleccionado un horario que continúa disponible, cuando confirma la reserva, entonces el sistema registra automáticamente la reserva asociada al horario seleccionado.

- CA3 — Actualización de disponibilidad: Dado que la reserva se ha registrado correctamente, cuando el sistema actualiza la disponibilidad, entonces el horario reservado deja de mostrarse como disponible para nuevas reservas.

- CA4 — Solicitud de confirmación: Dado que la reserva se ha registrado correctamente, cuando finaliza el registro, entonces el sistema envía automáticamente una solicitud de confirmación al paciente.

- CA5 — Horario reservado por otro paciente: Dado que el horario seleccionado deja de estar disponible antes de completar la reserva, cuando el paciente intenta reservarlo, entonces el sistema no registra una nueva reserva para ese horario e informa que ya no está disponible.

## HU-03 — Confirmar o cancelar una hora

Como paciente, quiero confirmar si mantengo o no una hora que tengo reservada, para informar mi decisión sobre la atención y continuar con el proceso correspondiente desde la plataforma.

**Actividad TO-BE asociada:** Confirmar o cancelar hora en plataforma.

**Criterios de aceptación:**

- **CA1 — Selección de respuesta:** Dado que el paciente tiene una hora reservada y ha recibido una solicitud de confirmación, cuando accede a la opción correspondiente en la plataforma, entonces el sistema le permite indicar si mantiene o no mantiene la hora reservada.

- **CA2 — Registro de respuesta:** Dado que el paciente ha seleccionado una respuesta, cuando confirma su decisión, entonces el sistema registra la respuesta asociada a la reserva.

- **CA3 — Mantener la hora:** Dado que el paciente indica que mantiene su hora, cuando confirma su decisión en la plataforma, entonces el sistema conserva la reserva y permite continuar con el proceso de pago según el flujo definido en el TO-BE.

- **CA4 — No mantener la hora:** Dado que el paciente indica que no mantiene su hora, cuando confirma su decisión en la plataforma, entonces el sistema permite continuar hacia el proceso de gestión de la reserva, donde el paciente puede solicitar su cancelación o reagendamiento.
  
## HU-04 — Reagendar o cancelar una hora

Como paciente, quiero gestionar una hora que tengo reservada desde la plataforma, para cancelarla o cambiarla por otro horario sin depender del contacto con la secretaria o la psicóloga.

**Actividad TO-BE asociada:** Solicitar reagendamiento o cancelación en plataforma; consultar nuevas horas disponibles; seleccionar nuevo horario; actualizar reserva.

**Criterios de aceptación:**

- **CA1 — Selección de acción:** Dado que el paciente tiene una hora reservada, cuando accede a las opciones de gestión de su reserva, entonces el sistema le permite seleccionar entre reagendar o cancelar la hora.

- **CA2 — Cancelación de reserva:** Dado que el paciente ha seleccionado la opción de cancelación para una reserva existente, cuando confirma su decisión, entonces el sistema registra la reserva como cancelada y libera el horario para una nueva reserva.

- **CA3 — Consulta de disponibilidad:** Dado que el paciente ha seleccionado la opción de reagendar, cuando solicita cambiar su hora, entonces el sistema consulta la disponibilidad registrada y obtiene las alternativas disponibles para realizar el cambio.

- **CA4 — Visualización de alternativas:** Dado que existen horarios disponibles para el reagendamiento, cuando el sistema presenta los resultados de la consulta, entonces el paciente puede visualizar las alternativas disponibles para seleccionar un nuevo horario.

- **CA5 — Selección del nuevo horario:** Dado que el sistema muestra alternativas disponibles, cuando el paciente selecciona una de ellas, entonces el sistema identifica el horario seleccionado y lo presenta como opción para confirmar el reagendamiento.

-  **CA6 — Actualización de la reserva:** Dado que el paciente ha seleccionado un nuevo horario disponible, cuando el sistema verifica que el horario continúa disponible y actualiza la reserva, entonces el sistema registra el nuevo horario y libera el horario anterior.

- **CA7 — Nuevo horario no disponible:** Dado que el horario seleccionado deja de estar disponible antes de completar el reagendamiento, cuando el paciente intenta confirmar el cambio, entonces el sistema no actualiza la reserva con ese horario e informa que debe seleccionar otra alternativa.

- **CA8 — Sin horarios disponibles:** Dado que el paciente ha solicitado reagendar su hora y no existen nuevos horarios disponibles, cuando el sistema consulta la disponibilidad, entonces informa que no hay alternativas disponibles y conserva la reserva original.

## HU-05 — Comprobar el pago

Como psicóloga, quiero consultar la información del pago asociada a una atención, para comprobar su estado sin depender únicamente de comprobantes enviados por WhatsApp.

**Actividad TO-BE asociada:** Comprobar pago con apoyo del sistema.

**Criterios de aceptación:**

- **CA1 — Consulta de información de pago:** Dado que existe una atención registrada, cuando la psicóloga consulta la información de pago asociada, entonces el sistema muestra los datos disponibles correspondientes a esa atención.

- **CA2 — Consulta de antecedentes del pago:** Dado que existe un comprobante u otro antecedente de pago registrado, cuando la psicóloga consulta la información de la atención, entonces el sistema permite visualizar dicho antecedente, si está disponible.

- **CA3 — Resultado de la comprobación:** Dado que la psicóloga ha revisado la información y los antecedentes disponibles, cuando realiza la comprobación del pago, entonces la plataforma le permite continuar con la actividad de registro del estado del pago, sin determinar automáticamente el resultado de la comprobación.

## HU-06 — Registrar el estado de pago

Como psicóloga, quiero registrar el estado de pago de una atención en la plataforma, para mantener actualizada la información administrativa del paciente.

**Actividad TO-BE asociada:** Registrar estado de pago en sistema.

**Criterios de aceptación:**

- **CA1 — Registro del estado de pago:** Dado que la psicóloga ha comprobado la información del pago de una atención, cuando selecciona y guarda el estado correspondiente en la plataforma, entonces el sistema almacena el estado registrado y lo muestra como parte de la información de esa atención.

- **CA2 — Asociación con el paciente:** Dado que la psicóloga registra el estado de pago de una atención, cuando el sistema guarda el registro, entonces este queda asociado al paciente correspondiente.

- **CA3 — Asociación con la atención:** Dado que la psicóloga registra el estado de pago, cuando el sistema guarda el registro, entonces este queda asociado a la atención correspondiente y puede consultarse desde su información.

- **CA4 — Confirmación del registro:** Dado que la psicóloga ha ingresado la información del estado de pago, cuando guarda el registro correctamente, entonces el sistema muestra una confirmación de que la operación se completó.
  
## HU-07 — Emitir boleta

Como psicóloga, quiero emitir una boleta desde la plataforma mediante un servicio de emisión integrado, para reducir el tiempo destinado a tareas administrativas.

**Actividad TO-BE asociada:** Emitir boleta con apoyo del sistema.

**Criterios de aceptación:**

- **CA1 — Inicio de emisión:** Dado que existe una atención registrada y la información necesaria está disponible, cuando la psicóloga solicita emitir la boleta, entonces el sistema prepara la información correspondiente y permite iniciar la solicitud de emisión.

- **CA2 — Asociación con la atención:** Dado que se solicita emitir una boleta para una atención, cuando el servicio de emisión procesa la solicitud correctamente, entonces el sistema asocia la boleta emitida con la atención correspondiente.

- **CA3 — Resultado de emisión:** Dado que la psicóloga ha solicitado emitir una boleta, cuando el servicio de emisión responde, entonces el sistema informa si la emisión fue exitosa o si ocurrió un error.

- **CA4 — Información insuficiente:** Dado que falta información obligatoria para emitir la boleta, cuando la psicóloga intenta iniciar la emisión, entonces el sistema informa qué información falta y no envía una solicitud incompleta al servicio de emisión.

## HU-08 — Registrar asistencia e inasistencia

Como psicóloga, quiero registrar la asistencia o inasistencia del paciente en la plataforma, para mantener actualizado el estado de cada atención.

**Actividad TO-BE asociada:** Registrar asistencia en sistema.

**Criterios de aceptación:**

- **CA1 — Registro de asistencia:** Dado que existe una atención programada, cuando la psicóloga registra si el paciente asistió o no asistió y guarda la información, entonces el sistema almacena el resultado del registro e informa que la operación se completó correctamente.

- **CA2 — Asociación del registro:** Dado que la psicóloga ha registrado la asistencia o inasistencia, cuando el sistema guarda la información, entonces el registro queda asociado al paciente y a la atención correspondiente.

- **CA3 — Consulta posterior:** Dado que la asistencia o inasistencia ha sido registrada correctamente, cuando la psicóloga consulta la información de la atención, entonces el sistema muestra el registro almacenado.

## HU-09 — Actualizar ficha clínica

Como psicóloga, quiero actualizar la ficha clínica del paciente en una plataforma centralizada, para mantener la información clínica organizada y disponible para el seguimiento de sus atenciones.

**Actividad TO-BE asociada:** Actualizar ficha clínica en sistema centralizado.

**Criterios de aceptación:**

- **CA1 — Acceso a la ficha clínica:** Dado que la psicóloga ha iniciado sesión y cuenta con los permisos correspondientes, cuando accede a la ficha clínica de un paciente, entonces el sistema muestra la información clínica registrada en esa ficha.
- **CA2 — Actualización de información clínica:** Dado que la psicóloga ha accedido a la ficha clínica y cuenta con los permisos necesarios, cuando registra o modifica información clínica y guarda los cambios, entonces el sistema informa que la actualización se ha realizado correctamente.
- **CA3 — Persistencia de los cambios:** Dado que la psicóloga ha guardado correctamente los cambios en la ficha clínica, cuando vuelve a consultar esa ficha, entonces el sistema muestra la información actualizada.
- **CA4 — Acceso no autorizado:** Dado que un usuario no cuenta con los permisos necesarios para acceder a una ficha clínica, cuando intenta consultar o modificar esa información, entonces el sistema deniega el acceso e impide la consulta o modificación de los datos clínicos.
