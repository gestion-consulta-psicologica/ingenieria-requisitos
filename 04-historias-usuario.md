# Historias de usuario

## HU-01 — Consultar disponibilidad

Como paciente, quiero consultar la disponibilidad de horas en la plataforma, para conocer las opciones de atención sin depender de una coordinación por WhatsApp.

**Actividad TO-BE asociada:** Consultar disponibilidad en plataforma

**Criterios de aceptación:**
- CA1: El paciente puede ingresar a la opción de consulta de disponibilidad.
- CA2: El sistema muestra únicamente horarios disponibles para reserva.
- CA3: La información mostrada corresponde a la disponibilidad registrada en el sistema.

## HU-02 — Reservar una hora

Como paciente, quiero seleccionar un horario disponible, para reservar una hora de atención directamente desde la plataforma.

**Actividad TO-BE asociada:** Seleccionar horario disponible

**Criterios de aceptación:**
- CA1: El paciente puede seleccionar uno de los horarios disponibles mostrados por el sistema.
- CA2: El sistema registra automáticamente la reserva correspondiente al horario seleccionado.
- CA3: Una vez registrada la reserva, ese horario deja de aparecer como disponible para una nueva reserva.
- CA4: Luego de registrar la reserva, el sistema envía automáticamente una solicitud de confirmación al paciente.

## HU-03 — Confirmar o cancelar una hora

Como paciente, quiero confirmar o cancelar mi hora desde la plataforma, para gestionar mi asistencia sin tener que responder mediante WhatsApp.

**Actividad TO-BE asociada:** Confirmar o cancelar hora en plataforma

**Criterios de aceptación:**
- CA1: El sistema permite al paciente indicar si mantiene o cancela la hora reservada.
- CA2: La respuesta del paciente queda registrada en el sistema.
- CA3: Si el paciente mantiene la hora, el proceso continúa hacia el pago.
- CA4: Si el paciente no mantiene la hora, el sistema permite continuar con la opción de reagendar o cancelar.

## HU-04 — Reagendar o cancelar una hora

Como paciente, quiero solicitar el reagendamiento o cancelación de una hora desde la plataforma, para modificar mi reserva sin depender del contacto con la secretaria o psicóloga.

**Actividad TO-BE asociada:** Solicitar reagendamiento o cancelación en plataforma

**Criterios de aceptación:**
- CA1: El paciente puede seleccionar si desea reagendar o cancelar su hora.
- CA2: Si cancela, la reserva queda cancelada y el proceso finaliza.
- CA3: Si solicita reagendar, el sistema consulta nuevas horas disponibles.
- CA4: El sistema muestra alternativas disponibles para realizar el cambio.

## HU-05 — Seleccionar una nueva hora

Como paciente, quiero seleccionar un nuevo horario disponible al reagendar, para reemplazar mi reserva anterior por una alternativa que se adapte a mi disponibilidad.

**Actividad TO-BE asociada:** Seleccionar nuevo horario disponible

**Criterios de aceptación:**
- CA1: El sistema muestra al paciente las nuevas alternativas disponibles.
- CA2: El paciente puede seleccionar una nueva alternativa de horario.
- CA3: El sistema actualiza automáticamente la reserva con el nuevo horario.
- CA4: Después del cambio, el sistema vuelve a solicitar la confirmación de la hora.

## HU-06 — Comprobar el pago

Como psicóloga, quiero consultar la información del pago asociada a una atención, para comprobar el pago sin depender únicamente de comprobantes enviados por WhatsApp.

**Actividad TO-BE asociada:** Comprobar pago con apoyo del sistema

**Criterios de aceptación:**
- CA1: La psicóloga puede consultar la información de pago asociada al paciente y a la atención.
- CA2: La información necesaria para verificar el pago se encuentra centralizada en la plataforma.
- CA3: La psicóloga puede determinar el estado del pago a partir de la información disponible.

## HU-07 — Registrar el estado de pago

Como psicóloga, quiero registrar el estado de pago de una atención en la plataforma, para mantener actualizada la información administrativa del paciente.

**Actividad TO-BE asociada:** Registrar estado de pago en sistema

**Criterios de aceptación:**
- CA1: La psicóloga puede registrar el estado de pago de una atención.
- CA2: El estado registrado queda asociado al paciente correspondiente.
- CA3: El estado registrado queda asociado a la atención correspondiente.

## HU-08 — Emitir boleta

Como psicóloga, quiero emitir la boleta con apoyo de la plataforma, para reducir el tiempo destinado a tareas administrativas.

**Actividad TO-BE asociada:** Emitir boleta con apoyo del sistema

**Criterios de aceptación:**
- CA1: La psicóloga puede iniciar la emisión de la boleta desde la plataforma.
- CA2: La boleta queda asociada a la atención correspondiente.
- CA3: La información necesaria para su emisión puede obtenerse desde los datos registrados en el sistema.

## HU-09 — Registrar asistencia e inasistencia

Como psicóloga, quiero registrar la asistencia o inasistencia del paciente en la plataforma, para mantener actualizado el estado de cada atención.

**Actividad TO-BE asociada:** Registrar asistencia en sistema

**Criterios de aceptación:**
- CA1: La psicóloga puede registrar si el paciente asistió o no a la atención.
- CA2: El registro de asistencia queda asociado al paciente y a la atención correspondiente.
- CA3: La información queda almacenada en la plataforma para su consulta posterior.

## HU-10 — Actualizar ficha clínica

Como psicóloga, quiero actualizar la ficha clínica del paciente en una plataforma centralizada, para mantener la información clínica organizada y disponible para el seguimiento de sus atenciones.

**Actividad TO-BE asociada:** Actualizar ficha clínica en sistema centralizado

**Criterios de aceptación:**
- CA1: La psicóloga puede acceder a la ficha clínica del paciente correspondiente.
- CA2: La psicóloga puede registrar y actualizar la información clínica de la atención.
- CA3: Los cambios realizados quedan almacenados en la ficha clínica del paciente.
- CA4: El acceso a la información clínica debe estar restringido según los permisos del usuario.
