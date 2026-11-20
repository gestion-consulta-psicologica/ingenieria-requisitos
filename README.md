# Gestión de consulta psicológica

Aplicación web sencilla del curso **CIN 324 — Ingeniería de Requisitos**, generada desde la documentación del repositorio. Incluye **HU-01 — Consultar disponibilidad** (el paciente consulta los bloques horarios libres de una semana y, si no hay horas, el sistema informa la próxima fecha disponible), **HU-02 — Reservar una hora** (el paciente reserva un bloque disponible, recibe un aviso por correo electrónico y el bloque deja de mostrarse como disponible), **HU-02A — Registrar datos del paciente** (un paciente nuevo se registra desde el flujo de reserva y retoma el bloque seleccionado), **HU-03 — Confirmar o cancelar una hora** (el paciente recibe la solicitud y el recordatorio por correo electrónico, responde desde la plataforma o desde enlaces seguros de un solo uso y, si no responde, el planificador registra un cargo de $5.000), **HU-04 — Reagendar o cancelar una hora** (el paciente cancela una reserva confirmada o la cambia por un bloque libre de los próximos 14 días, con historial de cambios y un nuevo ciclo de confirmación) y **HU-05 — Comprobar el pago** (la psicóloga consulta la información del pago de una atención, sus comprobantes y las atenciones con pago pendiente, sin modificar el estado).

## Requisitos

- Python 3.11 o superior (probado con Python 3.12).
- SQLite (incluido con Python).
- Git.
- OpenSpec es opcional para ejecutar la aplicación; se usa para gestionar las especificaciones del cambio.

## Instalación

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si `python` no se reconoce en la terminal, usa el ejecutable instalado o el Python del entorno virtual:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, puedes usar directamente `.\.venv\Scripts\python.exe` en los comandos siguientes.

## Datos de ejemplo

```powershell
python -m app.db.seed
```

El comando crea `data/app.db` (si no existe), aplica las migraciones `001` a `007` y carga datos de ejemplo de forma idempotente:

- Psicóloga **Ana Pérez**.
- Paciente de ejemplo **Paciente de Ejemplo**, RUT **22.222.222-2** (sirve para reservar).
- Semana del **9 de noviembre de 2026**:
  - martes 10 a las 10:00: reserva vigente en estado **Pendiente de confirmación** (no debe mostrarse).
  - martes 10 a las 11:00: bloque libre (debe mostrarse).
- Semana del **16 de noviembre de 2026**:
  - martes 17 a las 10:00: reserva vigente en estado **Confirmada** (no debe mostrarse).
  - martes 24 a las 10:00: próximo bloque libre, en modalidad online.
- Atenciones para **HU-05** (jueves 12 de noviembre de 2026):
  - 16:00: atención de **Paciente de Ejemplo** con pago pendiente y un comprobante de $30.000.
  - 17:00: atención de **Paciente Sin Comprobante** con pago pendiente y sin comprobante.
- Para **HU-05A**, al iniciar con el planificador activo la reserva confirmada del martes 17 a las 10:00 origina automáticamente una atención en estado `programada` y un pago en estado `Pendiente` con el monto configurable (por defecto **$30.000**). Esa atención aparece como tercera fila en `/pagos`.

Ejecutar el seed varias veces no duplica los datos.

Las migraciones se aplican automáticamente al arrancar la aplicación o el seed. La migración `002` deja `correo` opcional para que un paciente pueda registrarse solo con teléfono. La migración `003` agrega `solicitud_confirmacion` y `cargo`; la `004` agrega `estado`, `fecha_cierre` y el índice único de solicitud pendiente; la `005` agrega `correo_pendiente` y `token_confirmacion`; la `006` agrega `reserva.version`, reconstruye las solicitudes con unicidad por `(reserva_id, version, tipo)` y crea `reserva_historial` para HU-04; la `007` agrega `atencion`, `pago` y `comprobante_transferencia` para HU-05. La `007` no modifica las tablas de reservas, pacientes o bloques. Si quieres empezar de cero, elimina `data/app.db` y vuelve a ejecutar el seed.

## Configuración del correo electrónico

El envío real usa SMTP. Configura las variables en la terminal antes de iniciar la aplicación; **no** guardes credenciales en el repositorio:

