# Validación funcional integral — HU-01, HU-02, HU-02A, HU-03

> **Evidencia histórica:** este resultado corresponde a la implementación anterior con panel de simulación (`/simular`), validada el 2026-11-17. Fue superada por la migración a correo real por SMTP del 2026-11-18. No describe el sistema actual; la verificación vigente está en `.cin324/validaciones/VAL-HU-03-1.md` y en la suite `pytest`.

- [OK] F1 · La app responde y usa la base manual (sem 24/11 muestra bloques 2 y 4) — HTTP 200 (esperado 200)
- [OK] HU-01 · Raiz redirige a /disponibilidad — HTTP 303 (esperado 303)
- [OK] HU-01 · Semana 23-29 nov: bloques 2 y 4 disponibles — HTTP 200 (esperado 200)
- [OK] HU-01 · Semana 30 nov-6 dic: sin horarios y proximo 08/12/2026 — HTTP 200 (esperado 200)
- [OK] HU-01 · Semana 7-13 dic: bloque 5 disponible — HTTP 200 (esperado 200)
- [OK] HU-02 · Reservar bloque 2 con paciente existente — HTTP 303 (esperado 303)
- [OK] HU-02 · Reserva 3 creada (paciente 1, bloque 2, pendiente) — HTTP - (esperado -)
- [OK] HU-02 · Bloque 2 deja de estar disponible; bloque 4 sigue — HTTP 200 (esperado 200)
- [OK] HU-02 · Intentar reservar bloque 1 ocupado: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-02A · Reservar bloque 4 con RUT nuevo redirige a registro — HTTP 303 (esperado 303)
- [OK] HU-02A · Formulario de registro con bloque 4 — HTTP 200 (esperado 200)
- [OK] HU-02A · Registrar paciente 99.999.999-9 con correo vacio — HTTP 303 (esperado 303)
- [OK] HU-02A · Paciente 99.999.999-9 almacenado con correo NULL — HTTP - (esperado -)
- [OK] HU-02A · Completar reserva del bloque 4 — HTTP 303 (esperado 303)
- [OK] HU-02A · Reserva 4 creada (paciente 2, bloque 4, pendiente) — HTTP - (esperado -)
- [OK] HU-02A · Validacion de campos obligatorios (400) — HTTP 400 (esperado 400)
- [OK] HU-02A · RUT duplicado no crea segundo paciente — HTTP 303 (esperado 303)
- [OK] HU-02A · No se crea segundo paciente por RUT duplicado — HTTP - (esperado 2)
- [OK] HU-02A · Semana 24 nov queda sin bloques; proximo 08/12/2026 — HTTP 200 (esperado 200)
- [OK] HU-03 · Reserva 1 pendiente: panel visible y sin acciones de respuesta — HTTP 200 (esperado 200)
- [OK] HU-03 · Confirmar sin solicitud pendiente: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · Simular víspera en reserva 1 — HTTP 303 (esperado 303)
- [OK] HU-03 · Solicitud de víspera creada (2026-11-23, pendiente) — HTTP - (esperado -)
- [OK] HU-03 · Con solicitud pendiente aparecen las acciones de respuesta — HTTP 200 (esperado 200)
- [OK] HU-03 · Repetir víspera: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · Simular recordatorio en reserva 1 — HTTP 303 (esperado 303)
- [OK] HU-03 · Víspera reemplazada y recordatorio pendiente — HTTP - (esperado -)
- [OK] HU-03 · Repetir recordatorio: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · Simular hora de atencion en reserva 1 — HTTP 303 (esperado 303)
- [OK] HU-03 · Reserva 1 Sin confirmar, solicitud vencida y cargo $5.000 — HTTP - (esperado -)
- [OK] HU-03 · Detalle reserva 1 muestra Sin confirmar, vencida y cargo — HTTP 200 (esperado 200)
- [OK] HU-03 · Repetir hora no duplica el cargo: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · El cargo no se duplica — HTTP - (esperado 1)
- [OK] HU-03 · Simular víspera en reserva 3 — HTTP 303 (esperado 303)
- [OK] HU-03 · Confirmar asistencia de reserva 3 — HTTP 303 (esperado 303)
- [OK] HU-03 · Reserva 3 Confirmada con solicitud respondida confirma — HTTP - (esperado -)
- [OK] HU-03 · Detalle reserva 3 muestra Confirmada — HTTP 200 (esperado 200)
- [OK] HU-03 · Reintentar respuesta en reserva 3: HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · Simular víspera en reserva 4 — HTTP 303 (esperado 303)
- [OK] HU-03 · Respuesta no asistira en reserva 4 — HTTP 303 (esperado 303)
- [OK] HU-03 · Reserva 4 Cancelada con respuesta no asistira — HTTP - (esperado -)
- [OK] HU-03 · Detalle reserva 4 muestra Cancelada — HTTP 200 (esperado 200)
- [OK] HU-03 · Bloque 4 vuelve a estar disponible — HTTP 200 (esperado 200)
- [OK] HU-03 · Confirmar reserva 2 (ya Confirmada): HTTP 409 — HTTP 409 (esperado 409)
- [OK] HU-03 · GET reserva inexistente: 404 — HTTP 404 (esperado 404)
- [OK] HU-03 · POST confirmar inexistente: 404 — HTTP 404 (esperado 404)
- [OK] HU-03 · POST no-asistir inexistente: 404 — HTTP 404 (esperado 404)
- [OK] HU-03 · POST simular inexistente: 404 — HTTP 404 (esperado 404)

