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
| RP-13 | HU-06 | CU-07, CU-12 | — | EST-02 | Pago, Cargo, ComprobanteTransferencia |
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
| RP-26 | HU-03, HU-04 | CU-03, CU-04 | DSS-01, DSS-04 | EST-01 | Cargo, Reserva, Paciente |
| RD-01 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion, Paciente |
| RD-02 | HU-09 | CU-10 | — | — | FichaClinica, RegistroEvolucion |

## Cierre académico por historia

El alcance es la demostración con datos sintéticos y los roles Paciente y Psicóloga (Administradora). Hay **10 historias verificadas en demostración y una diferida**. Los **53 criterios cumplidos de 57** se respaldan en las pruebas existentes y sus corridas registradas. El estado de demostración no certifica preparación para operar con datos reales.

| Historia | Funcionalidad disponible | CA cumplidos |
|---|---|---:|
| HU-01 | Consultar disponibilidad y próxima fecha. | 5/5 |
| HU-02 | Seleccionar y reservar un bloque, con aviso y manejo de conflictos. | 6/6 |
| HU-02A | Registrar al paciente y retomar la reserva. | 4/4 |
| HU-03 | Confirmar o cancelar por web o enlace tras el envío; cerrar el plazo y cobrar solo cuando corresponde. | 7/7 |
| HU-04 | Cancelar o reagendar, con historial y nuevo ciclo de confirmación. | 8/8 |
| HU-05 | Consultar pagos pendientes, comprobantes y acceso al registro de estado. | 4/4 |
| HU-05A | Originar atención y pago y registrar comprobantes. | 6/6 |
| HU-06 | Seleccionar y guardar el estado de pago conforme a EST-02. | 4/4 |
| HU-07 | Emisión de boletas diferida por alcance hasta definir la integración externa. | 0/4 |
| HU-08 | Registrar asistencia y aplicar el cargo por inasistencia injustificada. | 5/5 |
| HU-09 | Consultar anamnesis, actualizar antecedentes y conservar evoluciones con autorización y bitácora. | 4/4 |

## Matriz final de aceptación

