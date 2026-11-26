# HU-02A — Registrar datos del paciente

**Estado:** implementada  ·  **Confirmada por el estudiante:** 2026-11-17 (consistencia revisada el 2026-11-17; correo obligatorio decidido el 2026-11-25)
**Fuente de la historia:** historia derivada, agregada a `04-historias-usuario.md` durante la validación de HU-02 · **Gherkin:** `07-criterios-aceptacion.md`

## Historia
Como paciente, quiero registrar mis datos personales en la plataforma, para poder reservar una hora de atención cuando aún no estoy registrado.

## Trazabilidad
- Actividad del TO-BE: **Registrar datos del paciente** (tipo: tarea de usuario con apoyo del sistema). Cambio respecto del AS-IS: reemplaza la entrega de datos por WhatsApp para que la secretaria los registre; el paciente los ingresa directamente en la plataforma.
- Caso de uso: **CU-11 — Registrar datos del paciente**. Actor principal: **Paciente**. Actores externos: **ninguno**.
- Relación: CU-11 **extiende** CU-02 (Reservar hora) cuando el RUT no está registrado.
- Requisitos que cubre: **RP-21**.
- Diagrama de secuencia: **reconstruido desde el Gherkin y CU-02** (supuesto); no existe un DSS propio.
- Diagrama de estado: **no aplica** (Paciente no tiene ciclo de vida modelado).

## Entidades del modelo de dominio
| Entidad | Operación en esta historia | Atributos usados | Asociaciones y multiplicidades |
|---------|----------------------------|------------------|--------------------------------|
| **Paciente** | Crea si el RUT no existe; reutiliza si ya existe | Obligatorios: nombreCompleto, rut y correo. Opcionales: telefono, fechaNacimiento, direccion, escolaridad, ocupacion | Paciente `1 – 0..*` Reserva; Paciente `1 – 0..1` FichaClinica |

El RUT identifica al Paciente y es único en el sistema. Los demás datos personales del modelo quedan opcionales en esta historia.

## Cambios de estado
No aplica: la clase Paciente no tiene diagrama de estado.

## Flujo de interacción
1. El Paciente, dentro del flujo de reserva de HU-02, ingresa su RUT.
2. El sistema verifica que el RUT no esté registrado.
3. El sistema muestra el formulario de registro: nombre completo, RUT, correo electrónico (obligatorio) y teléfono (opcional).
4. El Paciente completa los datos y guarda.
5. El sistema valida los datos obligatorios y que el RUT no exista ya.
6. Si todo es válido, el sistema registra al Paciente y confirma el registro.
7. Si el registro se inició desde HU-02, el sistema retoma la reserva del bloque horario seleccionado: redirige a `/reservar/<bloque_id>?rut=<rut>` con el RUT precargado para que el paciente confirme la reserva (no la crea automáticamente).
8. Si no viene `bloque_id`, el sistema muestra una confirmación de registro con un enlace a la disponibilidad.

**Variantes:**
- **Datos obligatorios incompletos:** no se registra al Paciente y se informa qué dato falta.
- **RUT ya registrado:** no se duplica al Paciente y se utiliza el registro existente (si vino de HU-02, se retoma la reserva con ese paciente, redirigiendo a `/reservar/<bloque_id>?rut=<rut>`).
- **Datos opcionales vacíos:** se aceptan.

## Sistemas externos
| Sistema | Mensajes | Comportamiento |
|---------|----------|----------------|
| Ninguno | — | — |

## Escenarios Gherkin (texto íntegro)
```gherkin
Característica: Registro de datos del paciente

  Escenario: Un paciente nuevo se registra desde la reserva
    Dado que el paciente ingresó un RUT que no está registrado
    Cuando ingresa su nombre completo, su RUT y su correo electrónico
    Y guarda sus datos
    Entonces el sistema registra al paciente
    Y retoma la reserva del bloque horario seleccionado

  Escenario: El paciente no completa los datos obligatorios
    Dado que el paciente está registrando sus datos
    Cuando intenta guardar sin nombre completo, RUT o correo electrónico
    Entonces el sistema no registra al paciente
    Y le informa qué dato falta

  Escenario: El RUT ya está registrado
    Dado que el paciente ingresa un RUT que ya existe en el sistema
    Cuando intenta registrar sus datos
    Entonces el sistema no duplica al paciente
    Y utiliza el registro existente
```

## Decisiones tomadas en la validación
- **Historia derivada:** se creó durante la validación de HU-02 (2026-11-17) porque el modelo de dominio exige un Paciente registrado para reservar y HU-02 no debe crearlo. Confirmado por el estudiante.
- **Datos obligatorios:** nombreCompleto, rut y correo. El teléfono y el resto de los atributos del Paciente quedan opcionales. Confirmado el 2026-11-17; el correo pasó a ser obligatorio el 2026-11-25 (ver decisión siguiente).
- **Secuencia de implementación:** primero HU-02 y después HU-02A. Al estar HU-02 ya construida, HU-02A implementa la página `/pacientes/registro` y el retorno a la reserva del bloque seleccionado. Confirmado el 2026-11-17.
- **Requisito y trazabilidad:** se agregó RP-21 a `03-requisitos.md` y su fila en `12-trazabilidad.md` (RP-21 → HU-02A → CU-11 → Paciente).
- **Retomar la reserva:** al registrarse correctamente, se redirige a `/reservar/<bloque_id>?rut=<rut>` con el RUT precargado; el paciente confirma la reserva y HU-02 la registra. Confirmado el 2026-11-17.
- **Medio de contacto:** originalmente se aceptaba registrarse solo con teléfono (migración `002` dejó `correo` opcional en la base). Confirmado el 2026-11-17.
- **Correo obligatorio (decidido por el estudiante el 2026-11-25):** la solicitud de confirmación de HU-03 solo llega por correo y la respuesta exige que ese correo se haya enviado; un paciente sin correo nunca podría confirmar su hora. Desde ahora la aplicación exige un correo con formato válido. La columna `correo` sigue admitiendo nulos para conservar los pacientes antiguos; no se crea migración.
- **RUT:** se normaliza (sin puntos ni guion, K mayúscula) y se exige único; no se valida dígito verificador. Confirmado el 2026-11-17.
- **Diagramas:** CU-11 se agregó a `diagramas/casos-de-uso.puml` y la actividad «Registrar datos del paciente» a `diagramas/TO-BE.bpmn` el 2026-11-17. El `TO-BE.png` debe re-exportarse desde el editor BPMN.

## Supuestos
- El Paciente puede registrarse sin autenticación real, accediendo desde el flujo de reserva (igual que en HU-01 y HU-02).
- El RUT es único y se compara normalizado (sin puntos ni guion) para evitar duplicados; no se valida dígito verificador.
- Si el registro se inicia desde HU-02, el bloque seleccionado se conserva para retomar la reserva al finalizar.
- No se editan ni eliminan datos del Paciente en esta historia.

## Fuera de alcance de esta historia
- La reserva de la hora en sí (HU-02 / CU-02).
- Autenticación real o inicio de sesión (se usa selector de rol de demostración).
- Edición o eliminación posterior de los datos del paciente.
- Ficha clínica y datos clínicos (HU-09).
- Los requisitos no funcionales RP-18, RP-19 y RP-20 se consideran contexto.
