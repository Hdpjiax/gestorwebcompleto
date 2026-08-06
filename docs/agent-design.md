# Diseno de Agentes

## Contrato inicial

Los agentes deben actuar como asistentes de planificacion y revision, no como motores ofensivos autonomos.

Entrada minima:

- `objective`: objetivo del usuario.
- `scope`: descripcion del entorno autorizado.
- `output`: formato esperado.

Salida minima:

- Resumen del alcance.
- Riesgos y limites.
- Plan defensivo o educativo.
- Evidencias o artefactos esperados.

## CrewAI stub

`agents/crewai_stub.py` modela roles simples:

- Coordinador de alcance.
- Analista defensivo.
- Redactor de reporte.

## AutoGen stub

`agents/autogen_stub.py` modela una conversacion determinista entre:

- Usuario solicitante.
- Revisor de seguridad.
- Planificador tecnico.

## Regla comun

Si el objetivo sugiere actividad no autorizada o evasion maliciosa, el agente debe rechazar esa parte y ofrecer una alternativa segura: laboratorio propio, checklist defensivo o guia de cumplimiento.

## Checklist operativo

La lista completa para fase 2 vive en [`docs/agent-checklist.md`](agent-checklist.md). Todo agente debe aplicarla antes de recomendar o ejecutar tareas relacionadas con Camoufox, mitmproxy, interceptacion, replay o manejo de evidencias.

Puntos minimos:

- Confirmar `objective`, `scope` y activos permitidos.
- Mantener procesos y pruebas en laboratorios locales o autorizados.
- Rechazar evasion maliciosa, abuso de plataformas, robo de credenciales o uso contra terceros sin permiso.
- Redactar secretos en logs, flows y reportes.
- Reportar artefactos, validaciones y riesgos residuales al finalizar.
