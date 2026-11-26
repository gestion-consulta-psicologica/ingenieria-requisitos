-- HU-09 — Trazabilidad de accesos e historial de antecedentes
-- La bitácora registra qué ficha se consultó o modificó y qué usuario lo hizo,
-- sin guardar contenido clínico. Los antecedentes conservan sus versiones
-- anteriores en lugar de sobrescribirse.

BEGIN IMMEDIATE;

ALTER TABLE bitacora_clinica ADD COLUMN paciente_id INTEGER REFERENCES paciente(id);
ALTER TABLE bitacora_clinica ADD COLUMN usuario TEXT;

CREATE INDEX IF NOT EXISTS idx_bitacora_clinica_paciente
    ON bitacora_clinica (paciente_id, fecha);

CREATE TABLE ficha_clinica_historial (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES ficha_clinica(paciente_id),
    fecha_reemplazo TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo_consulta TEXT NOT NULL,
    antecedentes_salud_mental TEXT NOT NULL,
    diagnosticos TEXT NOT NULL,
    medicamentos TEXT NOT NULL,
    datos_adulto_responsable TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ficha_clinica_historial_paciente
    ON ficha_clinica_historial (paciente_id, id);

-- Guarda la versión anterior cada vez que cambian los antecedentes.
-- No guarda versiones vacías (la ficha recién abierta) ni guardados sin cambios.
CREATE TRIGGER IF NOT EXISTS trg_ficha_clinica_historial
BEFORE UPDATE ON ficha_clinica
WHEN (OLD.motivo_consulta <> '' OR OLD.antecedentes_salud_mental <> ''
      OR OLD.diagnosticos <> '' OR OLD.medicamentos <> ''
      OR OLD.datos_adulto_responsable <> '')
 AND (OLD.motivo_consulta IS NOT NEW.motivo_consulta
      OR OLD.antecedentes_salud_mental IS NOT NEW.antecedentes_salud_mental
      OR OLD.diagnosticos IS NOT NEW.diagnosticos
      OR OLD.medicamentos IS NOT NEW.medicamentos
      OR OLD.datos_adulto_responsable IS NOT NEW.datos_adulto_responsable)
BEGIN
    INSERT INTO ficha_clinica_historial (
        paciente_id, motivo_consulta, antecedentes_salud_mental,
        diagnosticos, medicamentos, datos_adulto_responsable
    ) VALUES (
        OLD.paciente_id, OLD.motivo_consulta, OLD.antecedentes_salud_mental,
        OLD.diagnosticos, OLD.medicamentos, OLD.datos_adulto_responsable
    );
END;

COMMIT;
