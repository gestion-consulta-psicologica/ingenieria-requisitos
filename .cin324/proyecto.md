# Estado del proyecto — generación de la aplicación

## Proyecto
- Nombre: Gestión de consulta psicológica
- Repositorio de documentación: esta carpeta (`ingenieria-requisitos`)
- Última auditoría: 2026-11-18 — resultado: HU-03 migrada de mensajería simulada a correo real por SMTP con cola persistente, planificador y tokens de un solo uso; pendiente la validación del sistema por el estudiante

## Mapa de artefactos (rutas detectadas)
| Artefacto | Ruta(s) | Estado |
|-----------|---------|--------|
| BPMN AS-IS | `01-proceso-as-is.md`, `diagramas/as-is.png`, `diagramas/as-is.bpmn` | completo |
| BPMN TO-BE | `02-rediseno-to-be.md`, `diagramas/TO-BE.png`, `diagramas/TO-BE.bpmn` | completo (sin IDs ACT-TOBE); actividades de HU-02A y HU-03 agregadas al BPMN y PNG re-exportado |
| Historias de usuario | `04-historias-usuario.md` (HU-01 a HU-09 + HU-02A) | completo |
| Criterios Gherkin | `07-criterios-aceptacion.md` (HU-01 a HU-10 + HU-02A) | parcial: numeración desalineada desde HU-05 |
| Modelo de dominio | `08-modelo-dominio.md`, `diagramas/modelo-dominio.puml` | completo |
| Casos de uso | `09-casos-de-uso.md`, `diagramas/casos-de-uso.puml` | parcial: enlaces HU incorrectos en CU-06 a CU-10; CU-11 agregado al texto y al PUML el 2026-11-17 |
| Diagramas de estado | `11-diagramas-estado.md`, `diagramas/est-01/02/03.puml` | completo |
| Diagramas de secuencia | `10-diagramas-secuencia.md`, `diagramas/dss-01/02/03.puml` | completo |
| Requisitos y atributos de calidad | `03-requisitos.md`, `06-atributos-calidad.md` | completo |

## Supuestos acordados (por elementos faltantes o dudosos)
- Numeración de historias: la fuente de verdad es `04-historias-usuario.md` (HU-01 a HU-09). En `07-criterios-aceptacion.md` se renumerará desde HU-05 para que coincida; «Seleccionar una nueva hora» queda dentro de HU-04. Confirmado por el estudiante el 2026-11-11. No se corrige ahora; debe resolverse antes de implementar las historias afectadas.
- Los enlaces de CU-06 a CU-10 y la clase `CampoClinico` de `12-trazabilidad.md` se corregirán antes de implementar las historias afectadas.
- La tabla del TO-BE no tiene IDs `ACT-TOBE-xx`; la trazabilidad se hace por nombre de actividad.
- **HU-02 — aviso vs solicitud de confirmación:** HU-02 envía el **aviso de reserva registrada**; la solicitud de confirmación se envía la víspera y pertenece a HU-03 (EST-01). CA4 se mantiene sin cambios y se interpreta como aviso. Confirmado por el estudiante el 2026-11-17.
- **HU-02A — Registrar datos del paciente:** historia derivada de la validación de HU-02. HU-02 no crea al Paciente: lo busca por RUT; si no existe, deriva a `/pacientes/registro`. Se acordó implementar primero HU-02 y después HU-02A; HU-02A completa la derivación y el retorno a la reserva. Confirmado el 2026-11-17.
- **RP-21:** nuevo requisito funcional para el registro de datos del paciente, agregado a `03-requisitos.md` y a `12-trazabilidad.md`.
- **Diagramas de HU-02A:** la actividad «Registrar datos del paciente» se agregó a `diagramas/TO-BE.bpmn` y CU-11 a `diagramas/casos-de-uso.puml` el 2026-11-17; el `TO-BE.png` fue re-exportado en B6.
- **HU-03 — Confirmar o cancelar una hora:** confirmado el 2026-11-17 que cubre la solicitud y el recordatorio, la respuesta del paciente, la cancelación con liberación del bloque y el Cargo de $5.000 por no confirmar. Quedan fuera los pagos, el reagendamiento, la agenda de la psicóloga y la autenticación.
- **Correo real en HU-03 (2026-11-18):** se reemplazó `ServicioMensajeriaSimulado` y el panel de simulación por SMTP real, cola persistente `correo_pendiente`, planificador automático en `America/Santiago`, reintentos con backoff, recuperación tras reinicio y tokens de un solo uso hasheados para confirmar o cancelar desde el correo. La migración `005` agrega las tablas de soporte sin alterar las tablas de negocio. Las credenciales SMTP se leen del entorno y no se versionan.
- **Diagramas actualizados (2026-11-18):** `dss-01.puml`, `dss-03.puml`, `est-01.puml` y `casos-de-uso.puml` se reexportaron a PNG. `TO-BE.bpmn` actualizó los nombres de las actividades de correo, pero `TO-BE.png` queda pendiente de reexportar porque no hay herramienta BPMN disponible; no se editó la imagen a mano.
- **Horas de envío pendientes:** los requisitos no definen la hora exacta de la víspera ni del recordatorio. Se usan `09:00` y `08:00` como valores configurables iniciales (`CONFIRMACION_HORA_VISPERA` y `CONFIRMACION_HORA_RECORDATORIO`), pendientes de confirmación con el cliente.
- **Especificaciones e implementación de HU-03:** cambio `hu-03-confirmar-cancelar-hora` con `proposal.md`, `specs/confirmacion-asistencia/spec.md`, `design.md` y `tasks.md` actualizados al correo real. Pasan 72 pruebas en total, incluidas las de SMTP falso, cola, planificador, tokens, UI y migraciones. `data/app.db` permanece en la migración `004` y no fue modificada; la `005` se aplica al arrancar o en bases temporales. No archivar hasta que el estudiante valide el sistema.

