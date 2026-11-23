# Estado del proyecto — generación de la aplicación

## Proyecto
- Nombre: Gestión de consulta psicológica
- Repositorio de documentación: esta carpeta (`ingenieria-requisitos`)
- Última auditoría: 2026-11-23 — resultado: se aplicaron las 10 decisiones de alineación (HU-04, HU-05, HU-05A, HU-08, modelo de dominio, casos de uso, estados, trazabilidad y código); pendiente ejecutar la verificación final de pruebas y OpenSpec

## Mapa de artefactos (rutas detectadas)
| Artefacto | Ruta(s) | Estado |
|-----------|---------|--------|
| BPMN AS-IS | `01-proceso-as-is.md`, `diagramas/as-is.png`, `diagramas/as-is.bpmn` | completo |
| BPMN TO-BE | `02-rediseno-to-be.md`, `diagramas/TO-BE.png`, `diagramas/TO-BE.bpmn` | completo (sin IDs ACT-TOBE); el BPMN es la fuente de verdad y el PNG puede no reflejar los últimos cambios de actividades |
| Historias de usuario | `04-historias-usuario.md` (HU-01 a HU-09 + HU-02A + HU-05A) | completo |
| Criterios Gherkin | `07-criterios-aceptacion.md` (HU-01 a HU-09 + HU-02A + HU-05A) | completo |
| Modelo de dominio | `08-modelo-dominio.md`, `diagramas/modelo-dominio.puml` | completo |
| Casos de uso | `09-casos-de-uso.md`, `diagramas/casos-de-uso.puml` | completo: enlaces de CU-06 a CU-10 corregidos; CU-11 y CU-12 agregados al texto y al PUML |
| Diagramas de estado | `11-diagramas-estado.md`, `diagramas/est-01/02/03.puml` | completo |
| Diagramas de secuencia | `10-diagramas-secuencia.md`, `diagramas/dss-01/02/03/04/05.puml` | completo |
| Requisitos y atributos de calidad | `03-requisitos.md`, `06-atributos-calidad.md` | completo |

