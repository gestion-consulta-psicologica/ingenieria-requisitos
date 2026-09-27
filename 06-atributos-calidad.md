# Atributos de calidad (ISO 25010)

## Priorización de los 9 atributos de primer nivel

1. Security (Seguridad)
2. Interaction capability (Capacidad de interacción)
3. Performance efficiency (Eficiencia de desempeño)
4. Reliability (Fiabilidad)
5. Functional suitability (Adecuación funcional)
6. Flexibility (Flexibilidad)
7. Compatibility (Compatibilidad)
8. Maintainability (Mantenibilidad)
9. Safety (Seguridad frente a riesgos)

### Justificación de la priorización

1. **Security:** Es el atributo de mayor prioridad debido a que el sistema manejará información personal, administrativa y clínica confidencial de los pacientes. Se requiere controlar el acceso a esta información según el rol del usuario.

2. **Interaction capability:** La plataforma será utilizada por pacientes y por la psicóloga, por lo que debe ser sencilla de comprender y utilizar, especialmente para consultar, reservar, confirmar o reagendar horas.

3. **Performance efficiency:** La rapidez de respuesta fue identificada como un aspecto relevante. La consulta de disponibilidad, reservas y demás operaciones frecuentes deben responder en tiempos adecuados.

4. **Reliability:** El sistema debe mantenerse disponible y conservar correctamente la información de reservas, pagos, asistencia y fichas clínicas.

5. **Functional suitability:** Las funciones implementadas deben permitir realizar correctamente las actividades definidas en el proceso TO-BE.

6. **Flexibility:** El sistema debe poder adaptarse a cambios futuros en la gestión de horas, atención o información de pacientes.

7. **Compatibility:** La plataforma debe funcionar correctamente en distintos dispositivos y navegadores utilizados por los usuarios.

8. **Maintainability:** El sistema debe permitir realizar correcciones y modificaciones de forma controlada durante su evolución.

9. **Safety:** Aunque sigue siendo relevante, el sistema propuesto apoya principalmente actividades administrativas y de gestión clínica, y no toma decisiones clínicas o diagnósticas automáticamente.

## Métricas de los 3 atributos más importantes

### 1. Security (Seguridad)

- **Métrica:** Porcentaje de funcionalidades que manejan información clínica o personal y que cuentan con autenticación y control de acceso según rol.
- **Cálculo:** (Funcionalidades protegidas correctamente / Total de funcionalidades que manejan información sensible) × 100.
- **Meta:** 100% de las funcionalidades que manejan información sensible deben requerir autenticación y autorización según el rol correspondiente.

### 2. Interaction capability (Capacidad de interacción)

- **Métrica:** Porcentaje de tareas principales completadas correctamente por los usuarios sin ayuda externa.
- **Tareas evaluadas:** consultar disponibilidad, reservar una hora, confirmar o cancelar una hora y reagendar una atención.
- **Cálculo:** (Tareas completadas correctamente / Total de tareas intentadas) × 100.
- **Meta:** Al menos el 90% de las tareas evaluadas deben poder completarse correctamente sin asistencia.

### 3. Performance efficiency (Eficiencia de desempeño)

- **Métrica:** Tiempo de respuesta de las operaciones principales de la plataforma.
- **Operaciones evaluadas:** consulta de disponibilidad, registro de reserva, confirmación y consulta de información del paciente.
- **Medición:** Tiempo transcurrido desde que el usuario realiza la acción hasta que el sistema entrega la respuesta.
- **Meta:** Al menos el 95% de las operaciones evaluadas deben responder en un tiempo máximo de 2 segundos bajo condiciones normales de uso.