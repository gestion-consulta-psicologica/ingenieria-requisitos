-- HU-10. Cada bloque identifica un único profesional responsable.
PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TABLE bloque_horario_021 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    psicologa_id INTEGER REFERENCES psicologa(id),
    fecha TEXT NOT NULL,
    hora_inicio TEXT NOT NULL,
    hora_termino TEXT NOT NULL,
    modalidad TEXT NOT NULL,
    psiquiatra_cuenta_id INTEGER REFERENCES cuenta(id),
    CHECK ((psicologa_id IS NULL) <> (psiquiatra_cuenta_id IS NULL)),
    UNIQUE (psicologa_id, fecha, hora_inicio),
    UNIQUE (psiquiatra_cuenta_id, fecha, hora_inicio)
);

INSERT INTO bloque_horario_021 (id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad)
SELECT id, psicologa_id, fecha, hora_inicio, hora_termino, modalidad FROM bloque_horario;

INSERT INTO sqlite_sequence (name, seq)
SELECT 'bloque_horario_021', seq FROM sqlite_sequence WHERE name = 'bloque_horario'
  AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'bloque_horario_021');
UPDATE sqlite_sequence
SET seq = MAX(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'bloque_horario'), 0))
WHERE name = 'bloque_horario_021';

DROP TABLE bloque_horario;
ALTER TABLE bloque_horario_021 RENAME TO bloque_horario;

CREATE TRIGGER trg_bloque_modalidad_insertar
BEFORE INSERT ON bloque_horario
WHEN NEW.modalidad NOT IN ('presencial', 'online')
BEGIN
    SELECT RAISE(ABORT, 'modalidad inválida: use presencial u online');
END;

CREATE TRIGGER trg_bloque_modalidad_actualizar
BEFORE UPDATE OF modalidad ON bloque_horario
WHEN NEW.modalidad NOT IN ('presencial', 'online')
BEGIN
    SELECT RAISE(ABORT, 'modalidad inválida: use presencial u online');
END;

-- Las derivaciones previas conservan su estado y fechas. No se transfieren retroactivamente.
CREATE TABLE derivacion_021 (
    id INTEGER PRIMARY KEY,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    psicologa_cuenta_id INTEGER NOT NULL REFERENCES cuenta(id),
    psiquiatra_cuenta_id INTEGER NOT NULL REFERENCES cuenta(id),
    creada_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    aceptada_en TEXT,
    rechazada_en TEXT,
    version_origen INTEGER,
    bloque_origen_id INTEGER REFERENCES bloque_horario(id),
    bloque_destino_id INTEGER REFERENCES bloque_horario(id),
    estado TEXT GENERATED ALWAYS AS (
        CASE WHEN aceptada_en IS NOT NULL THEN 'Aceptada'
             WHEN rechazada_en IS NOT NULL THEN 'Rechazada'
             ELSE 'Pendiente' END
    ) VIRTUAL,
    CHECK (aceptada_en IS NULL OR rechazada_en IS NULL),
    CHECK ((version_origen IS NULL) = (bloque_origen_id IS NULL)),
    CHECK (version_origen IS NULL OR (aceptada_en IS NULL) = (bloque_destino_id IS NULL)),
    UNIQUE (reserva_id, psiquiatra_cuenta_id, version_origen)
);

INSERT INTO derivacion_021 (
    id, reserva_id, paciente_id, psicologa_cuenta_id, psiquiatra_cuenta_id, creada_en, aceptada_en
)
SELECT id, reserva_id, paciente_id, psicologa_cuenta_id, psiquiatra_cuenta_id, creada_en, aceptada_en
FROM derivacion;

DROP TABLE derivacion;
ALTER TABLE derivacion_021 RENAME TO derivacion;
CREATE INDEX derivacion_emisora ON derivacion(psicologa_cuenta_id, id);
CREATE INDEX derivacion_receptor ON derivacion(psiquiatra_cuenta_id, id);
CREATE UNIQUE INDEX derivacion_pendiente_por_ciclo ON derivacion(reserva_id, version_origen)
WHERE aceptada_en IS NULL AND rechazada_en IS NULL AND version_origen IS NOT NULL;

COMMIT;
PRAGMA foreign_keys = ON;
