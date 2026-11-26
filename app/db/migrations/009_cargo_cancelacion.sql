BEGIN IMMEDIATE;

CREATE TABLE cargo_009 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reserva(id),
    monto INTEGER NOT NULL CHECK (monto = 5000),
    motivo TEXT NOT NULL CHECK (
        motivo IN ('sin confirmar', 'inasistencia', 'cancelación')
    ),
    fecha TEXT NOT NULL
);

INSERT INTO cargo_009 (id, paciente_id, reserva_id, monto, motivo, fecha)
SELECT id, paciente_id, reserva_id, monto, motivo, fecha FROM cargo;

DROP TABLE cargo;
ALTER TABLE cargo_009 RENAME TO cargo;

COMMIT;
