# Trazabilidad

## Matriz de trazabilidad

| Requisito (Entrega 1) | Historia | Caso de uso | Secuencia | Estado | Clases del dominio |
|---|---|---|---|---|---|
| RP-01 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario, Psicóloga |
| RP-02 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario |
| RP-03 | HU-02 | CU-02 | DSS-03 | EST-01 | Reserva, BloqueHorario, Paciente |
| RP-04 | HU-02 | CU-02 | DSS-03 | EST-01 | Reserva, BloqueHorario |
| RP-05 | HU-03 | CU-03 | DSS-01 | EST-01 | SolicitudConfirmacion, Reserva |
| RP-06 | HU-03 | CU-03 | DSS-01 | EST-01 | Reserva, SolicitudConfirmacion, Cargo |
| RP-07 | HU-04 | CU-04, CU-05 | — | EST-01 | Reserva, BloqueHorario |
| RP-08 | HU-04 | CU-05 | — | EST-01 | BloqueHorario |
| RP-09 | HU-04 | CU-05 | — | EST-01 | BloqueHorario |
| RP-10 | HU-04 | CU-05 | — | EST-01 | Reserva, BloqueHorario |
| RP-11 | HU-04 | CU-05 | — | EST-01 | Reserva, SolicitudConfirmacion |
| RP-12 | HU-05 | CU-06 | — | EST-02 | Pago, ComprobanteTransferencia, Atención |
| RP-13 | HU-06 | CU-07 | — | EST-02 | Pago, ComprobanteTransferencia |
| RP-14 | HU-07 | CU-08 | DSS-02 | EST-03 | Boleta, Pago, Atención, Psicóloga, Paciente |
| RP-15 | HU-08 | CU-09 | — | — | Atención, CampoClinico |
| RP-16 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Atención |
| RP-17 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Paciente |
| RP-18 | HU-01 a HU-05 | CU-01 a CU-05 | — | — | — |
| RP-19 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario |
| RP-20 | HU-01 a HU-05 | CU-01 a CU-05 | — | — | — |

## Observaciones

- **RP-07 a RP-11 (cancelación y reagendamiento):** no cuentan con diagramas de secuencia específicos. Su comportamiento se encuentra representado mediante las transiciones del ciclo de vida de la reserva en EST-01 y los criterios de aceptación de HU-04.

- **RP-12 y RP-13 (gestión de pagos):** no cuentan con diagramas de secuencia propios. Su comportamiento se encuentra representado en el ciclo de vida del pago (EST-02).

- **RP-14 (emisión de boleta):** se encuentra relacionado con DSS-02 y EST-03, que representan la interacción para emitir la boleta y su ciclo de vida.

- **RP-15 (registro de asistencia):** su comportamiento corresponde al registro de asistencia de la atención y se encuentra descrito en HU-08 y CU-09. No cuenta con un diagrama de secuencia o estado específico.

- **RP-16 y RP-17 (ficha clínica y confidencialidad):** se encuentran relacionados con HU-09 y CU-10. La protección de la información clínica se aborda mediante los criterios de aceptación de acceso autorizado y denegación de acceso no autorizado.

- **RP-18 y RP-20 (requisitos no funcionales):** son requisitos transversales que afectan a varias funcionalidades de la plataforma. Su cumplimiento debe verificarse mediante las métricas y pruebas de los atributos de calidad.

- **RP-19 (tiempo de respuesta):** se relaciona con la consulta de disponibilidad de horarios y su comportamiento se representa en DSS-03.

- **Requisito derivado RD-01:** complementa RP-17 mediante la restricción del acceso a información clínica según autenticación y permisos del usuario.

- **Requisito derivado RD-02:** complementa RP-17 mediante el cifrado de la información sensible almacenada en la plataforma.
