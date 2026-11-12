# Estado del proyecto — generación de la aplicación

## Proyecto
- Nombre: Gestión de consulta psicológica
- Repositorio de documentación: esta carpeta (`ingenieria-requisitos`)
- Última auditoría: 2026-11-11 — resultado: con supuestos

## Mapa de artefactos (rutas detectadas)
| Artefacto | Ruta(s) | Estado |
|-----------|---------|--------|
| BPMN AS-IS | `01-proceso-as-is.md`, `diagramas/as-is.png`, `diagramas/as-is.bpmn` | completo |
| BPMN TO-BE | `02-rediseno-to-be.md`, `diagramas/TO-BE.png`, `diagramas/TO-BE.bpmn` | completo (sin IDs ACT-TOBE) |
| Historias de usuario | `04-historias-usuario.md` (HU-01 a HU-09) | completo |
| Criterios Gherkin | `07-criterios-aceptacion.md` (HU-01 a HU-10) | parcial: numeración desalineada desde HU-05 |
| Modelo de dominio | `08-modelo-dominio.md`, `diagramas/modelo-dominio.puml` | completo |
| Casos de uso | `09-casos-de-uso.md`, `diagramas/casos-de-uso.puml` | parcial: enlaces HU incorrectos en CU-06 a CU-10 |
| Diagramas de estado | `11-diagramas-estado.md`, `diagramas/est-01/02/03.puml` | completo |
| Diagramas de secuencia | `10-diagramas-secuencia.md`, `diagramas/dss-01/02/03.puml` | completo |
| Requisitos y atributos de calidad | `03-requisitos.md`, `06-atributos-calidad.md` | completo |

## Supuestos acordados (por elementos faltantes o dudosos)
- Numeración de historias: la fuente de verdad es `04-historias-usuario.md` (HU-01 a HU-09). En `07-criterios-aceptacion.md` se renumerará desde HU-05 para que coincida; «Seleccionar una nueva hora» queda dentro de HU-04. Confirmado por el estudiante el 2026-11-11. No se corrige ahora; debe resolverse antes de implementar las historias afectadas.
- Los enlaces de CU-06 a CU-10 y la clase `CampoClinico` de `12-trazabilidad.md` se corregirán antes de implementar las historias afectadas.
- La tabla del TO-BE no tiene IDs `ACT-TOBE-xx`; la trazabilidad se hace por nombre de actividad.

## Stack (se define una sola vez)
- Lenguaje y framework: Python 3.12 + FastAPI
- Base de datos: SQLite — archivo `data/app.db`
- Plantillas y formularios: Jinja2 + `python-multipart`
- Pruebas: pytest + `TestClient` de FastAPI
- Python instalado: `C:\Users\nicol\AppData\Local\Programs\Python\Python312` (usar `.venv\Scripts\python.exe`)
- Cómo instalar: `python -m venv .venv` → `.venv\Scripts\activate` → `pip install -r requirements.txt`
- Cómo ejecutar: `uvicorn app.main:app --reload` — URL: `http://localhost:8000`
- Cómo probar: `pytest`

## Historias
| Historia | Estado | Cambio de OpenSpec | Fecha | Observaciones |
|----------|--------|--------------------|-------|----------------|
| HU-01 — Consultar disponibilidad | hecha | `hu-01-consultar-disponibilidad` (archivado) | 2026-11-12 | 15/15 tareas; 6 pruebas pasan; validada sin observaciones; `http://localhost:8000/disponibilidad` |

## Validaciones
| Historia | Informe | Estado | Fecha |
|----------|---------|--------|-------|
| HU-01 — Consultar disponibilidad | Validación manual del estudiante | aprobada sin observaciones | 2026-11-12 |

## Cambios posteriores
| Cambio | Historia afectada | Motivo | Fecha |
|--------|-------------------|--------|-------|
| — | — | — | — |
