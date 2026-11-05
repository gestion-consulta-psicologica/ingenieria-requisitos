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
| RP-08 | HU-04 | CU-05 | — | — | BloqueHorario |
| RP-09 | HU-04 | CU-05 | — | — | BloqueHorario |
| RP-10 | HU-04 | CU-05 | — | EST-01 | Reserva, BloqueHorario |
| RP-11 | HU-05 | CU-06 | — | EST-01 | Reserva, SolicitudConfirmacion |
| RP-12 | HU-06 | CU-07 | — | EST-02 | Pago, ComprobanteTransferencia, Atención |
| RP-13 | HU-07 | CU-08 | — | EST-02 | Pago, ComprobanteTransferencia |
| RP-14 | HU-08 | CU-09 | DSS-02 | EST-02, EST-03 | Boleta, Pago, Atención, Psicóloga, Paciente |
| RP-15 | HU-08 | CU-09 | — | — | Atención, CampoClinico |
| RP-16 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Atención |
| RP-17 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Paciente |
| RP-18 | HU-01 a HU-05 | CU-01 a CU-05 | — | — | — |
| RP-19 | HU-01 | CU-01 | DSS-03 | — | BloqueHorario |
| RP-20 | HU-01 a HU-05 | CU-01 a CU-05 | — | — | — |

## Observaciones
- **RP-07 a RP-11 (reagendamiento y cancelación):** no tienen diagrama de secuencia propio porque no se integran con un sistema externo distinto al ya representado. Su comportamiento queda descrito en EST-01 (transiciones "paciente cancela la hora" y "paciente reagenda") y en los criterios de aceptación de HU-04 y HU-05.
- **RP-12 y RP-13 (comprobación y registro de pago):** no tienen diagrama de secuencia porque la verificación la hace la psicóloga dentro del sistema, sin integración con otro sistema. Su ciclo de vida queda descrito en EST-02.
- **RP-15 (asistencia e inasistencia):** no tiene diagrama de secuencia ni de estado propio. Los estados de Atencion (realizada, inasistencia, inasistencia justificada) quedan definidos en el modelo de dominio y en los criterios de aceptación de HU-09.
- **RP-16 y RP-17 (ficha clínica y confidencialidad):** no tienen diagrama de secuencia ni de estado porque la ficha clínica no tiene un ciclo de vida con estados relevantes; RP-17 se verifica con el escenario "La secretaria intenta acceder a una ficha clínica" de HU-10.
- **RP-18, RP-19 y RP-20 (requisitos no funcionales):** se asocian a las historias del paciente donde aplican, pero no se representan en diagramas de comportamiento. Se verifican con las métricas de 06-atributos-calidad.md (capacidad de interacción y eficiencia de desempeño).
- **Requisito derivado de la Entrega 1 (restringir el acceso a la información clínica según el rol):** se cubre con HU-10 y CU-10, al igual que su requisito origen RP-17.
- **DSS-03** combina CU-02 y CU-01 (relación include), por eso aparece asociado a RP-01, RP-02, RP-03, RP-04 y RP-19.
