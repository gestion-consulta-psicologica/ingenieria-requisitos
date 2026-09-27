# Proceso de negocio — AS-IS
 
## Macro-proceso y proceso específico

**Macroproceso:** Gestión de atención psicológica.

**Proceso específico:** Gestión de horas, confirmación de asistencia y seguimiento administrativo de pacientes.
 
## Objetivo de negocio del proceso
Coordinar y registrar la atención de pacientes de una consulta psicológica, gestionando la solicitud de horas, disponibilidad, confirmación de asistencia, pagos, reagendamientos e información asociada a los pacientes.

## Participantes y sus objetivos

| Participante | Objetivo en el proceso |
|---|---|
| Paciente | Solicitar, confirmar, cambiar o cancelar una hora de atención y cumplir con el proceso de pago correspondiente. |
| Secretaria | Coordinar horas, confirmar asistencia y apoyar la gestión administrativa de los pacientes. |
| Psicóloga | Gestionar su disponibilidad, coordinar y confirmar atenciones, verificar pagos y mantener actualizada la información de sus pacientes. |

## Descripción general del proceso actual

Actualmente, el paciente solicita una hora mediante WhatsApp. La psicóloga o la secretaria revisa la disponibilidad en la planilla Excel y comunica las alternativas disponibles al paciente.

Una vez seleccionado el horario, la psicóloga o la secretaria registra la hora en la planilla. Antes de la sesión, la asistencia es confirmada con el paciente. Si el paciente necesita cambiar o cancelar la hora, se revisa nuevamente la disponibilidad y se coordina una nueva fecha.

Los pagos son comprobados por la psicóloga y su estado se registra junto con la asistencia, reagendamientos e inasistencias. Posteriormente, la psicóloga realiza la atención y actualiza la información clínica del paciente.

## Diagrama AS-IS
![Proceso AS-IS](./diagramas/as-is.png)
 
Archivo fuente: [`./diagramas/as-is.bpmn`](./diagramas/as-is.bpmn)
 
 
## Problemas identificados

- **Psicóloga y secretaria — Objetivo: coordinar y confirmar las atenciones.**
  La confirmación de horas requiere gestión manual mediante contacto con los pacientes.

- **Psicóloga — Objetivo: verificar y registrar correctamente los pagos.**
  La comprobación de pagos puede ser difícil de realizar oportunamente, ya que los pagos pueden efectuarse en distintos momentos y requieren revisar comprobantes enviados por WhatsApp.

- **Psicóloga y secretaria — Objetivo: gestionar y mantener organizada la agenda.**
  La gestión de la agenda depende de la actualización manual de una planilla Excel.

- **Psicóloga — Objetivo: realizar la atención y gestionar las tareas administrativas asociadas.**
  La emisión de boletas consume tiempo dentro de la gestión administrativa.

- **Psicóloga — Objetivo: mantener actualizada y accesible la información de los pacientes.**
  La información de agenda y la información clínica se gestionan mediante herramientas separadas.

- **Psicóloga — Objetivo: gestionar adecuadamente la información de sus pacientes.**
  La información personal y clínica requiere un adecuado resguardo debido a su carácter confidencial.
