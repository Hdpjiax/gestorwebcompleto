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
