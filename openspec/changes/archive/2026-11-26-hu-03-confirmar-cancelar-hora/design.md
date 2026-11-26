# Design — HU-03 Confirmar o cancelar una hora

## Context

Ver `proposal.md` — Why. La aplicación ya registra Reservas en estado «Pendiente de confirmación» (HU-02), libera el bloque al cancelar y deja la reserva visible en `/reservas/{id}`. `reserva.estado` ya admite los cuatro estados de EST-01. La implementación anterior usaba `ServicioMensajeriaSimulado` y un panel «Simulación de tiempo»; esta etapa los reemplaza por correo real, cola persistente, planificador y tokens de un solo uso.

La ficha `.cin324/historias/HU-03.md`, el modelo de dominio, EST-01, DSS-01 y el BPMN deben quedar actualizados con el envío por correo, los enlaces seguros y la distinción entre `fechaRespuesta` y `fechaCierre`.

## Goals / Non-Goals

**Goals:**
- Enviar correo real por SMTP sin acoplar la lógica de negocio al proveedor.
- No perder ni duplicar envíos: cola persistente, idempotencia y reintentos.
- Recuperar el trabajo pendiente tras un reinicio del proceso.
- Enviar en los momentos definidos (víspera, mañana y hora de la atención) con zona `America/Santiago`.
- Permitir respuestas desde enlaces de correo de un solo uso, además de la plataforma.
- No registrar como exitoso ningún envío que no haya sido aceptado por SMTP.
- Mantener una sola solicitud pendiente y un solo cargo por reserva.

**Non-Goals:**
- WhatsApp real.
- Procesar pagos, comprobantes o boletas (HU-05 a HU-07).
- Cancelación o reagendamiento posterior (HU-04).
- Autenticación, autorización por roles o cifrado de la base.
- Guardar credenciales SMTP en el repositorio o en la base de datos.

## Decisions

### 1. Configuración por entorno

`app/configuracion.py` define `ConfiguracionCorreo` y `cargar_configuracion()`. Las credenciales y la URL pública se leen solo de variables de entorno; el repositorio no contiene secretos.

| Variable | Uso | Valor por defecto |
|---|---|---|
| `SMTP_HOST` | Servidor SMTP | — (obligatorio para enviar) |
| `SMTP_PORT` | Puerto | `587` |
| `SMTP_USUARIO` / `SMTP_CLAVE` | Autenticación | — (opcional, juntas) |
| `SMTP_REMITENTE` | Remitente | — (obligatorio para enviar) |
| `SMTP_SEGURIDAD` | `starttls`, `ssl` o `ninguna` | `starttls` |
| `SMTP_TIMEOUT` | Timeout de conexión, segundos | `10` |
| `CORREO_URL_PUBLICA` | Base de los enlaces del correo | `http://localhost:8000` |
| `CORREO_MAX_INTENTOS` | Intentos por correo | `5` |
| `CORREO_REINTENTO_BASE_SEGUNDOS` | Base del backoff | `60` |
| `PLANIFICADOR_ACTIVO` | Activa el planificador | `true` |
| `PLANIFICADOR_INTERVALO_SEGUNDOS` | Intervalo entre ciclos | `60` |
| `PLANIFICADOR_TIMEOUT_ENVIO_SEGUNDOS` | Antigüedad para recuperar `enviando` | `300` |
| `CONFIRMACION_HORA_VISPERA` | Hora del envío de víspera | `09:00` |
| `CONFIRMACION_HORA_RECORDATORIO` | Hora del recordatorio | `08:00` |
| `ZONA_HORARIA` | Zona de cálculo y presentación | `America/Santiago` |

**Decisión pendiente:** los documentos de requisitos no definen las horas exactas de envío. `09:00` y `08:00` son valores iniciales configurables y deben confirmarse con el estudiante/cliente. No se presentan como una regla aprobada.

### 2. Adaptador SMTP y clasificación de errores

`app/servicios/correo.py` define el `Protocol` `ServicioCorreo` y `ServicioCorreoSMTP`:

- `configurado()` y `motivo_no_configurado()` permiten avisar en la UI sin intentar enviar.
- `enviar(destinatario, asunto, texto, html) -> str` devuelve el `Message-ID`.
- `ErrorAutenticacionSMTP` no se reintenta: las credenciales no se corrigen solas.
- `ErrorConexionSMTP` y `ErrorEnvioSMTP` se reintentan con espera exponencial.
- `CorreoNoConfigurado` deja el trabajo en `pendiente` con el motivo; nunca se marca `enviado`.