## Supuestos acordados (por elementos faltantes o dudosos)
- Numeración de historias: la fuente de verdad es `04-historias-usuario.md` (HU-01 a HU-09 + HU-02A + HU-05A). Resuelto el 2026-11-19 durante la validación de HU-05: las secciones de `07-criterios-aceptacion.md` coinciden con `04` y se corrigieron los enlaces de CU-06 a CU-10 en `09-casos-de-uso.md` y la referencia de DSS-02 (emitir boleta es HU-07). «Seleccionar una nueva hora» queda dentro de HU-04.
- La clase `CampoClinico` de `12-trazabilidad.md` se corrigió a `Cargo`/`Paciente` el 2026-11-23; los enlaces de CU-06 a CU-10 ya se corrigieron el 2026-11-19.
- La tabla del TO-BE no tiene IDs `ACT-TOBE-xx`; la trazabilidad se hace por nombre de actividad.
- **HU-02 — aviso vs solicitud de confirmación:** HU-02 envía el **aviso de reserva registrada**; la solicitud de confirmación se envía la víspera y pertenece a HU-03 (EST-01). CA4 se mantiene sin cambios y se interpreta como aviso. Confirmado por el estudiante el 2026-11-17.
- **HU-02A — Registrar datos del paciente:** historia derivada de la validación de HU-02. HU-02 no crea al Paciente: lo busca por RUT; si no existe, deriva a `/pacientes/registro`. Se acordó implementar primero HU-02 y después HU-02A; HU-02A completa la derivación y el retorno a la reserva. Confirmado el 2026-11-17.
- **RP-21:** nuevo requisito funcional para el registro de datos del paciente, agregado a `03-requisitos.md` y a `12-trazabilidad.md`.
- **Diagramas de HU-02A:** la actividad «Registrar datos del paciente» se agregó a `diagramas/TO-BE.bpmn` y CU-11 a `diagramas/casos-de-uso.puml` el 2026-11-17; el `TO-BE.png` fue re-exportado en B6.
- **HU-03 — Confirmar o cancelar una hora:** confirmado el 2026-11-17 que cubre la solicitud y el recordatorio, la respuesta del paciente, la cancelación con liberación del bloque y el Cargo de $5.000 por no confirmar. Quedan fuera los pagos, el reagendamiento, la agenda de la psicóloga y la autenticación.
- **Correo real en HU-03 (2026-11-18):** se reemplazó `ServicioMensajeriaSimulado` y el panel de simulación por SMTP real, cola persistente `correo_pendiente`, planificador automático en `America/Santiago`, reintentos con backoff, recuperación tras reinicio y tokens de un solo uso hasheados para confirmar o cancelar desde el correo. La migración `005` agrega las tablas de soporte sin alterar las tablas de negocio. Las credenciales SMTP se leen del entorno y no se versionan.
- **Diagramas actualizados (2026-11-18):** `dss-01.puml`, `dss-03.puml`, `est-01.puml` y `casos-de-uso.puml` se reexportaron a PNG. `TO-BE.bpmn` actualizó los nombres de las actividades de correo, pero `TO-BE.png` no se pudo reexportar porque no hay herramienta BPMN disponible; el BPMN es la fuente de verdad y no se editó la imagen a mano.
- **Horas de envío pendientes:** los requisitos no definen la hora exacta de la víspera ni del recordatorio. Se usan `09:00` y `08:00` como valores configurables iniciales (`CONFIRMACION_HORA_VISPERA` y `CONFIRMACION_HORA_RECORDATORIO`), pendientes de confirmación con el cliente.
- **Especificaciones e implementación de HU-03:** cambio `hu-03-confirmar-cancelar-hora` con `proposal.md`, `specs/confirmacion-asistencia/spec.md`, `design.md` y `tasks.md` actualizados al correo real. Pasan 72 pruebas en total, incluidas las de SMTP falso, cola, planificador, tokens, UI y migraciones. `data/app.db` permanece en la migración `004` y no fue modificada; la `005` se aplica al arrancar o en bases temporales. No archivar hasta que el estudiante valide el sistema.
- **HU-05 — Comprobar el pago (2026-11-19):** ficha `.cin324/historias/HU-05.md` confirmada. HU-05 es de solo lectura; las transiciones de EST-02 pertenecen a HU-06. Se agregó **CA4** (listado de atenciones con pago pendiente) a `04-historias-usuario.md`; se corrigieron los enlaces de CU-06 a CU-10 en `09-casos-de-uso.md` y la referencia de DSS-02 (emitir boleta es HU-07); se creó **DSS-05** (`diagramas/dss-05.puml/.png`). La opción «Registrar estado de pago» queda visible e inactiva hasta HU-06. Se muestran el nombre y el RUT del paciente. Acceso como rol Psicóloga sin autenticación.
- **HU-05A — Registrar la atención y el comprobante de pago (2026-11-19):** historia derivada de la validación de HU-05 para cubrir la creación automática de la atención y el registro del comprobante de transferencia. Se agregó a `04-historias-usuario.md`, `07-criterios-aceptacion.md`, `03-requisitos.md` (**RP-23**), `09-casos-de-uso.md` (**CU-12**) y `12-trazabilidad.md`. La actividad TO-BE es **Realizar pago**, ya existente en el BPMN; la creación automática de la atención y su pago sigue la transición de EST-01. Ficha `.cin324/historias/HU-05A.md` confirmada el 2026-11-19. El monto de $30.000 es un ejemplo configurable, el disparo es automático e idempotente y el acceso del paciente es desde el detalle de la reserva. Debe implementarse después de HU-05.
- **HU-05A implementada (2026-11-20):** cambio `hu-05a-registrar-atencion-comprobante` con 17/17 tareas. Se agregó `app/servicios/atenciones.py`, la integración al ciclo del planificador, `GET/POST /pagos/{atencion_id}/comprobante`, la plantilla `pago_comprobante.html` y el enlace en `reserva_confirmada.html`. El monto se configura con `MONTO_ATENCION_CLP` (30000 por defecto). La migración `008` reconstruye `reserva` para permitir el estado `Finalizada`. Pasan 115 pruebas; no archivar hasta que el estudiante valide el sistema.
- **Alineación por auditoría (2026-11-23):** HU-05A queda dentro del alcance; la Reserva pasa a `Finalizada` al originarse la atención; `Paciente–FichaClinica` es `1 a 0..1`; `Atencion–Pago` es `1 a 1` y «atención sin pago» se lee como «pago pendiente sin comprobante»; el cargo de $5.000 por inasistencia sin justificación es real; todos los pagos van a la cuenta de la psicóloga; no hay tarifa por tipo de atención; CU-03 cubre ambas respuestas y CU-04 es cancelación independiente sin `extend`; `04-historias-usuario.md` es la fuente de verdad de los CA y `07-criterios-aceptacion.md` los deriva con trazabilidad explícita.

