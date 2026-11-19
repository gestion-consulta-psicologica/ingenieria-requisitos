-- HU-03 — Estado y cierre de SolicitudConfirmacion
-- Preflight de datos históricos, backfill determinista y restricciones finales.

BEGIN IMMEDIATE;

CREATE TEMP TABLE IF NOT EXISTS _preflight_004 (
    solicitud_id INTEGER,
    reserva_id INTEGER,
    motivo TEXT NOT NULL
);

DELETE FROM _preflight_004;

INSERT INTO _preflight_004 (solicitud_id, reserva_id, motivo)
SELECT s.id, s.reserva_id, 'respuesta efectiva sin fecha_respuesta'
FROM solicitud_confirmacion s
WHERE s.respuesta IN ('confirma', 'no asistirá')
  AND s.fecha_respuesta IS NULL;

INSERT INTO _preflight_004 (solicitud_id, reserva_id, motivo)
SELECT s.id, s.reserva_id, 'respuesta sin respuesta sin fecha_respuesta'
FROM solicitud_confirmacion s
WHERE s.respuesta = 'sin respuesta'
  AND s.fecha_respuesta IS NULL;

INSERT INTO _preflight_004 (solicitud_id, reserva_id, motivo)
SELECT s.id, s.reserva_id, 'solicitud sin respuesta y reserva no pendiente sin solicitud posterior'
FROM solicitud_confirmacion s
JOIN reserva r ON r.id = s.reserva_id
WHERE s.respuesta IS NULL
  AND r.estado <> 'Pendiente de confirmación'
  AND NOT EXISTS (
      SELECT 1
      FROM solicitud_confirmacion s2
      WHERE s2.reserva_id = s.reserva_id
        AND (
            s2.fecha_envio > s.fecha_envio
            OR (s2.fecha_envio = s.fecha_envio AND s2.id > s.id)
        )
  );

INSERT INTO _preflight_004 (solicitud_id, reserva_id, motivo)
SELECT s.id, s.reserva_id, 'respuesta no coincide con el estado de la reserva'
FROM solicitud_confirmacion s
JOIN reserva r ON r.id = s.reserva_id
WHERE (s.respuesta = 'confirma' AND r.estado <> 'Confirmada')
   OR (s.respuesta = 'no asistirá' AND r.estado <> 'Cancelada')
   OR (s.respuesta = 'sin respuesta' AND r.estado <> 'Sin confirmar');

INSERT INTO _preflight_004 (solicitud_id, reserva_id, motivo)
SELECT NULL, candidatas.reserva_id, 'más de una solicitud candidata a quedar pendiente'
FROM (
    SELECT s.reserva_id,
           ROW_NUMBER() OVER (
               PARTITION BY s.reserva_id
               ORDER BY s.fecha_envio DESC, s.id DESC
           ) AS posicion
    FROM solicitud_confirmacion s
    JOIN reserva r ON r.id = s.reserva_id
    WHERE s.respuesta IS NULL
      AND r.estado = 'Pendiente de confirmación'
      AND NOT EXISTS (
          SELECT 1
          FROM solicitud_confirmacion s2
          WHERE s2.reserva_id = s.reserva_id
            AND (
                s2.fecha_envio > s.fecha_envio
                OR (s2.fecha_envio = s.fecha_envio AND s2.id > s.id)
            )
      )
) candidatas
WHERE candidatas.posicion > 1;

CREATE TEMP TABLE IF NOT EXISTS _preflight_004_guard (
    total INTEGER NOT NULL CHECK (total = 0)
);

DELETE FROM _preflight_004_guard;

INSERT INTO _preflight_004_guard (total)
SELECT COUNT(*) FROM _preflight_004;

DROP TABLE _preflight_004_guard;
DROP TABLE _preflight_004;

DROP TABLE IF EXISTS solicitud_confirmacion_004;

CREATE TABLE solicitud_confirmacion_004 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
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
    UNIQUE (reserva_id, tipo),
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

WITH orden AS (
    SELECT s.id,
           LEAD(s.fecha_envio) OVER (
               PARTITION BY s.reserva_id
               ORDER BY s.fecha_envio, s.id
           ) AS siguiente_envio
    FROM solicitud_confirmacion s
)
INSERT INTO solicitud_confirmacion_004 (
    id, reserva_id, fecha_envio, tipo, estado, respuesta,
    fecha_respuesta, fecha_cierre
)
SELECT
    s.id,
    s.reserva_id,
    s.fecha_envio,
    s.tipo,
    CASE
        WHEN s.respuesta IN ('confirma', 'no asistirá') THEN 'respondida'
        WHEN s.respuesta = 'sin respuesta' THEN 'vencida'
        WHEN s.respuesta IS NULL AND o.siguiente_envio IS NOT NULL THEN 'reemplazada'
        WHEN s.respuesta IS NULL AND r.estado = 'Pendiente de confirmación' THEN 'pendiente'
    END,
    s.respuesta,
    CASE
        WHEN s.respuesta IN ('confirma', 'no asistirá') THEN s.fecha_respuesta
    END,
    CASE
        WHEN s.respuesta = 'sin respuesta' THEN s.fecha_respuesta
        WHEN s.respuesta IS NULL AND o.siguiente_envio IS NOT NULL THEN o.siguiente_envio
    END
FROM solicitud_confirmacion s
JOIN reserva r ON r.id = s.reserva_id
JOIN orden o ON o.id = s.id;

DROP TABLE solicitud_confirmacion;

ALTER TABLE solicitud_confirmacion_004 RENAME TO solicitud_confirmacion;

CREATE INDEX IF NOT EXISTS idx_solicitud_confirmacion_reserva
    ON solicitud_confirmacion (reserva_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_solicitud_pendiente
    ON solicitud_confirmacion (reserva_id)
    WHERE estado = 'pendiente';

COMMIT;