Los mensajes se construyen con `EmailMessage` (texto y HTML alternativo) y `make_msgid`.

### 3. Cola persistente e idempotencia

`app/db/migrations/005_notificaciones_correo.sql` crea `correo_pendiente`:

- `clave_idempotencia UNIQUE` (`aviso_reserva:{id}`, `solicitud:{id}`, `cargo:{id}`).
- `tipo` (`aviso_reserva`, `solicitud_confirmacion`, `aviso_cargo`).
- `estado` (`pendiente`, `enviando`, `enviado`, `fallido`, `omitido`, `cancelado`).
- `intentos`, `max_intentos`, `proximo_intento`, `ultimo_error`, `id_mensaje`, marcas de tiempo.
- `destinatario` nulo ⇒ `omitido`; el CHECK impide `enviado` sin destinatario y fecha de envío.

`app/servicios/cola_correo.py` encapsula `encolar`, `reclamar_siguiente`, `marcar_enviado`, `marcar_reintento`, `marcar_fallido`, `recuperar_enviando`, `cancelar_pendientes_de_solicitud` y consultas de lectura. `reclamar_siguiente` usa `BEGIN IMMEDIATE` y un `UPDATE ... WHERE estado = 'pendiente'` para que dos workers no tomen el mismo correo.

Los correos se encolan en la **misma transacción** que crea la solicitud o el cargo. Si el paciente no tiene correo, el registro queda `omitido` con el motivo; no se simula un envío.

### 4. Planificador y recuperación

`app/servicios/planificador.py` ejecuta un ciclo cada `PLANIFICADOR_INTERVALO_SEGUNDOS`:

1. Recupera trabajos `enviando` más antiguos que el timeout y los vuelve `pendiente`.
2. Procesa reservas pendientes: envía víspera, recordatorio o cierra por vencimiento según la hora local.
3. Reclama y envía hasta 50 correos por ciclo.

El ciclo se ejecuta con `asyncio.to_thread` para no bloquear el event loop durante las conexiones SMTP. El lifespan de `crear_app` inicia y detiene el planificador. Los tests lo desactivan con `PLANIFICADOR_ACTIVO=0` y lo ejecutan manualmente con una hora inyectada.

Si el proceso estuvo detenido y no hay ninguna solicitud registrada, la reserva no se vence automáticamente: no se envió una solicitud y no corresponde cobrar sin haber consultado al paciente. Este caso queda para revisión manual y se documenta como limitación operativa. Si existe al menos una solicitud pendiente, el cierre por vencimiento sí se aplica.

### 5. Tokens de un solo uso

`token_confirmacion` guarda `token_hash` SHA-256, `accion` (`confirmar` / `cancelar`), `creado_en`, `expira_en` y `usado_en`. Los tokens en claro solo existen en el correo; la base no los almacena. `expira_en` es el inicio de la atención en la zona configurada.

`buscar_token` rechaza token inexistente (404), usado, vencido o cuya solicitud/reserva ya no admite respuesta (409). Al registrar la respuesta, el `UPDATE ... WHERE usado_en IS NULL` marca el token y la respuesta se guarda en la misma transacción. El token de la acción contraria deja de servir porque la solicitud ya no está pendiente.

Las rutas `GET /respuesta/confirmar/{token}` y `GET /respuesta/cancelar/{token}` muestran una página de confirmación; el `POST` ejecuta la acción. Así un escáner que solo hace `GET` no consume el enlace.

### 6. Servicio de confirmación

`app/servicios/confirmacion.py`:

- `enviar_solicitud(conexion, reserva_id, tipo, configuracion, ahora)`: valida reserva pendiente; para `recordatorio` exige la víspera; marca la solicitud pendiente anterior como `reemplazada` con `fechaCierre`, cancela su correo pendiente, inserta la nueva solicitud `pendiente`, crea dos tokens y encola el correo, todo en una transacción.
- `registrar_respuesta` / `registrar_respuesta_con_token`: validan reserva pendiente y solicitud pendiente más reciente; consumen el token si corresponde; actualizan la solicitud a `respondida` con `respuesta` y `fechaRespuesta`; actualizan la Reserva a `Confirmada` o `Cancelada`.
- `marcar_hora_sin_respuesta`: exige una solicitud pendiente; actualiza a `vencida` con `respuesta = sin respuesta`, `fechaRespuesta = NULL` y `fechaCierre` con la fecha y hora del bloque; deja la Reserva en `Sin confirmar`, registra el Cargo y encola el aviso, en una transacción.

