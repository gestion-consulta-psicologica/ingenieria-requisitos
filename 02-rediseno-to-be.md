# Análisis de rediseño y propuesta TO-BE
 
## Mejoras identificadas por participante

| Participante | Objetivo | Problema | Mejora deseada |
|---|---|---|---|
| Paciente | Solicitar, confirmar, cambiar o cancelar una hora de atención y cumplir con el proceso de pago correspondiente. | La solicitud, confirmación y cambios de hora dependen de la comunicación por WhatsApp con la secretaria o la psicóloga. | Permitir que el paciente consulte disponibilidad, solicite y gestione sus horas mediante una plataforma de manera más autónoma. |
| Secretaria | Coordinar horas, confirmar asistencia y apoyar la gestión administrativa de los pacientes. | La agenda se administra manualmente en Excel y la confirmación de horas requiere contactar individualmente a los pacientes. | Centralizar la gestión de agenda y reducir las tareas manuales mediante disponibilidad actualizada y confirmaciones automatizadas. |
| Psicóloga | Gestionar su disponibilidad, coordinar y confirmar atenciones, verificar pagos y mantener actualizada la información de sus pacientes. | Debe comprobar pagos mediante comprobantes enviados por WhatsApp, emitir boletas, revisar información en herramientas separadas y gestionar datos confidenciales. | Centralizar la información administrativa y clínica, facilitar la comprobación de pagos y disminuir tareas administrativas repetitivas, manteniendo el resguardo de la información. |
 
## Iniciativas de rediseño
### Iniciativa 1: Autogestión de horas por parte del paciente
- Actividad(es) del AS-IS que afecta: Solicitar hora por WhatsApp, Revisar disponibilidad en Excel, Informar horarios disponibles, Seleccionar horario, Registrar hora en Excel, Revisar nueva disponibilidad en Excel, Informar nuevos horarios disponibles y Registrar nueva hora en Excel.
- Heurística aplicada: Tecnología integral.
- Objetivo o mejora que resuelve: Permitir que el paciente consulte disponibilidad y gestione sus horas de manera más autónoma, reduciendo la dependencia de la secretaria o la psicóloga.
- Efecto esperado:
  - Tiempo: disminución del tiempo de coordinación de horas.
  - Costo: reducción del trabajo administrativo asociado a la gestión manual de agenda.
  - Calidad: menor probabilidad de errores de registro y disponibilidad.
  - Flexibilidad: mayor autonomía para que el paciente gestione sus horas.

### Iniciativa 2: Automatización de la confirmación de horas
- Actividad(es) del AS-IS que afecta: Confirmar asistencia por WhatsApp y Responder confirmación.
- Heurística aplicada: Automatización de tareas.
- Objetivo o mejora que resuelve: Reducir la gestión manual de confirmaciones realizada por la secretaria y la psicóloga.
- Efecto esperado:
  - Tiempo: reducción del tiempo destinado a contactar pacientes.
  - Costo: menor carga administrativa.
  - Calidad: confirmaciones más consistentes y registradas en el sistema.
  - Flexibilidad: posibilidad de responder la confirmación sin depender de contacto directo.

### Iniciativa 3: Centralización de la información de agenda, pagos y pacientes
- Actividad(es) del AS-IS que afecta: Revisar disponibilidad en Excel, Registrar hora en Excel, Registrar nueva hora en Excel, Registrar estado de pago en Excel y Actualizar ficha clínica.
- Heurística aplicada: Integración.
- Objetivo o mejora que resuelve: Evitar que la información administrativa y clínica se gestione mediante herramientas separadas.
- Efecto esperado:
  - Tiempo: menor tiempo de búsqueda y actualización de información.
  - Costo: reducción de tareas duplicadas.
  - Calidad: información más consistente y actualizada.
  - Flexibilidad: acceso centralizado desde una misma plataforma.

### Iniciativa 4: Reducción de contactos administrativos
- Actividad(es) del AS-IS que afecta: Solicitar hora por WhatsApp, Informar horarios disponibles, Confirmar asistencia por WhatsApp e Informar nuevos horarios disponibles.
- Heurística aplicada: Reducción de contacto.
- Objetivo o mejora que resuelve: Disminuir las interacciones manuales necesarias para coordinar una atención.
- Efecto esperado:
  - Tiempo: menos intercambios de mensajes.
  - Costo: menor carga operativa para secretaria y psicóloga.
  - Calidad: menor riesgo de omisiones o errores de comunicación.
  - Flexibilidad: mayor independencia del paciente durante la gestión de su hora.
 
