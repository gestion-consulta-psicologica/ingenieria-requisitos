# Tasks

## 1. Datos y migración

- [x] 1.1 Crear `app/db/migrations/007_atencion_pago.sql` con las tablas `atencion`, `pago` y `comprobante_transferencia`, sus claves foráneas, unicidades y `CHECK` de estados; verificar que una base temporal aplica la migración y registra `007_atencion_pago.sql` en `schema_migrations`.
- [x] 1.2 Ampliar `app/db/seed.py` con un bloque del jueves 12 de noviembre de 2026 a las 16:00, su reserva confirmada, una atención con comprobante y otra sin comprobante; verificar que ejecutar el seed dos veces mantiene los mismos datos y no duplica registros.

## 2. Lógica de consulta

- [x] 2.1 Crear `app/servicios/pagos.py` con `listar_atenciones_con_pago_pendiente(conexion)` y `obtener_pago_de_atencion(conexion, atencion_id)`, que devuelvan atención, paciente (nombre y RUT), pago y comprobantes; verificar con una prueba de servicio sobre una base temporal que una atención con comprobante devuelve sus datos y una sin comprobante devuelve la lista vacía.
- [x] 2.2 Verificar que el servicio es de solo lectura: ejecutar dos consultas consecutivas y comprobar que el estado del pago y los comprobantes no cambian (prueba automática).

## 3. Rutas y pantallas

- [x] 3.1 Crear `app/rutas/pagos.py` con `GET /pagos` y `GET /pagos/{atencion_id}`, registrar el router en `app/main.py`; verificar con `TestClient` que `/pagos` responde 200 y que un `atencion_id` inexistente responde 404.
- [x] 3.2 Crear `app/templates/pagos.html` con el listado de atenciones con pago pendiente y `app/templates/pago_detalle.html` con nombre y RUT del paciente, monto de la atención, monto pagado, estado, comprobantes (monto, fecha de transferencia, cuenta de destino) o aviso de ausencia, y la opción «Registrar estado de pago» visible e inactiva; verificar el contenido renderizado con `TestClient`.
- [x] 3.3 Crear `tests/test_hu05_comprobar_pago.py` con una prueba por escenario de la especificación: «La atención tiene un comprobante de pago registrado», «La atención no tiene comprobante de pago» y «La psicóloga revisa la información y continúa al registro»; verificar que las tres pasan con `pytest`.

## 4. Documentación

- [x] 4.1 Actualizar `README.md` con la carga de datos de ejemplo, la URL `/pagos`, el recorrido de los dos escenarios Gherkin y el comando `pytest`; verificar que los comandos documentados se ejecutan tal como están escritos.

## Workflow follow-up

- Archivar el cambio después de que el estudiante valide el sistema.
- Verificar el resultado archivado en `openspec/changes/archive/` y las especificaciones principales.
