-- HU-09 / RD-02 — Historial de antecedentes calculado en el código
-- Con el cifrado de la ficha (RD-02), el mismo texto produce un valor cifrado
-- distinto en cada guardado, así que el trigger de la migración 015 ya no puede
-- distinguir un cambio real de un guardado sin cambios. La comparación se hace
-- ahora en la aplicación, con el texto descifrado (app/rutas/clinica.py).

DROP TRIGGER IF EXISTS trg_ficha_clinica_historial;
