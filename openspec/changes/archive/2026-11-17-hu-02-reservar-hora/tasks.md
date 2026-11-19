# Tasks — HU-02 Reservar una hora

## 1. Lógica de reserva

- [x] 1.1 Agregar `obtener_bloques_cercanos` al servicio de disponibilidad, reutilizando la consulta de bloques libres y ordenando por fecha y hora; verificar con una prueba unitaria que devuelve solo bloques libres y en orden.
- [x] 1.2 Implementar `buscar_paciente_por_rut` en `app/servicios/reserva.py` con normalización de RUT (sin puntos ni guion, K mayúscula); verificar con pruebas unitarias para RUT con formato, sin formato y no registrado.
- [x] 1.3 Implementar `registrar_reserva` en `app/servicios/reserva.py`: verifica que el bloque exista y esté libre, inserta la Reserva en "Pendiente de confirmación" y captura la violación de `idx_reserva_vigente`; verificar con pruebas de éxito y de bloque ya tomado.

## 2. Mensajería simulada

- [x] 2.1 Crear `app/servicios/mensajeria.py` con la interfaz `ServicioMensajeria` y `ServicioMensajeriaSimulado`, que registra el aviso con `logging` y devuelve éxito; verificar que una llamada no lanza excepción y deja el aviso en el log.
- [x] 2.2 Permitir inyectar el servicio en `crear_app(..., servicio_mensajeria=...)` y usarlo al registrar la reserva; verificar con un doble de prueba que recibe un aviso con paciente, bloque y reserva.

## 3. Rutas y pantallas

- [x] 3.1 Crear `GET /reservar/{bloque_id}` con `app/rutas/reserva.py` y la plantilla `reserva.html`, mostrando el bloque y el campo RUT; verificar con `TestClient` que responde 200 y muestra fecha, hora y modalidad.
- [x] 3.2 Crear `POST /reservar/{bloque_id}`: registra la reserva, envía el aviso y redirige `303` a `GET /reservas/{reserva_id}` con la plantilla `reserva_confirmada.html`; verificar con una prueba de integración que la reserva existe y se muestra la confirmación.
- [x] 3.3 Manejar el bloque tomado en `POST /reservar/{bloque_id}`: no registrar, mostrar «El bloque ya no está disponible» y listar los bloques cercanos; verificar con una prueba que no aumenta el número de reservas.
- [x] 3.4 Manejar el RUT no registrado: no registrar y redirigir `303` a `/pacientes/registro?bloque_id=<id>`; verificar con una prueba que no se creó la reserva y que la redirección conserva el bloque.
- [x] 3.5 Agregar el enlace «Reservar» por cada bloque en `app/templates/disponibilidad.html`; verificar con una prueba que cada bloque disponible enlaza a `/reservar/<id>`.

## 4. Pruebas Gherkin

- [x] 4.1 Crear `tests/test_hu02_reserva.py` con la prueba «HU-02 · El paciente reserva un bloque horario disponible», que verifica estado "Pendiente de confirmación", desaparición del bloque en `/disponibilidad` y aviso enviado; ejecutar y ver que pasa.
- [x] 4.2 Agregar la prueba «HU-02 · Otro paciente reservó el mismo bloque horario antes», que verifica el rechazo, la ausencia de una segunda reserva y los bloques cercanos informados; ejecutar y ver que pasa.
- [x] 4.3 Agregar la prueba «HU-02 · El paciente no está registrado en el sistema», que verifica que no se crea la reserva y la derivación a `/pacientes/registro` (el retorno a la reserva se prueba en HU-02A); ejecutar y ver que pasa.
- [x] 4.4 Ejecutar `pytest` completo y confirmar que las pruebas de HU-01 y HU-02 pasan.

## 5. Documentación

- [x] 5.1 Actualizar `README.md` con el flujo de reserva, la URL `/reservar/<bloque_id>` y cómo ejecutar las pruebas; verificar que las instrucciones funcionan en una ejecución real.

## Workflow follow-up

- Revisar las especificaciones y el código generado con el estudiante antes de cerrar el cambio.
- Archivar el cambio con `openspec archive` cuando el estudiante valide el sistema.
- Actualizar `.cin324/proyecto.md` con el cambio `hu-02-reservar-hora`, la fecha y la nota de que la derivación y el retorno se completan en HU-02A.