La numeración corresponde a las [historias oficiales](./04-historias-usuario.md). La [matriz de requisitos y casos de uso](#matriz-de-trazabilidad) enlaza cada historia con sus modelos y diagramas. La evidencia de los dos bloques de cierre aparece debajo.

| Criterio | Comportamiento | Estado en demostración | Evidencia o especificación |
|---|---|---|---|
| HU-01 CA1 | Acceso a la consulta | Cumplido | [Disponibilidad](./tests/test_hu01_disponibilidad.py) |
| HU-01 CA2 | Visualización de horarios disponibles | Cumplido | [Disponibilidad](./tests/test_hu01_disponibilidad.py) |
| HU-01 CA3 | Correspondencia de la información | Cumplido | [Disponibilidad](./tests/test_hu01_disponibilidad.py) |
| HU-01 CA4 | Ausencia de disponibilidad | Cumplido | [Disponibilidad](./tests/test_hu01_disponibilidad.py) |
| HU-01 CA5 | Próximo bloque disponible | Cumplido | [Disponibilidad](./tests/test_hu01_disponibilidad.py) |
| HU-02 CA1 | Selección de horario | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02 CA2 | Registro de la reserva | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02 CA3 | Actualización de disponibilidad | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02 CA4 | Solicitud de confirmación | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02 CA5 | Horario reservado por otro paciente | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02 CA6 | Paciente no registrado | Cumplido | [Reserva](./tests/test_hu02_reserva.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-02A CA1 | Registro del paciente | Cumplido | [Alta de pacientes](./tests/test_hu02a_registro_paciente.py) |
| HU-02A CA2 | Datos obligatorios | Cumplido | [Alta de pacientes](./tests/test_hu02a_registro_paciente.py) |
| HU-02A CA3 | RUT ya registrado | Cumplido | [Alta de pacientes](./tests/test_hu02a_registro_paciente.py) |
| HU-02A CA4 | Continuidad de la reserva | Cumplido | [Alta de pacientes](./tests/test_hu02a_registro_paciente.py) |
| HU-03 CA1 | Selección de respuesta | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA2 | Registro de respuesta | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA3 | Mantener la hora | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA4 | No mantener la hora | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA5 | Respuesta sin solicitud pendiente | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA6 | Sin respuesta | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-03 CA7 | Reemplazo de la solicitud anterior | Cumplido | [Confirmación](./tests/test_hu03_confirmacion.py) · [SMTP local](./tests/test_hu03_correo.py) |
| HU-04 CA1 | Selección de acción | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA2 | Cancelación de reserva | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA3 | Consulta de disponibilidad | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA4 | Visualización de alternativas | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA5 | Selección del nuevo horario | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA6 | Actualización de la reserva | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA7 | Nuevo horario no disponible | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-04 CA8 | Sin horarios disponibles | Cumplido | [Reagendamiento](./tests/test_hu04_reagendamiento.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05 CA1 | Consulta de información de pago | Cumplido | [Consulta de pagos](./tests/test_hu05_comprobar_pago.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05 CA2 | Consulta de antecedentes del pago | Cumplido | [Consulta de pagos](./tests/test_hu05_comprobar_pago.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05 CA3 | Resultado de la comprobación | Cumplido | [Consulta de pagos](./tests/test_hu05_comprobar_pago.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05 CA4 | Listado de atenciones con pago pendiente | Cumplido | [Consulta de pagos](./tests/test_hu05_comprobar_pago.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA1 | Origen automático de la atención | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA2 | Registro del comprobante | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA3 | Datos obligatorios del comprobante | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA4 | Varios comprobantes | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA5 | Comprobante disponible para la comprobación | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-05A CA6 | Reserva finalizada | Cumplido | [Atenciones y comprobantes](./tests/test_hu05a_atencion_comprobante.py) · [Recorrido](./tests/test_recorrido_integrado.py) |
| HU-06 CA1 | Registro del estado de pago | Cumplido | [Verificación de pagos](./tests/test_recorrido_integrado.py) |
| HU-06 CA2 | Asociación con el paciente | Cumplido | [Verificación de pagos](./tests/test_recorrido_integrado.py) |
| HU-06 CA3 | Asociación con la atención | Cumplido | [Verificación de pagos](./tests/test_recorrido_integrado.py) |
| HU-06 CA4 | Confirmación del registro | Cumplido | [Verificación de pagos](./tests/test_recorrido_integrado.py) |
| HU-07 CA1 | Inicio de emisión | Pendiente de integración externa | [Escenarios y condiciones](./07-criterios-aceptacion.md#hu-07--emitir-boleta) · [Diseño de emisión](./10-diagramas-secuencia.md#dss-02--emitir-boleta-de-honorarios) |
| HU-07 CA2 | Asociación con la atención | Pendiente de integración externa | [Escenarios y condiciones](./07-criterios-aceptacion.md#hu-07--emitir-boleta) · [Diseño de emisión](./10-diagramas-secuencia.md#dss-02--emitir-boleta-de-honorarios) |
| HU-07 CA3 | Resultado de emisión | Pendiente de integración externa | [Escenarios y condiciones](./07-criterios-aceptacion.md#hu-07--emitir-boleta) · [Diseño de emisión](./10-diagramas-secuencia.md#dss-02--emitir-boleta-de-honorarios) |
| HU-07 CA4 | Información insuficiente | Pendiente de integración externa | [Escenarios y condiciones](./07-criterios-aceptacion.md#hu-07--emitir-boleta) · [Diseño de emisión](./10-diagramas-secuencia.md#dss-02--emitir-boleta-de-honorarios) |
| HU-08 CA1 | Registro de asistencia | Cumplido | [Registro de asistencia](./tests/test_recorrido_integrado.py) |
| HU-08 CA2 | Asociación del registro | Cumplido | [Registro de asistencia](./tests/test_recorrido_integrado.py) |
| HU-08 CA3 | Consulta posterior | Cumplido | [Registro de asistencia](./tests/test_recorrido_integrado.py) |
| HU-08 CA4 | Inasistencia sin justificación | Cumplido | [Registro de asistencia](./tests/test_recorrido_integrado.py) |
| HU-08 CA5 | Inasistencia justificada | Cumplido | [Registro de asistencia](./tests/test_recorrido_integrado.py) |
| HU-09 CA1 | Acceso a la ficha clínica | Cumplido | [Ficha clínica y permisos](./tests/test_hu09_ficha_clinica.py) |
| HU-09 CA2 | Actualización de información clínica | Cumplido | [Ficha clínica y permisos](./tests/test_hu09_ficha_clinica.py) |
| HU-09 CA3 | Persistencia de los cambios | Cumplido | [Ficha clínica y permisos](./tests/test_hu09_ficha_clinica.py) |
| HU-09 CA4 | Acceso no autorizado | Cumplido | [Ficha clínica y permisos](./tests/test_hu09_ficha_clinica.py) |

## Pruebas y resultados registrados

| Corrida | Resultado | Alcance |
|---|---:|---|
| Suite completa histórica | 133 aprobadas | Punto de control anterior a la implementación de HU-09. |
| Incorporación de HU-09 | 9 aprobadas | Ficha clínica y recorrido integrado. |
| Primer bloque de cierre | 47 aprobadas | Reagendamiento, planificador, pago y asistencia. |
| Segundo bloque de cierre, grupo 1 | 58 aprobadas | Confirmación, SMTP local, reagendamiento, persistencia y recorrido. |
| Segundo bloque de cierre, grupo 2 | 21 aprobadas | Pagos, ficha clínica y recorrido. |
| Revisión final dirigida | 10 aprobadas | Arranque con base nueva, recorrido integrado y ficha clínica. |

Los grupos comparten pruebas. Los resultados históricos no se suman ni representan una ejecución completa del estado final. Las pruebas usan SQLite temporal; las de correo emplean SMTP local o un doble del servicio. El [README](./README.md#instalación-y-arranque-para-la-evaluación) indica cómo reproducir la demostración y las pruebas dirigidas.

## Evidencia de cierre de criterios

| Historia y criterio | Requisito | Estado en demostración | Prueba y evidencia |
|---|---|---|---|
| HU-04 CA7 | RP-08 a RP-11 | Cumplido | [Pruebas HTTP de reagendamiento](./tests/test_hu04_reagendamiento.py). El POST con un bloque ocupado devuelve 409 y el mensaje de conflicto, y conserva la reserva y su historial. |
| HU-04 CA8 | RP-08, RP-09 | Cumplido | [Pruebas HTTP de reagendamiento](./tests/test_hu04_reagendamiento.py). El GET sin alternativas informa que no hay horarios en los próximos 14 días y conserva la reserva original. |
| HU-05A CA6 | RP-25 | Cumplido | [Pruebas del planificador y las rutas](./tests/test_hu05a_atencion_comprobante.py). El planificador finaliza la reserva y las rutas de cancelación y reagendamiento rechazan la gestión con 409 sin generar historial ni cargo. |
| HU-06 CA2 | RP-13 | Cumplido | [Prueba de verificación de pagos](./tests/test_recorrido_integrado.py). La vista y la base identifican al mismo paciente al verificar el pago. El estado y monto del otro paciente permanecen intactos. |
| HU-08 CA1 | RP-15 | Cumplido | [Prueba de asistencia](./tests/test_recorrido_integrado.py). El panel confirma el guardado para la atención y muestra el nombre del paciente y el resultado en los tres escenarios. |
| HU-08 CA2 | RP-15 | Cumplido | [Prueba de asistencia](./tests/test_recorrido_integrado.py). Se verifica el RUT asociado a la atención registrada y que la atención del segundo paciente sigue programada. |
| HU-03 CA1 | RP-06 | Cumplido | [Pruebas de confirmación](./tests/test_hu03_confirmacion.py). El correo pendiente no habilita las acciones, el POST directo y el enlace se rechazan, y las acciones web aparecen tras el envío. |
| HU-03 CA6 | RP-22 | Cumplido | [Pruebas del planificador](./tests/test_hu03_confirmacion.py). Una solicitud enviada del ciclo vigente habilita el cargo. Correo pendiente, fallido u omitido: el ciclo cierra sin cargo ni aviso de cargo. |
| HU-06 CA1 | RP-13 | Cumplido | [Prueba de verificación de pagos](./tests/test_recorrido_integrado.py). Se seleccionan y guardan ambos estados de EST-02. La elección incompatible devuelve 409 y conserva el comprobante sin verificar. |
| HU-09 CA1 | RP-16, RD-01 | Cumplido | [Prueba de ficha clínica](./tests/test_hu09_ficha_clinica.py). La psicóloga autenticada consulta la anamnesis y las evoluciones del paciente correcto. |
| HU-09 CA2 | RP-16 | Cumplido | [Prueba de ficha clínica](./tests/test_hu09_ficha_clinica.py). Se verifican la edición de antecedentes, la confirmación de guardado y el registro de nuevas evoluciones. |
| HU-09 CA3 | RP-16 | Cumplido | [Prueba de ficha clínica](./tests/test_hu09_ficha_clinica.py). Dos atenciones del mismo paciente conservan sus evoluciones al volver a consultar la ficha y verificar SQLite. |

## Observaciones

- **HU-09 / CU-10:** RP-16 corresponde a CA1–CA3 y a la consulta y guardado de evoluciones en `app/rutas/clinica.py`. RP-17 y RD-01 se verifican en alcance de demostración mediante CA4 en `tests/test_hu09_ficha_clinica.py`: un paciente autenticado recibe 403 en lectura y escritura y ambas denegaciones quedan registradas sin contenido clínico. RD-02 (cifrado de datos en reposo) se implementó el 2026-11-25 en `app/servicios/cifrado.py` y se verifica en `tests/test_hu09_ficha_clinica.py` (datos cifrados en SQLite, cifrado de datos antiguos al arrancar y rechazo de una clave distinta).

- **RP-07 a RP-11 (cancelación y reagendamiento):** se representan en DSS-04 y en las transiciones de EST-01. El reagendamiento conserva el bloque anterior en el historial de cambios y reinicia el ciclo de solicitudes de confirmación sobre la misma reserva; la cancelación libera el bloque sin crear un nuevo ciclo.

- **RP-12 (comprobar pago):** cuenta con DSS-05 y con el ciclo de vida del pago (EST-02), que HU-05 consulta en modo de solo lectura. Las transiciones de EST-02 pertenecen a HU-06.

- **RP-13 (registrar estado de pago):** se representa en EST-02 y se ejecuta en HU-06 desde el panel de demostración, al guardar la verificación de los comprobantes seleccionados.

- **RP-23 (registrar comprobante de pago):** corresponde a HU-05A y CU-12. No tiene diagrama de secuencia propio. La creación automática de la atención y su pago se detalla en RP-25.

- **RP-24 (cargo por inasistencia):** corresponde a HU-08 y CU-09. La inasistencia sin justificación genera un cargo real de $5.000 asociado a la atención y al paciente; la inasistencia justificada no genera cargo. Su ciclo de vida se representa en EST-04. El cargo no modifica automáticamente el estado del pago.

- **RP-25 (origen automático de atención y pago):** corresponde a HU-05A y CU-12. Sigue la transición de EST-01 «llega la hora de la atención / originar atención y pago / finalizar reserva» y la transición inicial de EST-02. La atención originada tiene un pago asociado en estado pendiente. El ciclo de vida de la atención se representa en EST-04 y el ciclo de vida del pago en EST-02.

- **RP-26 (cargo por cancelación de reserva):** corresponde a HU-03 CA4 y HU-04 CA2. Se representa en DSS-01, DSS-04 y EST-01. Cuando el paciente cancela con «No asistiré» o desde la gestión de la reserva, el sistema registra un cargo de $5.000 asociado al paciente y a la reserva. Las cancelaciones realizadas por la psicóloga no generan cargos.

- **RP-14 (emisión de boleta):** HU-07 queda pendiente de integración externa por alcance. DSS-02 y EST-03 documentan el diseño previsto. La entrega académica no emite boletas ni asigna folios.

- **RP-15 (registro de asistencia):** su comportamiento corresponde al registro de asistencia de la atención y se encuentra descrito en HU-08 y CU-09. Su ciclo de vida se representa en EST-04. No cuenta con un diagrama de secuencia propio.

- **RP-16 y RP-17 (ficha clínica y confidencialidad):** se encuentran relacionados con HU-09 y CU-10. La protección de la información clínica se aborda mediante los criterios de aceptación de acceso autorizado y denegación de acceso no autorizado.

- **RP-18 y RP-20 (requisitos no funcionales):** son requisitos transversales que afectan a varias funcionalidades de la plataforma. Su cumplimiento debe verificarse mediante las métricas y pruebas de los atributos de calidad.

- **RP-19 (tiempo de respuesta):** se relaciona con la consulta de disponibilidad de horarios y su comportamiento se representa en DSS-03.

- **RP-05 y RP-06 (notificación y respuesta por correo):** el envío se realiza por SMTP mediante una cola persistente (`CorreoPendiente`) y los enlaces usan tokens de un solo uso (`TokenConfirmacion`). El planificador recupera envíos tras un reinicio y no marca como exitoso ningún correo que el servidor no haya aceptado. El servidor SMTP y su configuración son externos al dominio y no se versionan.

- **Requisito derivado RD-01:** complementa RP-17 mediante la restricción del acceso a información clínica según autenticación y permisos del usuario. Se relaciona con HU-09 y CU-10.

- **Requisito derivado RD-02:** complementa RP-17 mediante el cifrado de la información sensible almacenada en la plataforma. Se relaciona con HU-09 y CU-10.

- **Correspondencia CA ↔ escenario:** cada criterio de aceptación de `04-historias-usuario.md` se desarrolla en el escenario Gherkin correspondiente de `07-criterios-aceptacion.md`. Las secciones de HU-04, HU-05A y HU-08 incluyen la correspondencia explícita; ante una diferencia, prevalece `04-historias-usuario.md`.


## Evaluación 3 — HU-10

| Requisito | Historia y criterios | Artefactos | Implementación y evidencia |
|---|---|---|---|
| RP-27 · Revisión y registro | HU-10 CA1–CA3 | CU-13, DSS-06 | Panel, directorio, agenda y bandeja. `test_flujo_web_desde_reserva_hasta_aceptacion_y_reinicio`, `test_respuesta_web_sin_transferencia[rechazo]`. |
| RP-27 · Transferencia e historial | HU-10 CA4–CA5 y CA8 | Modelo de dominio, EST-05, [OpenSpec](./openspec/specs/derivacion-psiquiatria/spec.md) | `responder_derivacion`, `listar_historial`, migración 021. Flujo web con reinicio y `test_migracion_preserva_cuentas_sesiones_tokens_y_datos`. |
| RP-27 y RD-01 · Restricciones | HU-10 CA6–CA7 | CU-13, DSS-06, EST-05 | Revalidación de destino, versión y estado, CSRF y bitácora. Casos de destino inválido, respuesta sin transferencia, acceso por rol y aceptaciones concurrentes. |

[Evidencia automatizada de HU-10](./tests/test_hu10_derivaciones.py). El cierre académico histórico de esta matriz corresponde al alcance previo a HU-10.