## Limitaciones de seguridad del prototipo

El prototipo actual es una entrega académica y no implementa controles de seguridad para producción:

- **Sin autenticación ni autorización:** no existe inicio de sesión ni permisos por rol.
- **Acceso de demostración por identificadores secuenciales:** las reservas y los pagos se consultan mediante rutas como `/reservas/{id}` y `/pagos/{id}`, con IDs predecibles y sin verificación de pertenencia.
- **RUT expuesto en rutas y vistas:** el RUT aparece en formularios, redirecciones, parámetros y pantallas de pago, por ejemplo `/reservar/{bloque_id}?rut=...` o `/pagos/{atencion_id}`.
- **Formularios POST sin protección CSRF:** las operaciones de reserva, registro y confirmación no incluyen token CSRF.
- **Tokens en la URL del correo:** los enlaces viajan en la URL; la base guarda solo su hash y son de un solo uso, pero el correo puede reenviarse.
- **Credenciales SMTP en el entorno:** no se versionan, pero el prototipo no implementa gestión de secretos ni rotación.
- **Planificador en el proceso web:** corre dentro de la aplicación; en producción conviene separarlo en un worker y usar un bloqueo distribuido.
- **Datos personales en correos:** los mensajes incluyen nombre, fecha, hora y número de reserva; no incluyen información clínica.

Relación con los requisitos:

- **RP-17:** la confidencialidad de la información personal, administrativa y clínica no está garantizada por controles técnicos en este prototipo.
- **RD-01:** la autenticación y los permisos por rol no están implementados.
- **RD-02:** el cifrado de la información sensible almacenada no está implementado.

Estas limitaciones son propias del prototipo académico actual. No debe utilizarse con información clínica o personal real en un entorno de producción. Antes de producción se requiere implementar autenticación, autorización por roles, protección CSRF, protección de datos personales y controles de acceso adecuados. La documentación de estas limitaciones no implica que RP-17, RD-01 o RD-02 estén implementados.

## Stack (se define una sola vez)
- Lenguaje y framework: Python 3.12 + FastAPI
- Base de datos: SQLite — archivo `data/app.db`
- Plantillas y formularios: Jinja2 + `python-multipart`
- Pruebas: pytest + `TestClient` de FastAPI
- Python instalado: `C:\Users\nicol\AppData\Local\Programs\Python\Python312` (usar `.venv\Scripts\python.exe`)
- Cómo instalar: `python -m venv .venv` → `.venv\Scripts\activate` → `pip install -r requirements.txt`
- Cómo ejecutar: `uvicorn app.asgi:app --reload` — URL: `http://localhost:8000`
- Cómo probar: `pytest`

## Base de datos y respaldo
- `data/app.db` está actualmente en la migración `004`; su hash SHA-256 se verificó como `97E01B0E05CA75E8C42D62755D32779AA36D304A6B980CC47DA5AD83A3E60B29` al cerrar esta etapa.
- Las migraciones `005` (`correo_pendiente`, `token_confirmacion`), `006` (`reserva.version`, `reserva_historial`), `007` (`atencion`, `pago`, `comprobante_transferencia`) y `008` (`reserva` con estado `Finalizada`) se aplican al arrancar la aplicación o en bases temporales; no se aplicaron a `data/app.db` durante esta etapa. La `008` se verificó sobre una copia de `data/app.db` en `004`: aplica sin errores y conserva los datos.
- No existe una copia de seguridad previa a `004`; no se ha creado ni se debe simular una.
- Los tests usan una base SQLite temporal aislada; `pytest` no debe modificar `data/app.db`.
- Cualquier migración futura requiere detener la aplicación y crear una copia consistente antes de aplicarla.

