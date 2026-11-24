Cambios a en HU: 
  Al momento de que el paciente hace la reserva, al psicologo le llega una solicitud de revisión con una opcion
  de derivarlo a psiquiatra o no.
Modelo de domimio:
  Aparece las clases derivación a psiquiatra y psiquiatra.
  Psiquiatra emite boleta.
  Desde la reserva se manda una solicitud de "derivación a psiquiatra" a la psicologa.
  Si la solicitud es un si, se confirma la hora con el psiquiatra, si no se sigue con la psicologa.
Casos de uso:
  Nuevo caso de uso, llamado derivar solicitud de consulta
    -Derivar solicitud
    -Seleccionar psiquitra registrado.
Diagrama de secuencia:
  un nuevo DSS con confirmación si se deriva a psiquiatra o no y todas las acciones correspondientes.
Diagramas de estado:
  Cambia el diagrama de estado de reserva, haciendo que la confirmacion quede pendiente
  para ver si se deriva a psiquiatra o no.
  
