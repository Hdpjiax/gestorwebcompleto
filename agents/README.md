# Agents

Stubs ejecutables para integrar CrewAI o AutoGen mas adelante sin bloquear el avance del monorepo.

## Uso

```bash
python3 agents/crewai_stub.py --objective "Preparar laboratorio educativo de hardening"
python3 agents/autogen_stub.py --objective "Revisar alcance de auditoria autorizada" --scope "Aplicacion interna staging"
```

Ambos stubs producen JSON para facilitar integracion con CI, backend o flujos de UI.

## Checklist fase 2

Antes de conectar estos stubs a Camoufox, mitmproxy o cualquier runner real, aplicar [`docs/agent-checklist.md`](../docs/agent-checklist.md).

Resumen obligatorio:

- Exigir objetivo y alcance autorizado.
- Mantener acciones en laboratorios locales o activos permitidos.
- Rechazar evasion maliciosa, abuso de terceros y manejo inseguro de credenciales.
- Registrar artefactos, validaciones y riesgos residuales.
