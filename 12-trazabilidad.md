# Trazabilidad

## Matriz de trazabilidad

| Requisito (Entrega 1) | Historia | Caso de uso | Secuencia | Estado | Clases del dominio |
|---|---|---|---|---|---|
| RP-01 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario, Psicologa |
| RP-02 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario |
| RP-03 | HU-02 | CU-02 | DSS-03 | EST-01 | Reserva, BloqueHorario, Paciente |
| RP-04 | HU-02 | CU-02 | DSS-03 | EST-01 | Reserva, BloqueHorario |
| RP-05 | HU-02, HU-03 | CU-02, CU-03 | DSS-01, DSS-03 | EST-01 | SolicitudConfirmacion, Reserva, CorreoPendiente, TokenConfirmacion |
| RP-06 | HU-03 | CU-03 | DSS-01 | EST-01 | Reserva, SolicitudConfirmacion, Cargo, CorreoPendiente, TokenConfirmacion |
| RP-07 | HU-04 | CU-04, CU-05 | DSS-04 | EST-01 | Reserva, BloqueHorario |
| RP-08 | HU-04 | CU-05 | DSS-04 | EST-01 | BloqueHorario |
| RP-09 | HU-04 | CU-05 | DSS-04 | EST-01 | BloqueHorario |
| RP-10 | HU-04 | CU-05 | DSS-04 | EST-01 | Reserva, BloqueHorario |
| RP-11 | HU-04 | CU-05 | DSS-04 | EST-01 | Reserva, SolicitudConfirmacion |
| RP-12 | HU-05 | CU-06 | DSS-05 | EST-02 | Pago, ComprobanteTransferencia, Atencion |
| RP-13 | HU-06 | CU-07 | — | EST-02 | Pago, ComprobanteTransferencia |
| RP-14 | HU-07 | CU-08 | DSS-02 | EST-03 | Boleta, Pago, Atencion, Psicologa, Paciente |
| RP-15 | HU-08 | CU-09 | — | EST-04 | Atencion, Paciente |
| RP-16 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Atencion |
| RP-17 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Paciente |
| RP-18 | HU-01 a HU-09 (incluye HU-02A y HU-05A) | CU-01 a CU-12 | — | — | — |
| RP-19 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario |
| RP-20 | HU-01 a HU-09 (incluye HU-02A y HU-05A) | CU-01 a CU-12 | — | — | — |
| RP-21 | HU-02A | CU-11 | — | — | Paciente |
| RP-22 | HU-03 | CU-03 | DSS-01 | EST-01 | Cargo, Reserva, Paciente |
| RP-23 | HU-05A | CU-12 | — | EST-02 | Atencion, Pago, ComprobanteTransferencia, Paciente |
| RP-24 | HU-08 | CU-09 | — | EST-04 | Cargo, Atencion, Paciente |
| RP-25 | HU-05A | CU-12 | — | EST-01, EST-02, EST-04 | Reserva, Atencion, Pago, Paciente |
| RP-26 | HU-04 | CU-04 | DSS-04 | EST-01 | Cargo, Reserva, Paciente |
| RD-01 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Paciente |
| RD-02 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion |

## Observaciones

- **RP-07 a RP-11 (cancelación y reagendamiento):** se representan en DSS-04 y en las transiciones de EST-01. El reagendamiento conserva el bloque anterior en el historial de cambios y reinicia el ciclo de solicitudes de confirmación sobre la misma reserva; la cancelación libera el bloque sin crear un nuevo ciclo.

- **RP-12 (comprobar pago):** cuenta con DSS-05 y con el ciclo de vida del pago (EST-02), que HU-05 consulta en modo de solo lectura. Las transiciones de EST-02 pertenecen a HU-06.

- **RP-13 (registrar estado de pago):** no cuenta con diagrama de secuencia propio; su comportamiento se representa en EST-02 y se implementará en HU-06.

- **RP-23 (registrar comprobante de pago):** corresponde a HU-05A y CU-12. No tiene diagrama de secuencia propio. La creación automática de la atención y su pago se detalla en RP-25.

- **RP-24 (cargo por inasistencia):** corresponde a HU-08 y CU-09. La inasistencia sin justificación genera un cargo real de $5.000 asociado a la atención y al paciente; la inasistencia justificada no genera cargo. Su ciclo de vida se representa en EST-04. El cargo no modifica automáticamente el estado del pago.

- **RP-25 (origen automático de atención y pago):** corresponde a HU-05A y CU-12. Sigue la transición de EST-01 «llega la hora de la atención / originar atención y pago / finalizar reserva» y la transición inicial de EST-02. La atención originada tiene un pago asociado en estado pendiente. El ciclo de vida de la atención se representa en EST-04 y el ciclo de vida del pago en EST-02.

- **RP-26 (cargo por cancelación de reserva):** corresponde a HU-04 y CU-04. Se representa en DSS-04 y en las transiciones de EST-01. Cuando el paciente confirma la cancelación se registra un cargo de $5.000 asociado al paciente y a la reserva. Las cancelaciones realizadas por la psicóloga no generan cargos.

- **RP-14 (emisión de boleta):** se encuentra relacionado con DSS-02 y EST-03, que representan la interacción para emitir la boleta y su ciclo de vida.

- **RP-15 (registro de asistencia):** su comportamiento corresponde al registro de asistencia de la atención y se encuentra descrito en HU-08 y CU-09. Su ciclo de vida se representa en EST-04. No cuenta con un diagrama de secuencia propio.

- **RP-16 y RP-17 (ficha clínica y confidencialidad):** se encuentran relacionados con HU-09 y CU-10. La protección de la información clínica se aborda mediante los criterios de aceptación de acceso autorizado y denegación de acceso no autorizado.

- **RP-18 y RP-20 (requisitos no funcionales):** son requisitos transversales que afectan a varias funcionalidades de la plataforma. Su cumplimiento debe verificarse mediante las métricas y pruebas de los atributos de calidad.

- **RP-19 (tiempo de respuesta):** se relaciona con la consulta de disponibilidad de horarios y su comportamiento se representa en DSS-03.

- **RP-05 y RP-06 (notificación y respuesta por correo):** el envío se realiza por SMTP mediante una cola persistente (`CorreoPendiente`) y los enlaces usan tokens de un solo uso (`TokenConfirmacion`). El planificador recupera envíos tras un reinicio y no marca como exitoso ningún correo que el servidor no haya aceptado. El servidor SMTP y su configuración son externos al dominio y no se versionan.

- **Requisito derivado RD-01:** complementa RP-17 mediante la restricción del acceso a información clínica según autenticación y permisos del usuario. Se relaciona con HU-09 y CU-10.

- **Requisito derivado RD-02:** complementa RP-17 mediante el cifrado de la información sensible almacenada en la plataforma. Se relaciona con HU-09 y CU-10.

- **Correspondencia CA ↔ escenario:** cada criterio de aceptación de `04-historias-usuario.md` se desarrolla en el escenario Gherkin correspondiente de `07-criterios-aceptacion.md`. Las secciones de HU-04, HU-05A y HU-08 incluyen la correspondencia explícita; ante una diferencia, prevalece `04-historias-usuario.md`.