```powershell
$env:SMTP_HOST = "smtp.example.com"
$env:SMTP_PORT = "587"
$env:SMTP_USUARIO = "tu-usuario"
$env:SMTP_CLAVE = "tu-clave-de-aplicacion"
$env:SMTP_REMITENTE = "consultas@example.com"
$env:SMTP_SEGURIDAD = "starttls"
$env:CORREO_URL_PUBLICA = "http://localhost:8000"
```

- `SMTP_SEGURIDAD` acepta `starttls`, `ssl` o `ninguna`.
- `CORREO_URL_PUBLICA` debe ser una URL accesible desde el dispositivo del paciente, porque se usa para armar los enlaces de confirmación.
- `PLANIFICADOR_ACTIVO=0` desactiva el planificador para pruebas manuales controladas.
- `MONTO_ATENCION_CLP` define el monto de las atenciones nuevas y usa **30000** por defecto. La creación automática de la atención y su pago depende de que el planificador esté activo.
- `CONFIRMACION_HORA_VISPERA` (por defecto `09:00`) y `CONFIRMACION_HORA_RECORDATORIO` (por defecto `08:00`) son configurables; **aún no están confirmadas por el cliente**.
- La zona horaria por defecto es `America/Santiago`.
- Si el correo no está configurado, la aplicación funciona, pero los correos quedan en la cola como pendientes con el motivo y **nunca** se marca un envío como exitoso.

## Ejecutar la aplicación

Con el entorno virtual activado:

```powershell
uvicorn app.asgi:app --reload
```

