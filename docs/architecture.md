# Arquitectura Inicial

## Objetivo

Construir un gestor web para ciberseguridad educativa y profesional que combine:

- Gestion de laboratorios, ejercicios y evidencias.
- Automatizacion de navegador con Camoufox para QA, recorridos guiados y validaciones autorizadas.
- Agentes de asistencia para planificacion, documentacion y revision defensiva.
- Controles de alcance que bloqueen usos fuera de autorizacion.

## Componentes previstos

```text
Frontend web
  -> Backend API
  -> Agent runtime
  -> Browser automation service
  -> Storage de evidencias y auditoria
```

## Limites de responsabilidad

El sistema no debe ejecutar acciones contra terceros sin permiso verificable. Las integraciones de navegador y agentes deben exigir contexto de autorizacion, registrar decisiones relevantes y favorecer tareas de defensa, aprendizaje y cumplimiento.

## Camoufox

Camoufox se considera una dependencia de automatizacion de navegador para entornos controlados:

- Pruebas de compatibilidad web.
- Reproduccion de flujos de usuario en laboratorios.
- Captura de evidencias autorizadas.
- Entrenamiento educativo.

No debe exponerse como mecanismo para evadir protecciones de servicios externos, automatizar abuso, ocultar identidad en ataques o incumplir terminos de terceros.

## Convenciones de monorepo

- `apps/`: aplicaciones desplegables.
- `packages/`: librerias compartidas futuras.
- `agents/`: agentes y contratos CLI.
- `docs/`: decisiones, runbooks y politicas.
- `scripts/`: automatizacion local y CI.
