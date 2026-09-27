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
| Solicitar hora por WhatsApp | Consultar disponibilidad y reservar hora en plataforma | El paciente deja de depender del contacto por WhatsApp y puede gestionar su hora directamente. |
| Revisar disponibilidad en Excel | Consultar disponibilidad en sistema | La disponibilidad deja de revisarse manualmente en Excel y pasa a estar centralizada en la plataforma. |
| Informar horarios disponibles | Mostrar horarios disponibles | El sistema presenta automáticamente las horas disponibles al paciente. |
| Seleccionar horario | Seleccionar horario disponible | El paciente mantiene esta acción, pero ahora la realiza directamente en la plataforma. |
| Registrar hora en Excel | Registrar reserva automáticamente | La reserva se guarda automáticamente al seleccionar el horario. |
| Confirmar asistencia por WhatsApp | Enviar confirmación automática | El sistema envía la solicitud de confirmación sin intervención manual de secretaria o psicóloga. |
| Responder confirmación | Confirmar o cancelar hora en plataforma | El paciente responde directamente en el sistema. |
| Revisar nueva disponibilidad en Excel | Consultar nueva disponibilidad en sistema | Si se reagenda, la disponibilidad se obtiene desde la misma plataforma. |
| Informar nuevos horarios disponibles | Mostrar nuevas alternativas disponibles | El sistema presenta automáticamente opciones de reagendamiento. |
| Registrar nueva hora en Excel | Actualizar reserva automáticamente | La nueva hora queda registrada automáticamente al seleccionar una alternativa. |
| Registrar estado de pago en Excel | Registrar estado de pago en sistema | El estado del pago queda asociado a la atención y al paciente dentro de la plataforma. |
| Actualizar ficha clínica | Actualizar ficha clínica en sistema centralizado | La información clínica queda integrada con el resto de la información del paciente. |
