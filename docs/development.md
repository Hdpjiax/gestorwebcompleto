# Desarrollo

## Requisitos

- Bash
- Python 3.10+
- Node.js 20+ cuando se agreguen paquetes JavaScript

## Setup

```bash
./scripts/setup.sh
```

El script crea `.local/`, un entorno virtual en `.venv/` si Python esta disponible y copia `.env.example` a `.env` cuando todavia no existe.

## Build

```bash
./scripts/build.sh
```

El build detecta `package.json`, `pyproject.toml` o `requirements.txt` y ejecuta solo los pasos aplicables.

## Validacion

```bash
./scripts/test.sh
```

Las validaciones iniciales comprueban sintaxis Python, permisos de scripts y presencia de documentacion base.

## Fase 2

Para convertir los stubs en integraciones reales, usar estos documentos como entrada de implementacion:

- [`docs/phase-2-roadmap.md`](phase-2-roadmap.md): hitos tecnicos Camoufox + mitmproxy.
- [`docs/windows-wsl-runbook.md`](windows-wsl-runbook.md): setup y operacion local en Windows/WSL.
- [`docs/agent-checklist.md`](agent-checklist.md): controles de agentes, QA y limites eticos.

La fase 2 debe operar por defecto contra `127.0.0.1` y activos explicitamente autorizados. No instalar certificados CA en almacenes globales ni usar perfiles personales como datos de prueba.
