-- HU-03 — Notificaciones reales por correo electrónico
-- Cola persistente de correos y tokens seguros de un solo uso.
-- No modifica las tablas existentes.

CREATE TABLE IF NOT EXISTS correo_pendiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave_idempotencia TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK (
        tipo IN ('aviso_reserva', 'solicitud_confirmacion', 'aviso_cargo')
    ),
    reserva_id INTEGER REFERENCES reserva(id),
    solicitud_id INTEGER REFERENCES solicitud_confirmacion(id),
    destinatario TEXT,
    asunto TEXT NOT NULL,
    cuerpo_texto TEXT NOT NULL,
    cuerpo_html TEXT,
    estado TEXT NOT NULL CHECK (
        estado IN (
            'pendiente', 'enviando', 'enviado', 'fallido', 'omitido', 'cancelado'
        )
    ),
    intentos INTEGER NOT NULL DEFAULT 0 CHECK (intentos >= 0),
    max_intentos INTEGER NOT NULL DEFAULT 5 CHECK (max_intentos > 0),
    proximo_intento TEXT NOT NULL,
    ultimo_error TEXT,
    id_mensaje TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT NOT NULL,
    enviado_en TEXT,
    CHECK (
        (estado = 'enviado' AND enviado_en IS NOT NULL AND destinatario IS NOT NULL)
        OR estado <> 'enviado'
    ),
    CHECK (estado <> 'omitido' OR destinatario IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_correo_pendiente_cola
    ON correo_pendiente (estado, proximo_intento);

CREATE INDEX IF NOT EXISTS idx_correo_pendiente_reserva
    ON correo_pendiente (reserva_id);

CREATE INDEX IF NOT EXISTS idx_correo_pendiente_solicitud
    ON correo_pendiente (solicitud_id);

CREATE TABLE IF NOT EXISTS token_confirmacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER NOT NULL REFERENCES solicitud_confirmacion(id),
    accion TEXT NOT NULL CHECK (accion IN ('confirmar', 'cancelar')),
    token_hash TEXT NOT NULL UNIQUE,
    creado_en TEXT NOT NULL,
    expira_en TEXT NOT NULL,
    usado_en TEXT,
    UNIQUE (solicitud_id, accion)
);

CREATE INDEX IF NOT EXISTS idx_token_confirmacion_solicitud
    ON token_confirmacion (solicitud_id);
