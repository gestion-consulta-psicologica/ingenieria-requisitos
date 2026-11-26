BEGIN IMMEDIATE;

CREATE TABLE cuenta (
    id INTEGER PRIMARY KEY,
    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('paciente', 'psicologa')),
    paciente_id INTEGER UNIQUE REFERENCES paciente(id),
    psicologa_id INTEGER UNIQUE REFERENCES psicologa(id),
    correo_verificado_en INTEGER,
    identidad_verificada_en INTEGER,
    verificada_por INTEGER REFERENCES cuenta(id),
    rut_solicitado TEXT,
    nombre_solicitado TEXT,
    telefono_solicitado TEXT,
    bloque_preferido_id INTEGER REFERENCES bloque_horario(id) ON DELETE SET NULL,
    CHECK ((rol = 'psicologa' AND psicologa_id IS NOT NULL AND paciente_id IS NULL)
        OR (rol = 'paciente' AND psicologa_id IS NULL))
);

CREATE UNIQUE INDEX cuenta_una_psicologa ON cuenta(rol) WHERE rol = 'psicologa';

CREATE TABLE sesion (
    token_hash TEXT PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuenta(id) ON DELETE CASCADE,
    expira_en INTEGER NOT NULL
);
CREATE INDEX sesion_cuenta ON sesion(cuenta_id);

CREATE TABLE token_cuenta (
    token_hash TEXT PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuenta(id) ON DELETE CASCADE,
    proposito TEXT NOT NULL CHECK (proposito IN ('verificar', 'restablecer')),
    expira_en INTEGER NOT NULL,
    UNIQUE (cuenta_id, proposito)
);

CREATE TABLE limite_cuenta (
    clave TEXT PRIMARY KEY,
    expira_en INTEGER NOT NULL,
    intentos INTEGER NOT NULL
);

COMMIT;