## Historias
| Historia | Estado | Cambio de OpenSpec | Fecha | Observaciones |
|----------|--------|--------------------|-------|----------------|
| HU-01 — Consultar disponibilidad | hecha | `hu-01-consultar-disponibilidad` (archivado) | 2026-11-12 | 15/15 tareas; 6 pruebas pasan; validada sin observaciones; `http://localhost:8000/disponibilidad` |
| HU-02 — Reservar una hora | hecha | `hu-02-reservar-hora` (archivado) | 2026-11-17 | 15/15 tareas; 13 pruebas de HU-02 y 19 en total pasan; validada sin observaciones; `http://localhost:8000/reservar/<bloque_id>` |
| HU-02A — Registrar datos del paciente | hecha | `hu-02a-registrar-paciente` (archivado) | 2026-11-17 | 17/17 tareas; 14 pruebas de HU-02A y 33 en total pasan; validada sin observaciones; `http://localhost:8000/pacientes/registro` |
| HU-03 — Confirmar o cancelar una hora | implementada con correo real, pendiente de validación del sistema | `hu-03-confirmar-cancelar-hora` | 2026-11-18 | 37/37 tareas; 72 pruebas en total pasan; SMTP falso, cola, planificador, tokens y migraciones cubiertos; horas de envío configurables pendientes de confirmar; no archivar hasta la validación del estudiante |
| HU-04 — Reagendar o cancelar una hora | implementada, pendiente de validación del sistema | `hu-04-reagendar-cancelar-hora` | 2026-11-23 | 24/24 tareas; `openspec validate --strict` válido; `git diff --check` sin errores; 115 pruebas pasan; 14 días, estado `Pendiente de confirmación`, historial y correo alineados |
| HU-05 — Comprobar el pago | implementada, pendiente de validación del sistema | `hu-05-comprobar-pago` | 2026-11-19 | 8/8 tareas; 11 pruebas de HU-05 y 93 en total pasan; migración `007`; `/pagos` y `/pagos/{atencion_id}`; solo lectura; opción de registrar estado visible e inactiva hasta HU-06 |
| HU-05A — Registrar la atención y el comprobante de pago | implementada, pendiente de validación del sistema | `hu-05a-registrar-atencion-comprobante` | 2026-11-20 | 17/17 tareas; 22 pruebas de HU-05A y 115 en total pasan; creación automática e idempotente de atención/pago; reserva a `Finalizada`; `/pagos/{atencion_id}/comprobante`; monto configurable con `MONTO_ATENCION_CLP`; no modifica `data/app.db` |

## Validaciones
| Historia | Informe | Estado | Fecha |
|----------|---------|--------|-------|
| HU-01 — Consultar disponibilidad | Validación manual del estudiante | aprobada sin observaciones | 2026-11-12 |
| HU-02 — Reservar una hora | Validación manual del estudiante | aprobada sin observaciones | 2026-11-17 |
| HU-02A — Registrar datos del paciente | Ficha de validación | confirmada por el estudiante | 2026-11-17 |
| HU-02A — Registrar datos del paciente | Validación del sistema | aprobada sin observaciones | 2026-11-17 |
| HU-03 — Confirmar o cancelar una hora | Ficha de validación | confirmada por el estudiante | 2026-11-17 |
| HU-05 — Comprobar el pago | Ficha de validación | confirmada por el estudiante | 2026-11-19 |
| HU-05A — Registrar la atención y el comprobante de pago | Ficha de validación | confirmada por el estudiante | 2026-11-19 |
| HU-05 — Comprobar el pago | OpenSpec y pruebas | `openspec validate` válido; 8/8 tareas completadas; 11 pruebas de HU-05 y 93 en total pasan | 2026-11-19 |
| HU-05A — Registrar la atención y el comprobante de pago | OpenSpec, pruebas y smoke | `openspec validate` da el cambio por válido; 17/17 tareas; 22 pruebas de HU-05A y 115 en total pasan; smoke con planificador activo verificado | 2026-11-20 |
| HU-03 — Confirmar o cancelar una hora | `openspec validate` y revisión final | `openspec validate --strict` válido; 37/37 tareas completadas; `git diff --check` sin errores; pendiente la validación del sistema por el estudiante | 2026-11-18 |
| HU-04 — Reagendar o cancelar una hora | OpenSpec, pruebas y revisión final | `openspec validate --strict` válido; 24/24 tareas; `git diff --check` sin errores; 115 pruebas pasan; `data/app.db` conserva su hash y la migración `008` se probó sobre una copia | 2026-11-23 |
| HU-03 — Confirmar o cancelar una hora | Pruebas y migraciones | 72 pruebas en total pasan; migraciones 003, 004 y 005 cubiertas; no hay datos ambiguos en la base local | 2026-11-18 |

## Cambios posteriores
| Cambio | Historia afectada | Motivo | Fecha |
|--------|-------------------|--------|-------|
| Alineación de HU-04, HU-05, HU-05A, HU-08, modelo, CU y estados | HU-04, HU-05, HU-05A, HU-08 | Aplicar las 10 decisiones de la auditoría y eliminar contradicciones | 2026-11-23 |