## Diagrama TO-BE
![Proceso TO-BE](./diagramas/to-be.png)
 
Archivo fuente: [`./diagramas/to-be.bpmn`](./diagramas/to-be.bpmn)
 
Nota: distingan tareas de usuario, de servicio y manuales con el marcador correspondiente.
 
## Actividades que cambian del AS-IS al TO-BE

| Actividad en el AS-IS | Actividad en el TO-BE | Qué cambia |
|---|---|---|
| Solicitar hora por WhatsApp | Consultar disponibilidad en plataforma | El paciente deja de solicitar la hora por WhatsApp y accede directamente a la plataforma para revisar opciones disponibles. |
| Revisar disponibilidad en Excel | Consultar disponibilidad en sistema | La disponibilidad deja de revisarse manualmente en Excel y pasa a estar centralizada en el sistema. |
| Informar horarios disponibles | Mostrar horarios disponibles | El sistema presenta automáticamente al paciente los horarios que se encuentran disponibles. |
| Seleccionar horario | Seleccionar horario disponible | El paciente selecciona directamente en la plataforma el horario que desea reservar. |
| Registrar hora en Excel | Registrar reserva automáticamente | El sistema registra automáticamente la reserva una vez seleccionado el horario. |
| Confirmar asistencia por WhatsApp | Enviar solicitud de confirmación automática | El sistema envía automáticamente la solicitud de confirmación de la hora, sin intervención manual de la secretaria o psicóloga. |
| Responder confirmación | Confirmar o cancelar hora en plataforma | El paciente indica directamente en la plataforma si mantiene o cancela la hora reservada. |
| Solicitar cambio o cancelación | Solicitar reagendamiento o cancelación en plataforma | El paciente puede gestionar el cambio o la cancelación desde la plataforma, sin depender del contacto por WhatsApp. |
| Revisar nueva disponibilidad en Excel | Consultar nueva disponibilidad en sistema | Cuando el paciente solicita reagendar, la disponibilidad se obtiene directamente desde el sistema. |
| Informar nuevos horarios disponibles | Mostrar nuevas alternativas disponibles | El sistema presenta automáticamente las nuevas opciones disponibles para reagendar. |
| Seleccionar horario | Seleccionar nuevo horario disponible | El paciente selecciona en la plataforma una nueva alternativa de horario. |
| Registrar nueva hora en Excel | Actualizar reserva automáticamente | El sistema actualiza automáticamente la reserva con el nuevo horario seleccionado. |
| Comprobar pago | Comprobar pago con apoyo del sistema | La psicóloga revisa el pago utilizando la información centralizada en la plataforma, reduciendo la dependencia de comprobantes enviados por WhatsApp. |
| Registrar estado de pago en Excel | Registrar estado de pago en sistema | El estado del pago queda registrado dentro de la plataforma y asociado al paciente y a la atención correspondiente. |
| Emitir boleta | Emitir boleta con apoyo del sistema | La emisión de la boleta se realiza desde la plataforma, reduciendo el trabajo administrativo asociado al proceso. |
| Realizar atención psicológica | Realizar atención psicológica | La atención psicológica se mantiene como una actividad manual, ya que corresponde al servicio principal prestado por la psicóloga. |
| Registrar asistencia en Excel | Registrar asistencia en sistema | La asistencia deja de registrarse en Excel y pasa a quedar almacenada en la plataforma. |
| Actualizar ficha clínica | Actualizar ficha clínica en sistema centralizado | La información clínica se registra en la misma plataforma, integrada con la información administrativa del paciente. |ra queda registrada automáticamente al seleccionar una alternativa. |
| Registrar estado de pago en Excel | Registrar estado de pago en sistema | El estado del pago queda asociado a la atención y al paciente dentro de la plataforma. |
| Actualizar ficha clínica | Actualizar ficha clínica en sistema centralizado | La información clínica queda integrada con el resto de la información del paciente. |
