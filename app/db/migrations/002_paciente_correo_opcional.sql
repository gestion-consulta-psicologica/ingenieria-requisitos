-- HU-02A — Registrar datos del paciente
-- El paciente puede registrarse solo con teléfono, así que correo deja de ser obligatorio.

PRAGMA foreign_keys = OFF;

CREATE TABLE paciente_nuevo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    fecha_nacimiento TEXT,
    direccion TEXT,
    escolaridad TEXT,
    ocupacion TEXT,
    telefono TEXT,
    correo TEXT
);

INSERT INTO paciente_nuevo (
    id, nombre_completo, rut, fecha_nacimiento, direccion,
    escolaridad, ocupacion, telefono, correo
)
SELECT id, nombre_completo, rut, fecha_nacimiento, direccion,
       escolaridad, ocupacion, telefono, correo
FROM paciente;

DROP TABLE paciente;

ALTER TABLE paciente_nuevo RENAME TO paciente;

CREATE UNIQUE INDEX IF NOT EXISTS idx_paciente_rut_normalizado
    ON paciente (UPPER(REPLACE(REPLACE(REPLACE(rut, '.', ''), '-', ''), ' ', '')));

PRAGMA foreign_key_check;

PRAGMA foreign_keys = ON;
