# Clasificación de requisitos
 

## Requisitos de producto

| ID | Requisito | Tipo (funcional/no funcional) | Actividad TO-BE asociada |
|---|---|---|---|
| RP-01 | El sistema deberá permitir al paciente consultar la disponibilidad de horas mediante la plataforma. | Funcional | Consultar disponibilidad en plataforma |
| RP-02 | El sistema deberá mostrar automáticamente al paciente los horarios disponibles para reservar una atención. | Funcional | Mostrar horarios disponibles |
| RP-03 | El sistema deberá permitir al paciente seleccionar un horario disponible. | Funcional | Seleccionar horario disponible |
| RP-04 | El sistema deberá registrar automáticamente la reserva cuando el paciente confirme el horario seleccionado, siempre que este continúe disponible. | Funcional | Registrar reserva automáticamente |
| RP-05 | El sistema deberá enviar automáticamente un aviso por correo electrónico al registrar una reserva y programar el envío de una solicitud de confirmación asociada a la hora reservada, con enlaces seguros para responder, según los plazos establecidos en el proceso. | Funcional | Enviar solicitud de confirmación automática |
| RP-06 | El sistema deberá permitir al paciente confirmar o cancelar una hora reservada desde la plataforma o desde el enlace seguro del correo, una vez enviada la solicitud de confirmación asociada y mientras exista una solicitud pendiente de respuesta. | Funcional | Confirmar o cancelar hora en plataforma |
| RP-07 | El sistema deberá permitir al paciente solicitar el reagendamiento o cancelación de una hora desde la plataforma. | Funcional | Solicitar reagendamiento o cancelación en plataforma |
| RP-08 | El sistema deberá consultar la disponibilidad de nuevas horas cuando el paciente solicite un reagendamiento. | Funcional | Consultar nueva disponibilidad en sistema |
| RP-09 | El sistema deberá mostrar automáticamente las alternativas disponibles para reagendar una atención. | Funcional | Mostrar nuevas alternativas disponibles |
| RP-10 | El sistema deberá permitir al paciente seleccionar un nuevo horario disponible. | Funcional | Seleccionar nuevo horario disponible |
| RP-11 | El sistema deberá actualizar automáticamente la reserva con el nuevo horario seleccionado. | Funcional | Actualizar reserva automáticamente |
| RP-12 | El sistema deberá permitir a la psicóloga consultar la información necesaria para comprobar el pago asociado a una atención. | Funcional | Comprobar pago con apoyo del sistema |
| RP-13 | El sistema deberá permitir registrar el estado de pago asociado al paciente y a la atención correspondiente. | Funcional | Registrar estado de pago en sistema |
| RP-14 | El sistema deberá apoyar la emisión de la boleta asociada a una atención pagada. | Funcional | Emitir boleta con apoyo del sistema |
| RP-15 | El sistema deberá permitir registrar la asistencia del paciente a la atención psicológica. | Funcional | Registrar asistencia en sistema |
| RP-16 | El sistema deberá permitir actualizar la ficha clínica del paciente dentro de la plataforma centralizada. | Funcional | Actualizar ficha clínica en sistema centralizado |
| RP-17 | El sistema deberá proteger la confidencialidad de la información personal, administrativa y clínica de los pacientes. | No funcional | Actualizar ficha clínica en sistema centralizado |
| RP-18 | La plataforma deberá ser utilizable desde dispositivos móviles para facilitar el acceso a la gestión de horas e información. | No funcional | Consultar disponibilidad en plataforma |
| RP-19 | El sistema deberá responder las consultas de disponibilidad de horarios en un tiempo máximo de 2 segundos, permitiendo una interacción rápida para los usuarios. | No funcional | Consultar disponibilidad en plataforma |
| RP-20 | El sistema deberá permitir que al menos el 90% de los usuarios complete las tareas principales de gestión de horas sin asistencia externa. | No funcional | Seleccionar horario disponible |
| RP-21 | El sistema deberá permitir al paciente registrar sus datos personales (nombre completo, RUT y medio de contacto) cuando aún no esté registrado. | Funcional | Registrar datos del paciente |
| RP-22 | El sistema deberá registrar un cargo de $5.000, asociado al paciente y a la reserva, cuando el paciente no responda la solicitud de confirmación hasta la hora de la atención. | Funcional | Registrar cargo por falta de confirmación |
| RP-23 | El sistema deberá permitir al paciente registrar el comprobante de transferencia asociado al pago de su atención. | Funcional | Realizar pago |
| RP-24 | El sistema deberá registrar un cargo de $5.000 por inasistencia sin justificación, asociado a la atención y al paciente, cuando la psicóloga registre la inasistencia; la inasistencia justificada no genera cargo. | Funcional | Registrar asistencia en sistema |
| RP-25 | El sistema deberá originar automáticamente la atención y el pago pendiente cuando llegue la hora de una reserva confirmada, y dejar la reserva en estado finalizada. | Funcional | Originar atención y pago automáticamente |
| RP-26 | El sistema deberá registrar un cargo de $5.000, asociado al paciente y a la reserva, cuando el paciente confirme la cancelación de una hora reservada. Las cancelaciones realizadas por la psicóloga no generan cargos. | Funcional | Registrar cargo por cancelación de reserva |


## Requisitos de proyecto

| ID | Requisito |
|---|---|
| RY-01 | El proyecto deberá desarrollar y documentar una plataforma web para la gestión de la consulta psicológica. |
| RY-02 | El desarrollo deberá mantener trazabilidad entre las actividades del proceso TO-BE, los requisitos de producto y las historias de usuario. |
| RY-03 | La documentación del proyecto deberá mantenerse actualizada conforme se modifiquen los requisitos o el proceso TO-BE. |
| RY-04 | El equipo deberá mantener los artefactos del proyecto organizados y versionados en el repositorio definido para el desarrollo. |

## Requisito derivado

### Requisito derivado RD-01

**Requisito origen:** RP-17 — El sistema deberá proteger la confidencialidad de la información personal, administrativa y clínica de los pacientes.

**Requisito derivado:** El sistema deberá restringir el acceso a la información clínica mediante autenticación y permisos según el rol del usuario.

**Justificación:** Este requisito se deriva de la necesidad de controlar quién puede acceder a la información clínica de los pacientes, permitiendo que cada usuario pueda visualizar únicamente la información correspondiente a sus permisos dentro del sistema.


### Requisito derivado RD-02

**Requisito origen:** RP-17 — El sistema deberá proteger la confidencialidad de la información personal, administrativa y clínica de los pacientes.

**Requisito derivado:** El sistema deberá cifrar la información sensible almacenada dentro de la plataforma.

**Justificación:** Este requisito se deriva de la necesidad de proteger los datos personales y clínicos de los pacientes frente a accesos no autorizados, manteniendo la seguridad de la información almacenada.
