-- HU-10. Conserva IDs, credenciales y referencias de las cuentas existentes.
PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TABLE cuenta_017 (
    id INTEGER PRIMARY KEY,
    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('paciente', 'psicologa', 'psiquiatra')),
    paciente_id INTEGER UNIQUE REFERENCES paciente(id),
    psicologa_id INTEGER UNIQUE REFERENCES psicologa(id),
    correo_verificado_en INTEGER,
    identidad_verificada_en INTEGER,
    verificada_por INTEGER REFERENCES cuenta(id),
    rut_solicitado TEXT,
    nombre_solicitado TEXT,
    telefono_solicitado TEXT,
    bloque_preferido_id INTEGER REFERENCES bloque_horario(id) ON DELETE SET NULL,
    nombre_psiquiatra TEXT,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    CHECK (
        (rol = 'psicologa' AND psicologa_id IS NOT NULL AND paciente_id IS NULL
            AND nombre_psiquiatra IS NULL)
        OR (rol = 'paciente' AND psicologa_id IS NULL AND nombre_psiquiatra IS NULL)
        OR (rol = 'psiquiatra' AND psicologa_id IS NULL AND paciente_id IS NULL
            AND nombre_psiquiatra IS NOT NULL AND length(trim(nombre_psiquiatra)) > 0)
    )
);

INSERT INTO cuenta_017 (
    id, correo, clave_hash, rol, paciente_id, psicologa_id, correo_verificado_en,
    identidad_verificada_en, verificada_por, rut_solicitado, nombre_solicitado,
    telefono_solicitado, bloque_preferido_id
)
SELECT id, correo, clave_hash, rol, paciente_id, psicologa_id, correo_verificado_en,
       identidad_verificada_en, verificada_por, rut_solicitado, nombre_solicitado,
       telefono_solicitado, bloque_preferido_id
FROM cuenta;

DROP TABLE cuenta;
ALTER TABLE cuenta_017 RENAME TO cuenta;
CREATE UNIQUE INDEX cuenta_una_psicologa ON cuenta(rol) WHERE rol = 'psicologa';

CREATE TABLE derivacion (
    id INTEGER PRIMARY KEY,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    psicologa_cuenta_id INTEGER NOT NULL REFERENCES cuenta(id),
    psiquiatra_cuenta_id INTEGER NOT NULL REFERENCES cuenta(id),
    creada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    aceptada_en TEXT,
    estado TEXT GENERATED ALWAYS AS (
        CASE WHEN aceptada_en IS NULL THEN 'Pendiente' ELSE 'Aceptada' END
    ) VIRTUAL,
    UNIQUE (reserva_id, psiquiatra_cuenta_id)
);

CREATE INDEX derivacion_emisora ON derivacion(psicologa_cuenta_id, id);
CREATE INDEX derivacion_receptor ON derivacion(psiquiatra_cuenta_id, id);

COMMIT;
PRAGMA foreign_keys = ON;
