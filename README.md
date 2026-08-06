# Gestor Web Completo

Monorepo inicial para un gestor web de ciberseguridad educativo y profesional con Camoufox embebido.

El proyecto nace con una regla de producto clara: todo flujo debe estar orientado a aprendizaje, auditoria autorizada, gestion de evidencias y mejora defensiva. No se aceptan funciones de evasion maliciosa, abuso de terceros, robo de credenciales, persistencia no autorizada o automatizacion ofensiva fuera de alcance.

## Estructura

```text
apps/
  backend/          # Aplicacion futura del backend
agents/            # Stubs ejecutables para agentes CrewAI/AutoGen
docs/              # Arquitectura, etica, operaciones y runbooks
scripts/           # Setup, build y validaciones locales
.github/workflows/ # CI basico
```

## Inicio rapido

```bash
cp .env.example .env
./scripts/setup.sh
./scripts/build.sh
./scripts/test.sh
```

Los scripts son intencionalmente conservadores: validan el repo, preparan un entorno Python local para los agentes y solo ejecutan pasos de Node/Python cuando detectan los archivos correspondientes.

## Agentes

Los stubs de `agents/` funcionan sin instalar CrewAI o AutoGen. Si esas librerias estan disponibles, el codigo puede extenderse sin cambiar el contrato de CLI.

```bash
python3 agents/crewai_stub.py --objective "Revisar checklist defensivo de un laboratorio autorizado"
python3 agents/autogen_stub.py --objective "Generar plan de pruebas para entrenamiento interno"
```

## Principios de seguridad

- Uso solo en sistemas propios, laboratorios o entornos con permiso explicito.
- Registro de alcance, autorizacion y responsable antes de cualquier flujo sensible.
- No se implementan bypasses, sigilo malicioso, exfiltracion o abuso de terceros.
- Camoufox se usa para compatibilidad de navegacion, QA y automatizacion autorizada, no para evadir controles de plataformas externas.

## Licencia

MIT. Ver `LICENSE`.
