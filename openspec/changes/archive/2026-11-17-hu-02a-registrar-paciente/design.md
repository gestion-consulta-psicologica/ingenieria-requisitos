# Design — HU-02A Registrar datos del paciente

## Context

La aplicación ya tiene HU-01 (consulta de disponibilidad) y HU-02 (reserva) sobre FastAPI + Jinja2 + SQLite. HU-02 deriva a `/pacientes/registro?bloque_id=<id>` cuando el RUT no existe, pero esa ruta todavía no existe. La tabla `paciente` de la migración `001` tiene `correo TEXT NOT NULL`, mientras que la historia permite registrarse con teléfono o correo. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Registrar un Paciente desde el flujo de reserva y retomar el bloque seleccionado.
- Reutilizar el registro existente cuando el RUT ya está registrado.
- Validar nombre completo, RUT y al menos un medio de contacto.
- Cubrir los tres escenarios Gherkin con pruebas automáticas.

**Non-Goals:**
- Crear o modificar Reservas (HU-02 y HU-03).
- Editar o eliminar datos del Paciente.
- Autenticación real, ficha clínica y requisitos no funcionales.
- Validar el dígito verificador del RUT.

## Decisions

- **Migración `002` para `correo` opcional:** se reconstruye la tabla `paciente` con `correo TEXT` (sin `NOT NULL`) y se copian los datos. La migración desactiva las claves foráneas durante la reconstrucción, ejecuta `PRAGMA foreign_key_check` y las vuelve a activar; la tabla `reserva` sigue apuntando a `paciente` por nombre. Alternativa descartada: guardar una cadena vacía en `correo`, que oculta la regla en la base y confunde la lectura del modelo.
- **Reutilización de la lógica de RUT:** se usa `normalizar_rut` y `buscar_paciente_por_rut` de `app/servicios/reserva.py` para comparar sin puntos ni guion y con K mayúscula. No se valida el dígito verificador porque no está en el Gherkin; se registra como supuesto en la ficha.
- **Servicio de registro:** `app/servicios/paciente.py` expone `registrar_paciente(conexion, nombre_completo, rut, telefono, correo)`. Valida los obligatorios, normaliza el RUT, busca al Paciente y lo inserta solo si no existe. Si el `INSERT` choca con la unicidad del RUT, se captura la violación y se devuelve el registro existente, igual que en la reserva. Devuelve el Paciente y un indicador `creado`.
- **Validación de contacto:** al menos uno de `telefono` o `correo` debe tener contenido después de `strip()`. No se validan formatos de teléfono ni de correo; el Gherkin solo exige que exista un medio de contacto.
- **Orden de validación:** primero se busca el RUT. Si ya existe, se reutiliza el registro sin exigir nombre ni contacto nuevos, porque el paciente ya está registrado; si no existe, se validan el nombre, el RUT y el contacto antes de insertar.
- **Rutas y POST-Redirect-GET:** `GET /pacientes/registro` muestra el formulario y conserva `bloque_id` en un campo oculto. `POST /pacientes/registro` valida y, si hay errores, vuelve a renderizar el formulario con los valores ingresados y el mensaje de qué falta. Si el registro es correcto y hay `bloque_id`, responde `303` a `/reservar/<bloque_id>?rut=<rut_normalizado>`; si no hay bloque, responde `303` a `GET /pacientes/<id>` con la plantilla `registro_confirmado.html`. Se evita renderizar el éxito directamente para que recargar no reenvíe el formulario.
- **Precarga del RUT:** `GET /reservar/{bloque_id}` acepta un parámetro de consulta `rut` y lo pasa al contexto; la plantilla `reserva.html` ya usa `rut` para el valor del campo. Así el paciente no vuelve a escribir el RUT al retomar la reserva.
- **Bloque inválido o ausente:** si `bloque_id` no corresponde a un bloque existente, el registro se completa igual y se muestra la confirmación sin retomar la reserva. No se inventa una reserva para un bloque inexistente.
- **Datos opcionales:** el formulario solo muestra nombre completo, RUT, teléfono y correo, como indica el flujo confirmado. `fecha_nacimiento`, `direccion`, `escolaridad` y `ocupacion` quedan en `NULL`; no se editan en esta historia.
- **Sin sistemas externos:** no hay mensajería ni otro adaptador en esta historia.

## Risks / Trade-offs

- **Reconstrucción de `paciente` con datos existentes** → la migración copia las filas y verifica las claves foráneas; se prueba sobre una base con pacientes y reservas antes de usarla en `data/app.db`.
- **RUT sin dígito verificador válido** → se acepta cualquier RUT no vacío y único; es una simplificación confirmada, no una regla de negocio.
- **RUT ya registrado con otro nombre** → se reutiliza el registro existente y no se actualizan sus datos; el Gherkin pide no duplicar, no corregir.
- **`bloque_id` manipulado en el formulario** → si no existe, se ignora y se muestra la confirmación; no se crea nada.
- **Sin autenticación** → cualquiera puede registrar un RUT; es consistente con el selector de rol de demostración y queda fuera del alcance.

## Migration Plan

1. Crear `app/db/migrations/002_paciente_correo_opcional.sql` y aplicarla al arrancar.
2. Verificar con una base temporal que los pacientes y reservas existentes se conservan.
3. Para volver atrás, restaurar la migración `001` y la base desde una copia; el cambio no elimina datos.

## Open Questions

Ninguna que afecte las especificaciones. El texto exacto de los mensajes de validación se define en la plantilla y se puede ajustar sin cambiar el comportamiento.
