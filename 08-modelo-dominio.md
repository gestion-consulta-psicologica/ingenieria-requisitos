# Modelo de dominio

## Diagrama
![Modelo de dominio](./diagramas/modelo-dominio.png)

Archivo fuente: [`./diagramas/modelo-dominio.puml`](./diagramas/modelo-dominio.puml)

## Descripción de las clases
| Clase | Qué representa en el negocio | Atributos |
|-------|------------------------------|-----------|
| Psicologa | Profesional titular de la consulta, que ofrece horas de atención y emite las boletas de honorarios. | nombreCompleto, rut, correo |
| Paciente | Persona que se atiende en la consulta y que reserva, confirma y paga sus horas. | nombreCompleto, rut, fechaNacimiento, direccion, escolaridad, ocupacion, telefono, correo |
| BloqueHorario | Espacio de tiempo de un día que la psicóloga dispone para atender. Está disponible si no tiene una reserva vigente. | fecha, horaInicio, horaTermino, modalidad (presencial / online) |
| Reserva | Compromiso de un paciente de asistir a un bloque horario. | fechaRegistro, estado (pendiente de confirmación, confirmada, sin confirmar, cancelada) |
| SolicitudConfirmacion | Mensaje enviado al paciente para que confirme o cancele su asistencia (el día anterior y en la mañana de la atención). | fechaEnvio, tipo (aviso de víspera / recordatorio), respuesta (confirma / no asistirá / sin respuesta) |
| Atencion | Sesión psicológica que se origina de una reserva confirmada. | tipoAtencion (presencial / online), monto, estado (programada, realizada, inasistencia, inasistencia justificada) |
| Pago | Obligación de pago de una atención y su situación. | montoAtencion, montoPagado, estado (pendiente, pagado, pago incompleto) |
| ComprobanteTransferencia | Respaldo de la transferencia que hace el paciente para pagar una atención. | monto, fechaTransferencia, cuentaDestino |
| Cargo | Cobro de $5.000 por reserva de hora cuando el paciente no confirma o no asiste sin justificación. | monto, motivo (sin confirmar / inasistencia), fecha |
| Boleta | Boleta de honorarios electrónica que respalda el cobro de una atención pagada. | numeroFolio, fechaEmision, monto, estado (en preparación, pendiente de emisión, emitida) |
| FichaClinica | Registro clínico del paciente con sus antecedentes (anamnesis). | fechaApertura, motivoConsulta, antecedentesSaludMental, diagnosticos, medicamentos, datosAdultoResponsable |
| RegistroEvolucion | Anotación clínica de la psicóloga sobre una atención realizada. | fecha, observaciones, pruebasAplicadas |

## Asociaciones
| Asociación | Clases | Multiplicidades | Justificación |
|------------|--------|-----------------|----------------|
| ofrece | Psicologa – BloqueHorario | 1 a 0..* | La psicóloga define su disponibilidad. Cada bloque horario pertenece a la única psicóloga de la consulta. |
| realiza | Paciente – Reserva | 1 a 0..* | Un paciente puede tener muchas reservas en el tiempo. Cada reserva es de un solo paciente. |
| ocupa | Reserva – BloqueHorario | 0..* a 1 | Cada reserva ocupa un bloque horario. Un bloque puede acumular reservas canceladas en su historia, pero solo una reserva vigente a la vez. |
| recibe | Reserva – SolicitudConfirmacion | 1 a 0..* | Se envía el aviso de víspera y el recordatorio de la mañana; al reagendar se envían solicitudes nuevas. |
| origina | Reserva – Atencion | 1 a 0..1 | Solo una reserva confirmada da origen a una atención. Una reserva cancelada no tiene atención. |
| genera | Reserva – Cargo | 1 a 0..1 | Una reserva sin confirmar o con inasistencia sin justificación genera un cargo de $5.000. |
| adeuda | Paciente – Cargo | 1 a 0..* | Los cargos por reserva de hora quedan a nombre del paciente. |
| se paga con | Atencion – Pago | 1 a 1 | Toda atención tiene un pago asociado, cuyo estado puede estar pendiente. |
| se respalda con | Pago – ComprobanteTransferencia | 1 a 0..* | El paciente envía uno o más comprobantes; con varios se completa un pago incompleto. |
| se documenta con | Atencion – Boleta | 1 a 0..1 | Solo se emite boleta cuando la atención está pagada. |
| emite | Psicologa – Boleta | 1 a 0..* | La psicóloga es la emisora de las boletas de honorarios ante el SII. |
| tiene | Paciente – FichaClinica | 1 a 1 | Cada paciente tiene una única ficha clínica. |
| contiene | FichaClinica – RegistroEvolucion | 1 a 0..* (composición) | Los registros de evolución son parte de la ficha y no existen fuera de ella. |
| se registra en | Atencion – RegistroEvolucion | 1 a 0..1 | La psicóloga registra la evolución de cada atención realizada. |

## Decisiones de modelado
- **Secretaria como rol, no como clase:** el negocio no registra información propia de la secretaria, por lo que no se modela como clase del dominio. En el proceso TO-BE sus tareas de coordinación (informar horarios, registrar horas y confirmar asistencia) pasan a ser realizadas por el paciente y por el sistema, por lo que tampoco aparece como actor en los casos de uso de esta entrega; solo se menciona en HU-10 para verificar que no puede acceder a la ficha clínica. Paciente y Psicologa sí son clases porque el negocio guarda datos propios de cada uno (RUT, contacto, emisión de boletas).
- **Adulto responsable como dato de la ficha:** la ficha de anamnesis registra al adulto responsable y a las personas que viven con el paciente. En esta entrega se guarda como atributo de FichaClinica (datosAdultoResponsable), ya que en el proceso TO-BE quien reserva y confirma es el Paciente.
- **Composición:** se usó solo entre FichaClinica y RegistroEvolucion, porque un registro de evolución no tiene sentido fuera de la ficha del paciente. No se usó agregación.
- **Herencia:** no se usó. La modalidad presencial u online no cambia los datos ni las reglas de la atención, por lo que se modela como atributo (modalidad, tipoAtencion).
- **Estados como atributos:** los estados de Reserva, Atencion, Pago y Boleta usan los mismos nombres que los criterios de aceptación (07) y que los diagramas de estado (11): EST-01 Reserva, EST-02 Pago y EST-03 Boleta.
- **Sistemas externos fuera del dominio:** el servicio de mensajería y el SII no son conceptos del negocio, sino sistemas con los que el sistema se integra. Aparecen como actores en los casos de uso (09) y como participantes en los diagramas de secuencia (10).
