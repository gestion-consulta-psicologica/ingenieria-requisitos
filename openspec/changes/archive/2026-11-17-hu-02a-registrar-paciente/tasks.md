# Tasks — HU-02A Registrar datos del paciente

## 1. Datos

- [x] 1.1 Crear `app/db/migrations/002_paciente_correo_opcional.sql` para reconstruir `paciente` con `correo` opcional, copiando los datos y conservando la unicidad del RUT; verificar con una prueba que una base con pacientes y reservas existentes conserva sus filas y permite un paciente sin correo.
- [x] 1.2 Confirmar que el seed y las migraciones siguen funcionando sobre una base nueva; ejecutar `pytest` y ver que las pruebas de HU-01 y HU-02 no se rompen.

## 2. Lógica de registro

- [x] 2.1 Crear `app/servicios/paciente.py` con la validación de nombre completo, RUT y al menos uno de teléfono o correo, y con `registrar_paciente`; verificar con pruebas unitarias los casos: solo teléfono, solo correo, sin contacto y sin nombre.
- [x] 2.2 Reutilizar la búsqueda y normalización de RUT de `app/servicios/reserva.py`; verificar que un RUT con puntos y guion encuentra al Paciente existente y que no se duplica.
- [x] 2.3 Manejar la carrera de dos registros con el mismo RUT capturando la violación de unicidad y devolviendo el registro existente; verificar con una prueba que solo queda un Paciente.

## 3. Rutas y pantallas

- [x] 3.1 Crear `GET /pacientes/registro` con `app/rutas/paciente.py` y la plantilla `registro_paciente.html`, mostrando nombre completo, RUT, teléfono y correo, y conservando `bloque_id`; verificar con `TestClient` que responde 200 y muestra el formulario.
- [x] 3.2 Crear `POST /pacientes/registro`: registrar al Paciente y responder `303` a `/reservar/<bloque_id>?rut=<rut>` cuando hay bloque, o a `GET /pacientes/<id>` cuando no lo hay; verificar que no se crea ninguna Reserva.
- [x] 3.3 Si faltan datos obligatorios, volver a mostrar el formulario con los valores ingresados y el mensaje de qué falta; verificar que no se crea el Paciente.
- [x] 3.4 Si el RUT ya existe, usar el registro existente y retomar la reserva sin duplicar; verificar que el total de Pacientes no cambia y que la redirección conserva el bloque y el RUT.
- [x] 3.5 Crear `GET /pacientes/{paciente_id}` con la plantilla `registro_confirmado.html` para el registro sin bloque seleccionado; verificar que responde 200 y muestra el nombre y el RUT.
- [x] 3.6 Aceptar el parámetro `rut` en `GET /reservar/{bloque_id}` y pasarlo a la plantilla para precargar el campo; verificar con una prueba que el valor aparece en el formulario.
- [x] 3.7 Incluir el router de pacientes en `app/main.py`; verificar que la aplicación arranca y que las rutas de HU-01 y HU-02 siguen respondiendo.

## 4. Pruebas Gherkin

- [x] 4.1 Crear `tests/test_hu02a_registro_paciente.py` con la prueba «HU-02A · Un paciente nuevo se registra desde la reserva», que verifica el registro, la redirección con el RUT y que al confirmar la reserva esta queda en "Pendiente de confirmación"; ejecutar y ver que pasa.
- [x] 4.2 Agregar la prueba «HU-02A · El paciente no completa los datos obligatorios», que verifica que no se registra y que se informa el dato faltante; ejecutar y ver que pasa.
- [x] 4.3 Agregar la prueba «HU-02A · El RUT ya está registrado», que verifica que no se duplica el Paciente y que se utiliza el registro existente; ejecutar y ver que pasa.
- [x] 4.4 Ejecutar `pytest` completo y confirmar que las pruebas de HU-01, HU-02 y HU-02A pasan.

## 5. Documentación

- [x] 5.1 Actualizar `README.md` con el flujo de registro, la URL `/pacientes/registro`, la migración `002`, la dependencia con HU-02 y los pasos para probarlo; verificar que las instrucciones funcionan en una ejecución real.

## Workflow follow-up

- Revisar las especificaciones y el código generado con el estudiante antes de cerrar el cambio.
- Archivar el cambio con `openspec archive` cuando el estudiante valide el sistema.
- Actualizar `.cin324/proyecto.md` con el cambio `hu-02a-registrar-paciente`, la fecha y la nota de que el `TO-BE.png` debe re-exportarse.
