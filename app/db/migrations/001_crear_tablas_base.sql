-- HU-01 · Consultar disponibilidad
-- Tablas base derivadas del modelo de dominio.

CREATE TABLE IF NOT EXISTS psicologa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    correo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paciente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    fecha_nacimiento TEXT,
    direccion TEXT,
    escolaridad TEXT,
    ocupacion TEXT,
    telefono TEXT,
    correo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bloque_horario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    psicologa_id INTEGER NOT NULL REFERENCES psicologa(id),
    fecha TEXT NOT NULL,
    hora_inicio TEXT NOT NULL,
    hora_termino TEXT NOT NULL,
    modalidad TEXT NOT NULL,
    UNIQUE (psicologa_id, fecha, hora_inicio)
);

CREATE TABLE IF NOT EXISTS reserva (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id),
    bloque_horario_id INTEGER NOT NULL REFERENCES bloque_horario(id),
    fecha_registro TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (
        estado IN ('Pendiente de confirmación', 'Confirmada', 'Sin confirmar', 'Cancelada')
    )
);

-- Regla de vigencia de EST-01: solo una reserva vigente por bloque.
CREATE UNIQUE INDEX IF NOT EXISTS idx_reserva_vigente
    ON reserva (bloque_horario_id)
    WHERE estado IN ('Pendiente de confirmación', 'Confirmada');
