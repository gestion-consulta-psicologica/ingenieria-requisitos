BEGIN IMMEDIATE;

ALTER TABLE atencion ADD COLUMN justificacion_inasistencia TEXT;

CREATE TABLE cargo_011 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    reserva_id INTEGER UNIQUE REFERENCES reserva(id),
    atencion_id INTEGER UNIQUE REFERENCES atencion(id),
    monto INTEGER NOT NULL CHECK (monto = 5000),
    motivo TEXT NOT NULL CHECK (
        motivo IN ('sin confirmar', 'inasistencia', 'cancelación')
    ),
    fecha TEXT NOT NULL,
    CHECK ((reserva_id IS NULL) <> (atencion_id IS NULL))
);

INSERT INTO cargo_011 (id, paciente_id, reserva_id, monto, motivo, fecha)
SELECT id, paciente_id, reserva_id, monto, motivo, fecha FROM cargo;

DROP TABLE cargo;
ALTER TABLE cargo_011 RENAME TO cargo;

COMMIT;
