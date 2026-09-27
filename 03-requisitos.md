# Clasificación de requisitos
 
# Clasificación de requisitos

## Requisitos de producto

| ID | Requisito | Tipo (funcional/no funcional) | Actividad TO-BE asociada |
|---|---|---|---|
| RP-01 | El sistema deberá permitir al paciente consultar la disponibilidad de horas mediante la plataforma. | Funcional | Consultar disponibilidad en plataforma |
| RP-02 | El sistema deberá mostrar automáticamente al paciente los horarios disponibles para reservar una atención. | Funcional | Mostrar horarios disponibles |
| RP-03 | El sistema deberá permitir al paciente seleccionar un horario disponible. | Funcional | Seleccionar horario disponible |
| RP-04 | El sistema deberá registrar automáticamente la reserva cuando el paciente seleccione un horario. | Funcional | Registrar reserva automáticamente |
| RP-05 | El sistema deberá enviar automáticamente una solicitud de confirmación asociada a la hora reservada. | Funcional | Enviar solicitud de confirmación automática |
| RP-06 | El sistema deberá permitir al paciente confirmar o cancelar una hora reservada desde la plataforma. | Funcional | Confirmar o cancelar hora en plataforma |
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
 
## Requisitos de proyecto

| ID | Requisito |
|---|---|
| RY-01 | El proyecto deberá desarrollar una plataforma web para centralizar la gestión de reservas, pagos, asistencia e información clínica de los pacientes. |
| RY-02 | El desarrollo deberá mantener trazabilidad entre las actividades del proceso TO-BE, los requisitos de producto y las historias de usuario. |
| RY-03 | El sistema deberá ser desarrollado considerando la protección de la información personal y clínica de los pacientes durante todo el proyecto. |
| RY-04 | El proyecto deberá contemplar una interfaz adaptable a dispositivos móviles para facilitar el acceso de pacientes y psicóloga. |
 
## Requisito derivado

**Requisito origen:** RP-17 — El sistema deberá proteger la confidencialidad de la información personal, administrativa y clínica de los pacientes.

**Requisito derivado:** El sistema deberá restringir el acceso a la información clínica mediante autenticación y permisos según el rol del usuario.

**Justificación:** Este requisito se deriva de la necesidad de proteger la confidencialidad de los datos del paciente. Para cumplir con RP-17, no basta con almacenar la información de forma centralizada; es necesario controlar quién puede acceder a los distintos tipos de información según su rol dentro del sistema.