También puedes ejecutarlo sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.asgi:app --reload
```

Abre <http://localhost:8000/disponibilidad>.

Para HU-05 abre <http://localhost:8000/pagos>.

Para HU-05A, entra al detalle de una reserva confirmada con atención y pago pendiente, por ejemplo <http://localhost:8000/reservas/2>, y usa el enlace **Registrar comprobante de pago**. También puedes abrir directamente <http://localhost:8000/pagos/{atencion_id}/comprobante>.

La raíz <http://localhost:8000/> redirige a la consulta de disponibilidad.

## Base de datos y respaldo

- `data/app.db` no se versiona; las migraciones `005`, `006` y `007` se aplican al arrancar o en una base temporal, nunca sobre `data/app.db` durante el desarrollo.
- **No existe una copia de seguridad previa a la migración `004`.** No se debe asumir que existe ni crearla de forma ficticia.
- `pytest` usa una base SQLite temporal aislada y no modifica `data/app.db`.
- Para pruebas manuales de HU-03 se debe usar exclusivamente `data/manual-hu03.db` mediante la variable `CONSULTA_DB`.
- Para HU-04 usa una copia aislada (por ejemplo `data/manual-hu04.db`) o una base recién sembrada con `CONSULTA_DB`; no modifiques `data/app.db`.
- Para HU-05 usa una base aislada (por ejemplo `data/manual-hu05.db`) o una base recién sembrada con `CONSULTA_DB`; no modifiques `data/app.db`.
- Para HU-05A usa una base aislada (por ejemplo `data/manual-hu05a.db`) o una base recién sembrada con `CONSULTA_DB`; no modifiques `data/app.db`.
- Si la base original no tiene solicitudes, el planificador no la modifica al arrancar; aun así, usa una base aislada para probar envíos.
- Antes de una migración futura, detén la aplicación y crea una copia consistente de la base real.

## Recorrido manual de HU-01

1. Abre <http://localhost:8000/disponibilidad?semana=2026-11-09>.
   - Debes ver el bloque del **martes 10 de noviembre a las 11:00** como disponible.
   - **No** debe aparecer el bloque de las 10:00, porque tiene una reserva vigente.
2. Abre <http://localhost:8000/disponibilidad?semana=2026-11-16>.
   - Debes ver el mensaje **«No hay horas disponibles para esa semana.»**
   - Debes ver que la fecha del próximo bloque disponible es el **24 de noviembre de 2026**.
3. Cambia la fecha del formulario y pulsa **Consultar** para repetir la consulta con otra semana.

El selector de rol de la cabecera es **solo de demostración**: no hay autenticación real. En esta historia se usa el rol **Paciente**.

## Recorrido manual de HU-02

1. Abre <http://localhost:8000/disponibilidad?semana=2026-11-09> y pulsa **Reservar** en el bloque del **martes 10 de noviembre a las 11:00**.
   - Debes ver el formulario con el bloque seleccionado y el campo **RUT del paciente**.
2. Ingresa el RUT **22.222.222-2** y pulsa **Confirmar reserva**.
   - Debes ver la reserva en estado **Pendiente de confirmación**.
   - El aviso de reserva registrada queda en la cola de correos; si el paciente no tiene correo, aparece como **omitido**.
   - Con SMTP configurado, el planificador lo envía y el detalle muestra el estado **Enviado**.
3. Vuelve a <http://localhost:8000/disponibilidad?semana=2026-11-09>.
   - El bloque del martes 10 a las 11:00 **ya no debe aparecer** como disponible.
4. Para probar el bloque ya tomado, abre directamente <http://localhost:8000/reservar/1> (el bloque del martes 10 a las 10:00 ya tiene una reserva vigente) e intenta reservarlo con el RUT **22.222.222-2**.
   - Debes ver **«El bloque ya no está disponible.»** y la lista de bloques cercanos.
5. Para probar el RUT no registrado, reserva un bloque con el RUT **99.999.999-9**.
   - El sistema no registra la reserva y redirige a `/pacientes/registro?bloque_id=...`, donde puedes completar el registro (ver el recorrido de HU-02A).

El aviso de reserva se envía por **correo electrónico real** mediante SMTP. Sin configuración SMTP queda pendiente en la cola, no se marca como enviado y el detalle lo informa.

## Recorrido manual de HU-02A

1. Con una base recién sembrada, abre <http://localhost:8000/reservar/4> (martes 24 de noviembre a las 10:00, modalidad online) e intenta reservar con el RUT **99.999.999-9**.
   - Debes llegar a `/pacientes/registro?bloque_id=4` con el formulario de registro.
2. Completa **nombre completo** y **RUT**, deja el **teléfono** con un valor y el **correo** vacío; pulsa **Guardar datos**.
   - Debes volver a `/reservar/4?rut=999999999` con el RUT precargado.
   - En la base, el paciente queda con `correo` nulo; se permite registrarse solo con teléfono.
3. Pulsa **Confirmar reserva**.
   - La reserva queda en estado **Pendiente de confirmación**.
4. Para probar los datos obligatorios, abre <http://localhost:8000/pacientes/registro> y guarda sin nombre o sin teléfono ni correo.
   - Debes ver **«Falta completar: …»** y el paciente no se registra.
5. Para probar el RUT ya registrado, abre `/pacientes/registro` y usa el RUT **22.222.222-2** con otro nombre; puedes dejar teléfono y correo vacíos.
   - Debes volver a la confirmación del paciente existente (o a la reserva, si venías con un bloque).
   - No se crea un segundo paciente con ese RUT.
6. Abre <http://localhost:8000/pacientes/registro> sin `bloque_id`, completa los datos y guarda.
   - Debes ver la página **Registro completado** con el nombre y el RUT.

## Recorrido manual de HU-03

Usa una base aislada y un correo de prueba; **no** uses direcciones de pacientes reales. Con una base recién sembrada, la reserva **1** queda en estado **Pendiente de confirmación** (martes 10 de noviembre a las 10:00).

1. Configura SMTP y `CORREO_URL_PUBLICA` como se indica arriba. Para una prueba controlada puedes usar `PLANIFICADOR_ACTIVO=0` y ejecutar el planificador desde una consola o desde las pruebas.
2. Abre <http://localhost:8000/reservas/1>.
   - Debes ver el estado, los hitos programados (víspera, recordatorio, vencimiento) y el estado del SMTP y del planificador.
   - Las acciones **Confirmar asistencia** y **No asistiré** no aparecen mientras no exista una solicitud pendiente.
   - Ya no existe el panel de simulación.
3. En la víspera, el planificador registra la solicitud, crea los enlaces de un solo uso y encola el correo.
   - El detalle muestra la solicitud **pendiente** y el correo en estado **Pendiente**, **Enviado** o **Fallido** según el resultado real de SMTP.
   - Aparecen las acciones de respuesta; la respuesta se asociará a la solicitud pendiente.
4. En la mañana, el planificador envía el recordatorio.
   - La solicitud de víspera pasa a **reemplazada** con su fecha de cierre y su correo pendiente queda **cancelado**.
   - El recordatorio queda como la única solicitud **pendiente**; sus enlaces son los válidos.
5. Responde desde la plataforma o desde el enlace del correo:
   - **Confirmar asistencia**: la reserva pasa a **Confirmada** y la solicitud pendiente más reciente queda **respondida**, con respuesta **confirma** y su fecha de respuesta.
   - **No asistiré**: la reserva pasa a **Cancelada**, la solicitud pendiente más reciente queda **respondida**, con respuesta **no asistirá** y su fecha de respuesta, y el bloque vuelve a aparecer en `/disponibilidad?semana=2026-11-09`.
   - El enlace usado queda marcado como utilizado; un segundo intento devuelve **HTTP 409** y no cambia la respuesta.
6. Si el paciente no responde y llega la hora de la atención con una solicitud pendiente:
   - La reserva pasa a **Sin confirmar**, la solicitud queda **vencida** con respuesta **sin respuesta** y fecha de cierre (sin fecha de respuesta del paciente).
   - Se crea el **Cargo de $5.000** con motivo **sin confirmar** asociado al paciente y a la reserva, y se encola su aviso por correo.
7. Para probar los errores, intenta responder una reserva que ya no está pendiente, responder sin una solicitud pendiente o reutilizar un enlace.
   - Debes ver **HTTP 409** con un mensaje claro y sin cambios en la reserva, las solicitudes, los cargos ni los tokens.
   - Una solicitud **respondida**, **reemplazada** o **vencida** no puede recibir otra respuesta; sin solicitud pendiente no se muestran las acciones de respuesta.
   - Solo puede existir una solicitud **pendiente** por reserva; la base de datos lo impide con una restricción de integridad.

Los correos se envían **realmente** por SMTP. Si el servidor falla, el trabajo se reintenta con espera exponencial; si las credenciales son rechazadas queda **fallido**; si no hay configuración queda **pendiente** con el motivo. Nunca se registra un éxito ficticio. Si el proceso estuvo detenido y la reserva nunca recibió una solicitud, no se vence automáticamente: requiere revisión manual.

## Recorrido manual de HU-04

Usa una copia aislada y un correo de prueba; **no** modifiques `data/app.db`. Por ejemplo:

```powershell
Copy-Item data\app.db data\manual-hu04.db
$env:CONSULTA_DB = "$PWD\data\manual-hu04.db"
```

La reserva **2** queda en estado **Confirmada** (martes 17 de noviembre de 2026 a las 10:00). El bloque del martes 24 a las 10:00 es una alternativa dentro de los próximos 14 días.

1. Abre <http://localhost:8000/reservas/2>.
   - Debes ver **Reagendar hora** y **Cancelar reserva**.
2. Pulsa **Reagendar hora** y abre <http://localhost:8000/reservas/2/reagendar>.
   - Debes ver el bloque del **martes 24 de noviembre a las 10:00** como alternativa.
   - La reserva original sigue **Confirmada** mientras no elijas una alternativa.
3. Selecciona el bloque del martes 24 a las 10:00 y confirma.
   - La reserva **2** queda en **Pendiente de confirmación**, asociada al nuevo bloque.
   - El bloque del martes 17 a las 10:00 vuelve a aparecer en `/disponibilidad?semana=2026-11-16`.
   - El detalle muestra el historial con el bloque anterior y el nuevo bloque.
   - El aviso de reserva reagendada queda en la cola de correos.
4. Para probar la cancelación, vuelve a crear `data/manual-hu04.db` desde `data/app.db` y abre `/reservas/2`.
   - Pulsa **Cancelar reserva** y confirma.
   - La reserva queda **Cancelada**, el bloque del martes 17 a las 10:00 se libera y el historial registra la cancelación.
5. Para probar el rechazo, abre `/reservas/2/reagendar` sobre una reserva que ya no está **Confirmada** o elige un bloque que otro paciente tomó en el intervalo.
   - Debes ver **HTTP 409** con un mensaje claro y sin cambios en la reserva original.

No hay autenticación real; `/reservas/{id}` sigue siendo el acceso de demostración. La cancelación de una reserva **Pendiente de confirmación** no pertenece a HU-04: se responde con «no asistiré» en HU-03.

## Recorrido manual de HU-05

Usa una base aislada o una recién sembrada; **no** modifiques `data/app.db`. Por ejemplo:

```powershell
$env:CONSULTA_DB = "$PWD\data\manual-hu05.db"
python -m app.db.seed
```

1. Abre <http://localhost:8000/pagos>.
   - Debes ver dos atenciones con pago pendiente: **Paciente de Ejemplo** (jueves 12 a las 16:00) y **Paciente Sin Comprobante** (jueves 12 a las 17:00).
2. Abre <http://localhost:8000/pagos/1> (atención de Paciente de Ejemplo).
   - Debes ver el nombre, el RUT **22.222.222-2**, el monto de la atención **$30.000**, el monto pagado **$0** y el estado **Pendiente**.
   - Debes ver el comprobante por **$30.000**, con fecha de transferencia **2026-11-10** y cuenta de destino **Cuenta de ejemplo**.
   - La opción **Registrar estado de pago** aparece visible, pero inactiva.
3. Abre <http://localhost:8000/pagos/2> (atención de Paciente Sin Comprobante).
   - Debes ver **«La atención no tiene comprobante de pago.»**
   - La atención sigue apareciendo en el listado de `/pagos`.
4. Abre <http://localhost:8000/pagos/999>.
   - Debes ver **HTTP 404** con **«No se encontró la atención o no tiene un pago asociado.»**
5. Recarga <http://localhost:8000/pagos/1>.
   - El estado del pago sigue en **Pendiente** y el comprobante no cambia: HU-05 es de solo lectura y no produce transiciones de EST-02.

## Recorrido manual de HU-05A

Usa una base aislada y deja el planificador activo (es el valor por defecto):

```powershell
$env:CONSULTA_DB = "$PWD\data\manual-hu05a.db"
python -m app.db.seed
uvicorn app.asgi:app --reload
```

1. Abre <http://localhost:8000/pagos>.
   - Debes ver una tercera atención de **Paciente de Ejemplo** para el martes 17 a las 10:00, con pago **Pendiente**. Fue creada automáticamente por el planificador.
2. Abre <http://localhost:8000/reservas/2>.
   - Debes ver el enlace **Registrar comprobante de pago**.
3. Pulsa el enlace y registra un monto, una fecha de transferencia y una cuenta de destino.
   - Debes ver **«El comprobante quedó registrado»** y el comprobante en la lista.
4. Registra un segundo comprobante para la misma atención.
   - Deben aparecer ambos comprobantes y el pago debe seguir en **Pendiente**.
5. Intenta guardar sin monto, sin fecha o sin cuenta, o con un monto en cero.
   - Debes ver **HTTP 400** con el dato faltante o inválido, sin un nuevo comprobante.
6. Abre <http://localhost:8000/pagos/3> o el listado `/pagos`.
   - El comprobante debe estar disponible para la comprobación de la psicóloga.
7. Para el caso de pago ya pagado, no hay pantalla de HU-06 todavía; el rechazo se verifica con la suite automática (`test_pago_ya_pagado_no_permite_registrar_comprobante` y `test_ruta_responde_409_si_el_pago_ya_esta_pagado`).

## Pruebas

```powershell
pytest
```

o, sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Las pruebas cubren:

- `HU-01 · El paciente consulta una semana con bloques horarios libres`.
- `HU-01 · El paciente consulta una semana sin bloques horarios libres`.
- La regla de vigencia de EST-01 (Pendiente de confirmación y Confirmada bloquean; Cancelada y Sin confirmar no).
- El cálculo del próximo bloque disponible cuando no hay alternativas.
- La redirección de `/` a `/disponibilidad` y la consulta sin parámetro de semana.
- `HU-02 · El paciente reserva un bloque horario disponible`.
- `HU-02 · Otro paciente reservó el mismo bloque horario antes`.
- `HU-02 · El paciente no está registrado en el sistema`.
- La búsqueda de pacientes por RUT normalizado, el registro de la reserva y el aviso de reserva en la cola de correos.
- `HU-02A · Un paciente nuevo se registra desde la reserva`.
- `HU-02A · El paciente no completa los datos obligatorios`.
- `HU-02A · El RUT ya está registrado`.
- La migración `002` (correo opcional y RUT único normalizado), la validación de datos y la reutilización del paciente por RUT.
- El retorno a `/reservar/{bloque_id}?rut=...` con el RUT precargado y la confirmación sin bloque seleccionado.
- `HU-03 · El sistema envía la solicitud de confirmación y el recordatorio`.
- `HU-03 · El paciente confirma su asistencia`.
- `HU-03 · El paciente cancela su hora al responder la confirmación`.
- `HU-03 · El paciente no responde la confirmación`.
- `HU-03 · El recordatorio reemplaza la solicitud anterior`, la aparición de acciones solo con una solicitud pendiente y el rechazo de respuestas sobre solicitudes cerradas.
- `HU-03 · Se repite el envío de una solicitud`, la secuencia inválida, los enlaces usados o vencidos y las respuestas sin solicitud pendiente o sobre una reserva que ya no está pendiente (HTTP 409).
- La migración `003` (tablas `solicitud_confirmacion` y `cargo`, restricciones de unicidad).
- La migración `004` (estado y fecha de cierre, backfill determinista, preflight de datos ambiguos, restricciones de estado e índice único de solicitud pendiente).
- La migración `005` (`correo_pendiente`, `token_confirmacion`, idempotencia y tokens).
- La migración `006` (`reserva.version`, solicitudes por ciclo y `reserva_historial`), incluida la preservación de datos y la integridad referencial.
- `HU-04 · El paciente accede a las opciones de gestión`.
- `HU-04 · El paciente cancela una reserva`, con liberación del bloque, historial y rechazo desde una reserva pendiente.
- `HU-04 · El paciente solicita reagendar y existen alternativas`, excluyendo el bloque actual y los bloques ocupados.
- `HU-04 · El paciente solicita reagendar y no existen alternativas`, conservando la reserva original.
- `HU-04 · El paciente elige una alternativa disponible`, actualizando la misma reserva, liberando el bloque anterior, registrando historial, encolando el aviso y reiniciando el ciclo de confirmación.
- `HU-04 · La alternativa elegida fue tomada por otro paciente`, con reversión total y reserva original intacta.
- Las rutas y pantallas de reagendamiento y cancelación, incluido el historial y el nuevo ciclo de solicitudes.
- `HU-05 · La atención tiene un comprobante de pago registrado`.
- `HU-05 · La atención no tiene comprobante de pago`.
- `HU-05 · La psicóloga revisa la información y continúa al registro`.
- `HU-05A · La reserva confirmada llega a la hora de la atención`.
- `HU-05A · El sistema no duplica una atención ya originada`.
- `HU-05A · El paciente registra el comprobante de su transferencia`.
- `HU-05A · El paciente registra un segundo comprobante`.
- `HU-05A · El paciente no completa los datos obligatorios del comprobante`.
- `HU-05A · El comprobante tiene datos inválidos`.
- `HU-05A · La atención no tiene pago asociado`.
- `HU-05A · El pago ya está pagado`.
- La migración `007` (`atencion`, `pago`, `comprobante_transferencia`), la idempotencia del seed y la consulta de solo lectura.
- Las rutas `/pagos` y `/pagos/{atencion_id}`, incluido el 404 y el listado de atenciones con pago pendiente.
- La creación automática e idempotente de la atención y el pago, el monto configurable, la ruta `/pagos/{atencion_id}/comprobante` y el enlace en el detalle de la reserva.
- El envío real con un servidor SMTP falso local: éxito, error de conexión y reintento, credenciales rechazadas, SMTP no configurado, recuperación tras reinicio, duplicados e integridad.
- El planificador automático, el reemplazo de solicitudes, el vencimiento con cargo y el estado de los correos en la pantalla.
- El aislamiento de pytest: la base por defecto de las pruebas es temporal, el planificador está desactivado y no se modifica `data/app.db`.

Resultado actual: **115 pruebas pasan** (93 existentes + 22 de HU-05A).

## Estructura

```text
app/
  main.py                  # fábrica de la aplicación y filtros de fechas
  asgi.py                  # instancia ASGI app = crear_app()
  db/
    conexion.py            # SQLite y migraciones
    migrations/            # migraciones SQL numeradas
    seed.py                # datos de ejemplo idempotentes
  configuracion.py         # variables de entorno de SMTP, planificador, horas y monto de atención
  tiempo.py                # zona America/Santiago y conversiones UTC/local
  servicios/
    disponibilidad.py      # lógica de consulta y regla de vigencia
    paciente.py            # validación y registro de pacientes
    reserva.py             # búsqueda de paciente, registro de reserva y consulta
    confirmacion.py        # solicitudes, respuestas, tokens y cargo de HU-03
    reagendamiento.py      # cancelación, alternativas, reagendamiento e historial de HU-04
    pagos.py               # consulta de solo lectura de atención, pago y comprobantes de HU-05
    atenciones.py          # origen automático de atención/pago y registro de comprobantes de HU-05A
    notificaciones.py      # encolado del aviso de reserva
    cola_correo.py         # cola persistente e idempotencia
    correo.py              # adaptador SMTP y errores tipados
    plantillas_correo.py   # texto y HTML de los correos
    tokens.py              # tokens de un solo uso (hash, expiración)
    planificador.py        # eventos temporales y envío de la cola
  rutas/
    disponibilidad.py      # GET /disponibilidad
    paciente.py            # GET/POST /pacientes/registro y GET /pacientes/{id}
    reserva.py             # reserva, detalle, respuesta por plataforma o token
    pagos.py               # GET /pagos, GET /pagos/{atencion_id} y GET/POST /pagos/{atencion_id}/comprobante
  templates/
    disponibilidad.html    # pantalla de consulta
    registro_paciente.html # formulario de registro
    registro_confirmado.html # confirmación del registro
    reserva.html           # formulario de reserva
    reserva_confirmada.html # detalle, correos, solicitudes, historial y cargo
    reagendar.html         # alternativas de reagendamiento
    pagos.html             # listado de atenciones con pago pendiente
    pago_detalle.html      # detalle del pago y sus comprobantes
    pago_comprobante.html  # formulario del paciente para registrar el comprobante
    respuesta_token.html   # confirmación desde el enlace del correo
