-- HU-05 — Comprobar el pago
-- Tablas derivadas del modelo de dominio para consultar la atención,
-- su pago y los comprobantes de transferencia. No modifica las tablas
-- de reservas, pacientes, bloques ni notificaciones.

CREATE TABLE IF NOT EXISTS atencion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reserva(id),
    tipo_atencion TEXT NOT NULL CHECK (tipo_atencion IN ('presencial', 'online')),
    monto INTEGER NOT NULL CHECK (monto >= 0),
    estado TEXT NOT NULL CHECK (
        estado IN ('programada', 'realizada', 'inasistencia', 'inasistencia justificada')
    )
);

CREATE TABLE IF NOT EXISTS pago (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atencion_id INTEGER NOT NULL UNIQUE REFERENCES atencion(id),
    monto_atencion INTEGER NOT NULL CHECK (monto_atencion >= 0),
    monto_pagado INTEGER NOT NULL DEFAULT 0 CHECK (monto_pagado >= 0),
    estado TEXT NOT NULL CHECK (
        estado IN ('Pendiente', 'Pagado', 'Pago incompleto')
    )
);

CREATE INDEX IF NOT EXISTS idx_pago_estado
    ON pago (estado);

CREATE TABLE IF NOT EXISTS comprobante_transferencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pago_id INTEGER NOT NULL REFERENCES pago(id),
    monto INTEGER NOT NULL CHECK (monto > 0),
    fecha_transferencia TEXT NOT NULL,
    cuenta_destino TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comprobante_transferencia_pago
    ON comprobante_transferencia (pago_id);
