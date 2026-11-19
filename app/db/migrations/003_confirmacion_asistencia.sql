-- HU-03 — Confirmar o cancelar una hora
-- Tablas derivadas del modelo de dominio.

CREATE TABLE IF NOT EXISTS solicitud_confirmacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    fecha_envio TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('aviso de víspera', 'recordatorio')),
    respuesta TEXT CHECK (respuesta IN ('confirma', 'no asistirá', 'sin respuesta')),
    fecha_respuesta TEXT,
    UNIQUE (reserva_id, tipo)
);

CREATE INDEX IF NOT EXISTS idx_solicitud_confirmacion_reserva
    ON solicitud_confirmacion (reserva_id);

CREATE TABLE IF NOT EXISTS cargo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reserva(id),
    monto INTEGER NOT NULL CHECK (monto = 5000),
    motivo TEXT NOT NULL CHECK (motivo IN ('sin confirmar', 'inasistencia')),
    fecha TEXT NOT NULL
);
