BEGIN IMMEDIATE;

CREATE TABLE bitacora_clinica_020 (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rol TEXT CHECK (rol IN ('Paciente', 'Psicóloga', 'Psiquiatra')),
    operacion TEXT NOT NULL CHECK (operacion IN ('lectura', 'escritura')),
    resultado TEXT NOT NULL CHECK (resultado IN ('denegado', 'permitido')),
    paciente_id INTEGER REFERENCES paciente(id),
    usuario TEXT
);

INSERT INTO bitacora_clinica_020 (id, fecha, rol, operacion, resultado, paciente_id, usuario)
SELECT id, fecha, rol, operacion, resultado, paciente_id, usuario
FROM bitacora_clinica;

DROP TABLE bitacora_clinica;
ALTER TABLE bitacora_clinica_020 RENAME TO bitacora_clinica;
CREATE INDEX idx_bitacora_clinica_paciente ON bitacora_clinica (paciente_id, fecha);

COMMIT;
