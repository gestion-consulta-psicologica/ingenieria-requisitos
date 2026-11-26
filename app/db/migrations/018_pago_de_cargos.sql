-- HU-06 (extensión) — Pagar un cargo de $5.000
-- El cargo (por cancelación, por no confirmar o por inasistencia) se paga como
-- la atención: el paciente registra uno o más comprobantes de transferencia y la
-- psicóloga los verifica (Pendiente → Pago incompleto / Pagado, como EST-02).
-- Los cargos existentes quedan Pendientes con monto pagado 0.

BEGIN IMMEDIATE;

ALTER TABLE cargo ADD COLUMN estado TEXT NOT NULL DEFAULT 'Pendiente'
    CHECK (estado IN ('Pendiente', 'Pago incompleto', 'Pagado'));
ALTER TABLE cargo ADD COLUMN monto_pagado INTEGER NOT NULL DEFAULT 0
    CHECK (monto_pagado >= 0);

CREATE INDEX IF NOT EXISTS idx_cargo_estado ON cargo (estado);
CREATE INDEX IF NOT EXISTS idx_cargo_paciente ON cargo (paciente_id);

CREATE TABLE comprobante_cargo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cargo_id INTEGER NOT NULL REFERENCES cargo(id),
    monto INTEGER NOT NULL CHECK (monto > 0),
    fecha_transferencia TEXT NOT NULL,
    cuenta_destino TEXT NOT NULL,
    verificado INTEGER NOT NULL DEFAULT 0 CHECK (verificado IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_comprobante_cargo_cargo ON comprobante_cargo (cargo_id);

COMMIT;
