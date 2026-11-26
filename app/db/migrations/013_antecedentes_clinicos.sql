BEGIN IMMEDIATE;

ALTER TABLE ficha_clinica ADD COLUMN motivo_consulta TEXT NOT NULL DEFAULT '';
ALTER TABLE ficha_clinica ADD COLUMN antecedentes_salud_mental TEXT NOT NULL DEFAULT '';
ALTER TABLE ficha_clinica ADD COLUMN diagnosticos TEXT NOT NULL DEFAULT '';
ALTER TABLE ficha_clinica ADD COLUMN medicamentos TEXT NOT NULL DEFAULT '';
ALTER TABLE ficha_clinica ADD COLUMN datos_adulto_responsable TEXT NOT NULL DEFAULT '';

COMMIT;
