-- HU-05A — Modalidad válida del bloque horario
-- La atención exige tipo_atencion IN ('presencial', 'online') y se copia desde
-- la modalidad del bloque. Si el bloque admitiera otro valor, la atención no
-- podría originarse. SQLite no permite agregar un CHECK a una tabla existente
-- sin reconstruirla, así que la regla se aplica con triggers.

CREATE TRIGGER IF NOT EXISTS trg_bloque_modalidad_insertar
BEFORE INSERT ON bloque_horario
WHEN NEW.modalidad NOT IN ('presencial', 'online')
BEGIN
    SELECT RAISE(ABORT, 'modalidad inválida: use presencial u online');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloque_modalidad_actualizar
BEFORE UPDATE OF modalidad ON bloque_horario
WHEN NEW.modalidad NOT IN ('presencial', 'online')
BEGIN
    SELECT RAISE(ABORT, 'modalidad inválida: use presencial u online');
END;