## Limitaciones de seguridad del prototipo

El prototipo actual es una entrega académica y no implementa controles de seguridad para producción:

- **Sin autenticación ni autorización:** no existe inicio de sesión ni permisos por rol.
- **Acceso de demostración por identificadores secuenciales:** las reservas se consultan mediante rutas como `/reservas/{id}`, con IDs predecibles y sin verificación de pertenencia.
- **RUT expuesto en rutas y vistas:** el RUT aparece en formularios, redirecciones y parámetros, por ejemplo `/reservar/{bloque_id}?rut=...`.
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
- La migración `005` (`correo_pendiente`, `token_confirmacion`) se aplica al arrancar la aplicación o en bases temporales; no se aplicó a `data/app.db` durante esta etapa.
- No existe una copia de seguridad previa a `004`; no se ha creado ni se debe simular una.
- Los tests usan una base SQLite temporal aislada; `pytest` no debe modificar `data/app.db`.
- Cualquier migración futura requiere detener la aplicación y crear una copia consistente antes de aplicarla.

## Historias
| Historia | Estado | Cambio de OpenSpec | Fecha | Observaciones |
|----------|--------|--------------------|-------|----------------|
| HU-01 — Consultar disponibilidad | hecha | `hu-01-consultar-disponibilidad` (archivado) | 2026-11-12 | 15/15 tareas; 6 pruebas pasan; validada sin observaciones; `http://localhost:8000/disponibilidad` |
| HU-02 — Reservar una hora | hecha | `hu-02-reservar-hora` (archivado) | 2026-11-17 | 15/15 tareas; 13 pruebas de HU-02 y 19 en total pasan; validada sin observaciones; `http://localhost:8000/reservar/<bloque_id>` |
| HU-02A — Registrar datos del paciente | hecha | `hu-02a-registrar-paciente` (archivado) | 2026-11-17 | 17/17 tareas; 14 pruebas de HU-02A y 33 en total pasan; validada sin observaciones; `http://localhost:8000/pacientes/registro` |
| HU-03 — Confirmar o cancelar una hora | implementada con correo real, pendiente de validación del sistema | `hu-03-confirmar-cancelar-hora` | 2026-11-18 | 72 pruebas en total pasan; SMTP falso, cola, planificador, tokens y migraciones cubiertos; horas de envío configurables pendientes de confirmar; no archivar hasta la validación del estudiante |

## Validaciones
| Historia | Informe | Estado | Fecha |
|----------|---------|--------|-------|
| HU-01 — Consultar disponibilidad | Validación manual del estudiante | aprobada sin observaciones | 2026-11-12 |
| HU-02 — Reservar una hora | Validación manual del estudiante | aprobada sin observaciones | 2026-11-17 |
| HU-02A — Registrar datos del paciente | Ficha de validación | confirmada por el estudiante | 2026-11-17 |
| HU-02A — Registrar datos del paciente | Validación del sistema | aprobada sin observaciones | 2026-11-17 |
| HU-03 — Confirmar o cancelar una hora | Ficha de validación | confirmada por el estudiante | 2026-11-17 |
| HU-03 — Confirmar o cancelar una hora | `openspec validate` y revisión final | `openspec validate --strict` válido; 30/30 tareas completadas; `git diff --check` sin errores; pendiente la validación del sistema por el estudiante | 2026-11-18 |
| HU-03 — Confirmar o cancelar una hora | Pruebas y migraciones | 72 pruebas en total pasan; migraciones 003, 004 y 005 cubiertas; no hay datos ambiguos en la base local | 2026-11-18 |

## Cambios posteriores
| Cambio | Historia afectada | Motivo | Fecha |
|--------|-------------------|--------|-------|
| — | — | — | — |
