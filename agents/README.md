# Agents

Stubs ejecutables para apoyar la construccion del monorepo con CrewAI o AutoGen mas adelante.

Estos agentes son independientes del gestor web: no forman parte del backend, del frontend, del navegador embebido ni del runtime distribuible. Se usan solo como herramientas de desarrollo, planificacion, revision y QA del repositorio.

## Uso

```bash
python3 agents/crewai_stub.py --objective "Preparar laboratorio educativo de hardening"
python3 agents/autogen_stub.py --objective "Revisar alcance de auditoria autorizada" --scope "Aplicacion interna staging"
```

Ambos stubs producen JSON para facilitar integracion con CI o scripts internos de desarrollo. No deben conectarse al backend ni a flujos de UI del producto.

## Checklist fase 2

Antes de usar estos stubs para coordinar tareas sobre Camoufox, mitmproxy o cualquier runner real de desarrollo, aplicar [`docs/agent-checklist.md`](../docs/agent-checklist.md).

Resumen obligatorio:

- Exigir objetivo y alcance autorizado.
- Mantener acciones en laboratorios locales o activos permitidos.
- Rechazar evasion maliciosa, abuso de terceros y manejo inseguro de credenciales.
- Registrar artefactos, validaciones y riesgos residuales.
