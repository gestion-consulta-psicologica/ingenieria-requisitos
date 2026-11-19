# Consultas SQL - estado final de data/manual-hu03.db

## Bloques

| id | psicologa_id | fecha | hora_inicio | hora_termino | modalidad |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2026-11-24 | 10:00 | 10:50 | presencial |
| 2 | 1 | 2026-11-24 | 11:00 | 11:50 | presencial |
| 3 | 1 | 2026-11-26 | 10:00 | 10:50 | presencial |
| 4 | 1 | 2026-11-26 | 11:00 | 11:50 | online |
| 5 | 1 | 2026-12-08 | 10:00 | 10:50 | online |

## Reservas

| id | paciente_id | bloque_horario_id | fecha_registro | estado |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 2026-11-01T09:00:00 | Sin confirmar |
| 2 | 1 | 3 | 2026-11-02T09:00:00 | Confirmada |
| 3 | 1 | 2 | 2026-11-18T22:24:18 | Confirmada |
| 4 | 2 | 4 | 2026-11-18T22:24:18 | Cancelada |

## Solicitudes

| id | reserva_id | fecha_envio | tipo | estado | respuesta | fecha_respuesta | fecha_cierre |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2026-11-23 | aviso de víspera | reemplazada | None | None | 2026-11-24 |
| 2 | 1 | 2026-11-24 | recordatorio | vencida | sin respuesta | None | 2026-11-24T10:00 |
| 3 | 3 | 2026-11-23 | aviso de víspera | respondida | confirma | 2026-11-18T22:24:18 | None |
| 4 | 4 | 2026-11-25 | aviso de víspera | respondida | no asistirá | 2026-11-18T22:24:18 | None |

## Cargos

| id | paciente_id | reserva_id | monto | motivo | fecha |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 5000 | sin confirmar | 2026-11-24 |

## Pacientes

| id | nombre_completo | rut | telefono | correo |
| --- | --- | --- | --- | --- |
| 1 | Paciente de Ejemplo | 22.222.222-2 | +56 9 1111 1111 | paciente@example.cl |
| 2 | Paciente Nuevo | 99.999.999-9 | +56 9 9999 9999 | None |

## Integridad

- PRAGMA integrity_check: ['ok']
- PRAGMA foreign_key_check: []