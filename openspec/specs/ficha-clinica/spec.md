# ficha-clinica Specification

## Purpose

Permite a la psicóloga consultar y actualizar la ficha clínica del paciente en la plataforma, conservando los registros anteriores y restringiendo el acceso a la información clínica.

## Requirements

### Requirement: Registrar la evolución de una atención realizada

La psicóloga DEBE (MUST) poder registrar la evolución de una Atencion en estado "realizada" en la ficha clínica del paciente. La ficha DEBE (MUST) conservar el registro con la fecha de la atención, y los registros anteriores NO DEBEN modificarse. Los antecedentes de la ficha DEBEN poder actualizarse conservando sus versiones anteriores.

#### Scenario: La psicóloga registra la evolución de una atención realizada

- **GIVEN** que la atención del jueves 12 de noviembre está en estado "realizada"
- **AND** que la psicóloga inició sesión con su cuenta
- **WHEN** la psicóloga registra la evolución de esa atención en la ficha clínica del paciente
- **THEN** la ficha clínica conserva el registro con la fecha de la atención
- **AND** los registros anteriores de la ficha clínica se mantienen sin cambios

### Requirement: Denegar el acceso clínico sin permiso

El sistema DEBE (MUST) denegar la consulta y la modificación de una ficha clínica a cualquier usuario sin permiso clínico, sin revelar ni modificar datos, y DEBE (MUST) registrar el intento en la bitácora con el usuario y la ficha, sin contenido clínico.

#### Scenario: Un paciente autenticado intenta acceder a una ficha clínica

- **GIVEN** que el paciente inició sesión y su rol no tiene permiso de acceso clínico
- **WHEN** intenta consultar o modificar una ficha clínica
- **THEN** el sistema deniega la solicitud sin revelar ni modificar datos clínicos
- **AND** registra el intento de acceso en la bitácora sin guardar contenido clínico
