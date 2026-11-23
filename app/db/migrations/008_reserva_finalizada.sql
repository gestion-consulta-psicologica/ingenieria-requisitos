-- HU-05A — Reserva finalizada
-- Reconstruye reserva para permitir el estado Finalizada cuando la reserva
-- confirmada origina su atención y su pago.

PRAGMA foreign_keys = OFF;

BEGIN IMMEDIATE;

CREATE TABLE reserva_008 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    bloque_horario_id INTEGER NOT NULL REFERENCES bloque_horario(id),
    fecha_registro TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (
        estado IN (
            'Pendiente de confirmación',
            'Confirmada',
            'Sin confirmar',
            'Cancelada',
            'Finalizada'
        )
    ),
    version INTEGER NOT NULL DEFAULT 1
);

INSERT INTO reserva_008 (
    id, paciente_id, bloque_horario_id, fecha_registro, estado, version
)
SELECT
    id, paciente_id, bloque_horario_id, fecha_registro, estado, version
FROM reserva;

DROP TABLE reserva;

ALTER TABLE reserva_008 RENAME TO reserva;

CREATE UNIQUE INDEX IF NOT EXISTS idx_reserva_vigente
    ON reserva (bloque_horario_id)
    WHERE estado IN ('Pendiente de confirmación', 'Confirmada');

COMMIT;

PRAGMA foreign_keys = ON;
