-- HU-04 — Reagendar o cancelar una hora
-- Agrega el ciclo de confirmación de la reserva y el historial de cambios.
-- Reconstruye solicitud_confirmacion para permitir un nuevo ciclo por reagendamiento.
-- No modifica las tablas de pacientes ni bloque_horario.

PRAGMA foreign_keys = OFF;

BEGIN IMMEDIATE;

ALTER TABLE reserva ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

CREATE TABLE solicitud_confirmacion_006 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    version INTEGER NOT NULL DEFAULT 1,
    fecha_envio TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('aviso de víspera', 'recordatorio')),
    estado TEXT NOT NULL CHECK (
        estado IN ('pendiente', 'respondida', 'reemplazada', 'vencida')
    ),
    respuesta TEXT CHECK (
        respuesta IN ('confirma', 'no asistirá', 'sin respuesta')
    ),
    fecha_respuesta TEXT,
    fecha_cierre TEXT,
    UNIQUE (reserva_id, version, tipo),
    CHECK (
        (
            estado = 'pendiente'
            AND respuesta IS NULL
            AND fecha_respuesta IS NULL
            AND fecha_cierre IS NULL
        )
        OR (
            estado = 'respondida'
            AND respuesta IN ('confirma', 'no asistirá')
            AND fecha_respuesta IS NOT NULL
            AND fecha_cierre IS NULL
        )
        OR (
            estado = 'reemplazada'
            AND respuesta IS NULL
            AND fecha_respuesta IS NULL
            AND fecha_cierre IS NOT NULL
        )
        OR (
            estado = 'vencida'
            AND respuesta = 'sin respuesta'
            AND fecha_respuesta IS NULL
            AND fecha_cierre IS NOT NULL
        )
    )
);

INSERT INTO solicitud_confirmacion_006 (
    id, reserva_id, version, fecha_envio, tipo, estado, respuesta,
    fecha_respuesta, fecha_cierre
)
SELECT
    id, reserva_id, 1, fecha_envio, tipo, estado, respuesta,
    fecha_respuesta, fecha_cierre
FROM solicitud_confirmacion;

DROP TABLE solicitud_confirmacion;

ALTER TABLE solicitud_confirmacion_006 RENAME TO solicitud_confirmacion;

CREATE INDEX IF NOT EXISTS idx_solicitud_confirmacion_reserva
    ON solicitud_confirmacion (reserva_id);

CREATE INDEX IF NOT EXISTS idx_solicitud_confirmacion_version
    ON solicitud_confirmacion (reserva_id, version);

CREATE UNIQUE INDEX IF NOT EXISTS ux_solicitud_pendiente
    ON solicitud_confirmacion (reserva_id)
    WHERE estado = 'pendiente';

CREATE TABLE reserva_historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('cancelacion', 'reagendamiento')),
    estado_anterior TEXT NOT NULL,
    estado_nuevo TEXT NOT NULL,
    bloque_anterior_id INTEGER REFERENCES bloque_horario(id),
    bloque_nuevo_id INTEGER REFERENCES bloque_horario(id),
    version_anterior INTEGER NOT NULL,
    version_nueva INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    CHECK (
        (
            tipo = 'cancelacion'
            AND bloque_nuevo_id IS NULL
            AND version_nueva = version_anterior
        )
        OR (
            tipo = 'reagendamiento'
            AND bloque_nuevo_id IS NOT NULL
            AND version_nueva = version_anterior + 1
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_reserva_historial_reserva
    ON reserva_historial (reserva_id);

COMMIT;

PRAGMA foreign_keys = ON;