Excepciones: `ReservaNoEncontrada`, `EstadoReservaInvalido`, `SolicitudPendienteNoDisponible`, `SecuenciaSimulacionInvalida` (recordatorio sin víspera), `SolicitudDuplicada`, `CargoDuplicado`.

### 7. Rutas y pantalla

- `POST /reservar/{bloque_id}` registra la reserva y encola el aviso de reserva.
- `GET /reservas/{id}` muestra estado, datos, hitos programados, acciones de respuesta solo con solicitud pendiente, estado de cada correo y estado del SMTP/planificador.
- `POST /reservas/{id}/confirmar` y `/no-asistir` responden desde la plataforma.
- `GET/POST /respuesta/{confirmar|cancelar}/{token}` responden desde el correo.
- 404 para reserva o token inexistente; 409 con mensaje claro para estado, secuencia o token inválido. En error no se modifican Reserva, Solicitudes, Cargos ni tokens.

Se elimina el panel de simulación y la ruta `/reservas/{id}/simular`.

### 8. Migración 005

Crea solo tablas nuevas e índices. No altera `reserva`, `paciente`, `bloque_horario`, `solicitud_confirmacion` ni `cargo`. La base original `data/app.db` no se migra en esta etapa; la migración se aplica al arrancar la aplicación o en bases temporales de prueba. Rollback: eliminar las tablas nuevas no afecta los datos de negocio; el código anterior seguiría funcionando con mensajería simulada.

### 9. Trazabilidad con los artefactos

- **Modelo de dominio:** `SolicitudConfirmacion` conserva `estado`, `fechaRespuesta` y `fechaCierre`; se documentan `Correo` y `TokenConfirmacion` como conceptos de soporte, no como entidades del negocio.
- **EST-01:** mismas transiciones de Reserva; se documentan los estados de la solicitud y de la cola de correo.
- **DSS-01:** se agregan el envío SMTP, la cola, los tokens y la respuesta por enlace.
- **BPMN:** se mantienen las actividades de envío automático, recordatorio, cancelación y cargo; el canal es correo electrónico.
- **RP-05, RP-06 y RP-22:** se mantiene la trazabilidad y se agrega la entrega real por correo.
- **B6/B7:** las imágenes exportadas deben corresponder a las fuentes actualizadas; las limitaciones de seguridad se documentan en README y `.cin324/proyecto.md`.

## Risks / Trade-offs

- **Credenciales SMTP comprometidas** → solo se leen de entorno; no se versionan; se documenta el uso de contraseñas de aplicación.
- **Enlaces con token en el correo** → tokens de un solo uso, hash en base y expiración; se documenta que el token viaja en la URL y que el correo es un canal externo.
- **Duplicados por reintentos** → clave de idempotencia y estados condicionados; un correo ya `enviado` no se vuelve a reclamar.
- **Fallo de SMTP** → reintentos con backoff; autenticación fallida no se reintenta; nunca se marca éxito sin aceptación del servidor.
- **Planificador bloqueante** → se ejecuta en un hilo aparte.
- **Horas de envío no definidas** → configurables y documentadas como decisión pendiente.
- **Sin correo registrado** → el trabajo queda `omitido`; la UI lo muestra, sin simular éxito.
- **Proceso detenido toda la víspera y la mañana** → no se vence una reserva sin solicitud previa; se documenta para revisión manual.
- **Datos históricos ambiguos en la migración 004** → se mantiene el preflight y la resolución manual.

## Migration Plan

1. Aplicar `005` al arrancar o en la base temporal de pruebas; verificar tablas e índices.
2. Configurar SMTP por variables de entorno fuera del repositorio.
3. Ejecutar la suite completa con el servidor SMTP falso.
4. Verificar en una base aislada el ciclo víspera → recordatorio → respuesta/vencimiento.
5. Rollback: detener el planificador, eliminar `correo_pendiente` y `token_confirmacion`; las tablas de negocio no se tocan.

## Open Questions

- Confirmar las horas de envío de la víspera y del recordatorio (hoy `09:00` y `08:00`, configurables).
- Confirmar el proveedor SMTP y la dirección remitente definitiva.
