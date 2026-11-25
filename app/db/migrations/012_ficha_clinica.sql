BEGIN IMMEDIATE;

CREATE TABLE ficha_clinica (
    paciente_id INTEGER PRIMARY KEY REFERENCES paciente(id),
    fecha_apertura TEXT NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE registro_evolucion (
    atencion_id INTEGER PRIMARY KEY REFERENCES atencion(id),
    paciente_id INTEGER NOT NULL REFERENCES ficha_clinica(paciente_id),
    observaciones TEXT NOT NULL,
    pruebas_aplicadas TEXT NOT NULL DEFAULT ''
);

CREATE TABLE bitacora_clinica (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rol TEXT CHECK (rol IN ('Paciente', 'Psicóloga')),
    operacion TEXT NOT NULL CHECK (operacion IN ('lectura', 'escritura')),
    resultado TEXT NOT NULL CHECK (resultado IN ('denegado', 'permitido'))
);

COMMIT;
