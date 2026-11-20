# Tasks

## 1. Configuración y datos de ejemplo

- [x] 1.1 Agregar `monto_atencion_clp()` en `app/configuracion.py` para leer `MONTO_ATENCION_CLP` con $30.000 por defecto; verificar con una prueba que el valor por defecto es 30000 y que la variable de entorno lo cambia.
- [x] 1.2 Verificar que la reserva `2` del seed (`2026-11-17 10:00`, `Confirmada`, sin atención) sirve como caso vencido y, si hiciera falta, ajustar el seed; comprobar que no tiene atención y que una segunda reserva confirmada futura no se procesa.

## 2. Creación automática de Atencion y Pago

- [x] 2.1 Implementar `crear_atenciones_vencidas()` en `app/servicios/atenciones.py`: consultar reservas confirmadas vencidas sin atención y crear `Atencion` (`programada`) y `Pago` (`Pendiente`, `montoPagado = 0`) en una transacción; verificar los escenarios «La reserva confirmada llega a la hora de la atención» y «El sistema no duplica una atención ya originada» con pruebas sobre la reserva `2`.
- [x] 2.2 Integrar la llamada a `crear_atenciones_vencidas()` en `PlanificadorCorreos.ejecutar_ciclo`, después de `_procesar_reservas`, e incluir el conteo en el resultado; verificar con un `ahora` controlado que dos ciclos crean una sola atención y que las pruebas actuales del planificador siguen pasando.
- [x] 2.3 Agregar `obtener_atencion_de_reserva()` para obtener `atencion_id`, `pago_id` y `pago_estado` desde una reserva; verificar que la reserva `3` devuelve la atención `1` con pago `Pendiente` y que la reserva `2` devuelve `None` antes del procesamiento.

## 3. Registro del comprobante

- [x] 3.1 Implementar `registrar_comprobante()` para insertar un `ComprobanteTransferencia` asociado al pago sin modificar el estado ni `montoPagado`; verificar los escenarios «El paciente registra el comprobante de su transferencia» y «El paciente registra un segundo comprobante» comprobando que se conservan ambos registros.
- [x] 3.2 Agregar validaciones de monto entero positivo, fecha de transferencia ISO válida y cuenta de destino obligatoria; verificar los escenarios «El paciente no completa los datos obligatorios del comprobante» y «El comprobante tiene datos inválidos» comprobando que no se insertan filas y que el mensaje identifica el dato faltante o inválido.
- [x] 3.3 Rechazar el registro cuando no exista la atención, falte el pago o el pago esté `Pagado`; verificar los escenarios «La atención no tiene pago asociado» y «El pago ya está pagado» comprobando que no se modifica ningún comprobante.
- [x] 3.4 Extender el detalle de pago existente con `reserva_id` y la lista de comprobantes necesarios para el formulario; verificar que las pruebas de HU-05 siguen pasando y que el detalle de la atención `2` muestra sus comprobantes.

## 4. Rutas y plantillas

- [x] 4.1 Agregar `GET` y `POST /pagos/{atencion_id}/comprobante` en `app/rutas/pagos.py` con 400 para datos inválidos, 404 para atención o pago inexistente, 409 para pago `Pagado` y 303 al formulario con confirmación en éxito; verificar cada caso con `TestClient`.
- [x] 4.2 Crear `app/templates/pago_comprobante.html` con los datos de la atención, el formulario (`monto`, `fecha_transferencia`, `cuenta_destino`), los comprobantes anteriores y los mensajes de éxito o error; verificar que el HTML contiene los campos y que un registro exitoso muestra la confirmación.
- [x] 4.3 Pasar el identificador de atención y el estado del pago desde `app/rutas/reserva.py` y mostrar en `app/templates/reserva_confirmada.html` el enlace «Registrar comprobante de pago» solo para pagos `Pendiente` o `Pago incompleto`; verificar que aparece en la reserva `3` y que no aparece con pago `Pagado` ni sin atención.

## 5. Cierre e integración

- [x] 5.1 Ejecutar la suite completa con `source .venv/bin/activate && python -m pytest -q` y verificar que las 93 pruebas existentes y las nuevas de HU-05A pasan.
- [x] 5.2 Hacer una prueba manual con el planificador activo: reiniciar la base, arrancar `uvicorn app.main:app --reload`, comprobar que la reserva `2` origina atención y pago, registrar un comprobante desde `/reservas/3` o `/pagos/{atencion_id}/comprobante` y verlo en `/pagos`.
- [x] 5.3 Actualizar `.cin324/proyecto.md` con la historia implementada, las pruebas y la URL de demostración; verificar que la tabla de historias queda consistente.
- [x] 5.4 Actualizar `README.md` con la variable `MONTO_ATENCION_CLP`, la ruta del formulario, el flujo de demostración y el comando de pruebas; verificar que las instrucciones ejecutan lo escrito.

## Workflow follow-up

- Presentar `proposal.md`, `spec.md`, `design.md` y `tasks.md` al estudiante y esperar su confirmación antes de implementar.
- Implementar solo después de la aprobación; al terminar, archivar el cambio y verificar las specs principales.