tests/
  conftest.py              # fixtures y aislamiento de la base de pruebas
  smtp_falso.py            # servidor SMTP local para pruebas
  test_aislamiento.py
  test_hu01_disponibilidad.py
  test_hu02_reserva.py
  test_hu02a_registro_paciente.py
  test_hu03_confirmacion.py
  test_hu03_correo.py
  test_hu03_migracion.py
  test_hu04_reagendamiento.py
  test_hu05_comprobar_pago.py
  test_hu05a_atencion_comprobante.py
data/app.db                # base local (se crea con el seed)
```

## Limitaciones de seguridad del prototipo

Este prototipo es una entrega académica y **no implementa controles de seguridad para producción**. Las limitaciones conocidas son:

- **Sin autenticación ni autorización:** no hay inicio de sesión ni permisos por rol; cualquier persona con la URL puede acceder a las pantallas y acciones disponibles.
- **Acceso de demostración por identificadores secuenciales:** rutas como `/reservas/{id}` y `/pagos/{id}` permiten abrir reservas y pagos mediante un ID predecible, sin comprobar que pertenezcan al usuario.
- **RUT expuesto en rutas y vistas:** el RUT se muestra o se transporta en formularios, redirecciones, parámetros y pantallas de pago, por ejemplo `/reservar/{bloque_id}?rut=...` o `/pagos/{atencion_id}`.
- **Formularios POST sin protección CSRF:** las operaciones de reserva, registro y confirmación no incluyen token CSRF.
- **Tokens en la URL del correo:** los enlaces de confirmación viajan en la URL; la base guarda solo su hash y son de un solo uso, pero el correo es un canal externo que puede reenviarse.
- **Correo sin cifrado en el repositorio:** las credenciales SMTP se leen del entorno y no se versionan; aun así, el prototipo no implementa gestión de secretos ni rotación.
- **Planificador en el proceso web:** el planificador corre dentro de la aplicación; en producción conviene separarlo en un worker y usar un broker o bloqueo distribuido.
- **Datos personales en correos:** los mensajes incluyen nombre, fecha, hora y número de reserva; no incluyen información clínica. El paciente debe usar una dirección que autorice.

Estas limitaciones afectan el cumplimiento de **RP-17** (confidencialidad de la información), **RD-01** (autenticación y permisos por rol) y **RD-02** (cifrado de información sensible). **La documentación de estas limitaciones no implica que RP-17, RD-01 o RD-02 estén implementados.**

No debe utilizarse este prototipo con información clínica o personal real en un entorno de producción. Antes de producción se requiere implementar autenticación, autorización por roles, protección CSRF, protección de datos personales y controles de acceso adecuados.

## Fuera de alcance

- Editar o eliminar los datos de un paciente ya registrado, y validar el dígito verificador del RUT.
- **HU-05A y HU-06 a HU-09**: registro automático de la atención y del comprobante, registro del estado de pago, boletas, registro de asistencia y ficha clínica.
- Autenticación real (el selector de rol es de demostración) y requisitos no funcionales.
- WhatsApp real; el canal implementado es correo electrónico por SMTP.
- Envío de correos a pacientes reales en pruebas; se usa un correo de prueba y un servidor SMTP falso.
- Confirmar las horas exactas de envío de la víspera y del recordatorio (hoy configurables con valores iniciales).