## Estado final

```json
{
  "reservas": [
    {
      "id": 1,
      "paciente_id": 1,
      "bloque_horario_id": 1,
      "fecha_registro": "2026-11-01T09:00:00",
      "estado": "Sin confirmar"
    },
    {
      "id": 2,
      "paciente_id": 1,
      "bloque_horario_id": 3,
      "fecha_registro": "2026-11-02T09:00:00",
      "estado": "Confirmada"
    },
    {
      "id": 3,
      "paciente_id": 1,
      "bloque_horario_id": 2,
      "fecha_registro": "2026-11-18T22:24:18",
      "estado": "Confirmada"
    },
    {
      "id": 4,
      "paciente_id": 2,
      "bloque_horario_id": 4,
      "fecha_registro": "2026-11-18T22:24:18",
      "estado": "Cancelada"
    }
  ],
  "solicitudes": [
    {
      "id": 1,
      "reserva_id": 1,
      "fecha_envio": "2026-11-23",
      "tipo": "aviso de víspera",
      "estado": "reemplazada",
      "respuesta": null,
      "fecha_respuesta": null,
      "fecha_cierre": "2026-11-24"
    },
    {
      "id": 2,
      "reserva_id": 1,
      "fecha_envio": "2026-11-24",
      "tipo": "recordatorio",
      "estado": "vencida",
      "respuesta": "sin respuesta",
      "fecha_respuesta": null,
      "fecha_cierre": "2026-11-24T10:00"
    },
    {
      "id": 3,
      "reserva_id": 3,
      "fecha_envio": "2026-11-23",
      "tipo": "aviso de víspera",
      "estado": "respondida",
      "respuesta": "confirma",
      "fecha_respuesta": "2026-11-18T22:24:18",
      "fecha_cierre": null
    },
    {
      "id": 4,
      "reserva_id": 4,
      "fecha_envio": "2026-11-25",
      "tipo": "aviso de víspera",
      "estado": "respondida",
      "respuesta": "no asistirá",
      "fecha_respuesta": "2026-11-18T22:24:18",
      "fecha_cierre": null
    }
  ],
  "cargos": [
    {
      "id": 1,
      "paciente_id": 1,
      "reserva_id": 1,
      "monto": 5000,
      "motivo": "sin confirmar",
      "fecha": "2026-11-24"
    }
  ],
  "pacientes": [
    {
      "id": 1,
      "nombre_completo": "Paciente de Ejemplo",
      "rut": "22.222.222-2",
      "telefono": "+56 9 1111 1111",
      "correo": "paciente@example.cl"
    },
    {
      "id": 2,
      "nombre_completo": "Paciente Nuevo",
      "rut": "99.999.999-9",
      "telefono": "+56 9 9999 9999",
      "correo": null
    }
  ],
  "bloques": [
    {
      "id": 1,
      "psicologa_id": 1,
      "fecha": "2026-11-24",
      "hora_inicio": "10:00",
      "hora_termino": "10:50",
      "modalidad": "presencial"
    },
    {
      "id": 2,
      "psicologa_id": 1,
      "fecha": "2026-11-24",
      "hora_inicio": "11:00",
      "hora_termino": "11:50",
      "modalidad": "presencial"
    },
    {
      "id": 3,
      "psicologa_id": 1,
      "fecha": "2026-11-26",
      "hora_inicio": "10:00",
      "hora_termino": "10:50",
      "modalidad": "presencial"
    },
    {
      "id": 4,
      "psicologa_id": 1,
      "fecha": "2026-11-26",
      "hora_inicio": "11:00",
      "hora_termino": "11:50",
      "modalidad": "online"
    },
    {
      "id": 5,
      "psicologa_id": 1,
      "fecha": "2026-12-08",
      "hora_inicio": "10:00",
      "hora_termino": "10:50",
      "modalidad": "online"
    }
  ],
  "integrity_check": [
    "ok"
  ],
  "foreign_key_check": [],
  "persistencia_reconexion": true,
  "asociaciones_cargo_validas": true
}
```