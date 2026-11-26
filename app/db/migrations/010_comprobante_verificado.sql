ALTER TABLE comprobante_transferencia
ADD COLUMN verificado INTEGER NOT NULL DEFAULT 0 CHECK (verificado IN (0, 1));
