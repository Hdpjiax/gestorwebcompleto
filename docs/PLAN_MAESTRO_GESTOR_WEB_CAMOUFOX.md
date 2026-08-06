# Plan Maestro: Gestor Web de Ciberseguridad con Camoufox Embebido

> **Alcance declarado**: Herramienta educativa/profesional de pentesting y QA (tipo "Burp Suite + Anti-detect Browser Manager"), construida sobre Camoufox como motor embebido. Uso exclusivo en entornos propios/autorizados. 100% stack gratuito y open-source.

---

## 0. Fundamentos del proyecto

### 0.1 Qué es y qué NO es
- **ES**: un gestor de perfiles de navegador (tipo Multilogin/GoLogin pero self-hosted y gratis) + proxy interceptor (tipo Burp/OWASP ZAP) + motor de fingerprinting (Camoufox), todo embebido en un solo ejecutable de escritorio.
- **NO ES**: una recompilación diaria del código C++ de Camoufox. Ese repo se toca solo si falta una feature de spoofing que su API de Python/config no expone [web:8][web:30].

### 0.2 Stack 100% gratuito (todo open-source, sin licencias de pago)

| Capa | Herramienta | Licencia |
|---|---|---|
| Motor de navegador | Camoufox (Firefox parcheado) | MIT/MPL |
| Automatización del navegador | Playwright (Python) | Apache 2.0 |
| Interceptor de tráfico | mitmproxy | MIT |
| Backend API | FastAPI + Uvicorn | MIT |
| Base de datos local | SQLite (perfiles) + opcional Supabase (sync cloud gratis tier) | MIT/Apache |
| Frontend | Electron + React + Vite + TypeScript | MIT |
| UI Kit | shadcn/ui + Radix UI + TailwindCSS | MIT |
| Iconos | Lucide Icons | ISC |
| Empaquetado backend | PyInstaller | GPL (uso libre) |
| Empaquetado app final | electron-builder | MIT |
| CI/CD | GitHub Actions (gratis en repos públicos/privados con minutos free) | — |
| Orquestación multi-agente | CrewAI o Microsoft AutoGen (ambos open-source) | MIT |
| Testing E2E | Playwright Test + Vitest | Apache/MIT |
| Fingerprint generator | BrowserForge (usado internamente por Camoufox) | MIT |

---

## 1. Arquitectura general

```
┌──────────────────────────────────────────────────────────┐
│                  ELECTRON SHELL (Frontend)                │
│  React + Vite + shadcn/ui + Tailwind                       │
│  - Profile Manager UI                                      │
│  - Interceptor UI (estilo Burp: HTTP History / Repeater)   │
│  - Privacy Level Selector (1/2/3)                          │
│  - Embedded Browser Viewport (via CDP/Playwright stream)   │
└───────────────────────┬──────────────────────────────────┘
                         │ IPC (Electron) + WebSocket/HTTP
┌───────────────────────▼──────────────────────────────────┐
│              PYTHON BACKEND (FastAPI, local :8756)         │
│  - Profile Service (CRUD, fingerprint JSON, cookies path)  │
│  - Launcher Service (lanza instancias Camoufox)            │
│  - Proxy Orchestrator (levanta mitmproxy por perfil)        │
│  - Anonymity Level Engine (aplica presets 1/2/3)            │
│  - Flow Store (SQLite: requests/responses capturados)       │
└───────┬───────────────────────────────┬────────────────────┘
        │                               │
┌───────▼─────────┐           ┌─────────▼──────────┐
│  Camoufox #1..N   │           │  mitmproxy #1..N     │
│  (1 por perfil)    │◄─proxy──│  (1 por perfil)       │
│  user_data_dir     │         │  addon.py (intercept) │
│  fingerprint.json  │         └──────────────────────┘
└────────────────────┘
```

**Regla de aislamiento**: cada perfil = 1 `user_data_dir` único + 1 puerto de mitmproxy único + 1 fingerprint JSON único. Nunca comparten cookies ni proceso.

---

## 2. Estructura de carpetas (monorepo, tipo árbol SSD completo)

```
cyber-browser-manager/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml            # tests + lint Python
│   │   ├── ci-frontend.yml           # tests + lint TS/React
│   │   ├── build-release.yml         # build multiplataforma .exe/.dmg/.AppImage
│   │   └── agents-orchestration.yml  # dispara agentes QA/design/backend en paralelo
│   └── ISSUE_TEMPLATE/
│
├── apps/
│   ├── desktop/                      # ELECTRON APP (frontend)
│   │   ├── src/
│   │   │   ├── main/                 # proceso principal Electron
│   │   │   │   ├── main.ts
│   │   │   │   ├── ipc-handlers.ts
│   │   │   │   ├── backend-spawner.ts   # levanta el .exe de Python al iniciar
│   │   │   │   └── window-manager.ts
│   │   │   ├── preload/
│   │   │   │   └── preload.ts
│   │   │   └── renderer/             # UI React
│   │   │       ├── pages/
│   │   │       │   ├── ProfileManager/
│   │   │       │   ├── Interceptor/       # vista tipo Burp Proxy/Repeater
│   │   │       │   ├── AnonymitySettings/
│   │   │       │   ├── BrowserView/       # viewport embebido
│   │   │       │   └── Dashboard/
│   │   │       ├── components/
│   │   │       │   ├── ui/                # shadcn components
│   │   │       │   ├── ProfileCard.tsx
│   │   │       │   ├── FingerprintEditor.tsx
│   │   │       │   ├── ProxyForm.tsx
│   │   │       │   ├── AnonymityLevelSlider.tsx
│   │   │       │   ├── FlowTable.tsx        # tabla HTTP History
│   │   │       │   └── RequestEditor.tsx    # equivalente a Repeater
│   │   │       ├── hooks/
│   │   │       ├── store/            # Zustand/Redux
│   │   │       ├── lib/api.ts        # cliente HTTP hacia backend FastAPI
│   │   │       └── styles/
│   │   ├── electron-builder.yml
│   │   ├── vite.config.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── backend/                      # PYTHON FASTAPI
│       ├── app/
│       │   ├── main.py               # entrypoint FastAPI
│       │   ├── api/
│       │   │   ├── routes_profiles.py
│       │   │   ├── routes_launcher.py
│       │   │   ├── routes_interceptor.py
│       │   │   ├── routes_anonymity.py
│       │   │   └── routes_flows.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── security.py
│       │   │   └── logging.py
│       │   ├── services/
│       │   │   ├── camoufox_launcher.py     # lanza instancias Camoufox
│       │   │   ├── proxy_orchestrator.py    # gestiona procesos mitmproxy
│       │   │   ├── fingerprint_generator.py # wrapper sobre BrowserForge
│       │   │   ├── anonymity_presets.py     # lógica niveles 1/2/3
│       │   │   └── profile_manager.py
│       │   ├── mitm_addons/
│       │   │   ├── intercept_addon.py       # captura request/response
│       │   │   ├── modify_addon.py          # edición manual (Repeater)
│       │   │   ├── cert_installer.py        # instala CA en perfil Camoufox
│       │   │   └── ws_streamer.py           # emite flows al frontend via WS
│       │   ├── models/
│       │   │   ├── profile.py               # Pydantic + ORM
│       │   │   ├── flow.py
│       │   │   └── fingerprint.py
│       │   ├── db/
│       │   │   ├── database.py              # SQLite (local) / Supabase client
│       │   │   ├── migrations/
│       │   │   └── seed_data.py
│       │   └── utils/
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── e2e/
│       ├── requirements.txt
│       └── pyinstaller.spec
│
├── packages/                         # código compartido
│   ├── shared-types/                 # tipos TS/JSON schema comunes
│   └── fingerprint-presets/          # JSONs de fingerprints predefinidos
│
├── agents/                           # definiciones de agentes IA (CrewAI/AutoGen)
│   ├── design_agent.py
│   ├── backend_agent.py
│   ├── qa_agent.py
│   ├── test_agent.py
│   └── orchestrator.py               # corre los 4 en paralelo
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ANONYMITY_LEVELS.md
│   ├── LEGAL_ETHICS.md
│   └── API_REFERENCE.md
│
├── scripts/
│   ├── setup_dev_env.sh / .ps1
│   ├── build_all.sh / .ps1
│   └── fetch_camoufox.py
│
├── .env.example
├── docker-compose.dev.yml            # opcional: backend+mitmproxy en contenedores para dev
├── README.md
└── LICENSE
```

---

## 3. Diseño del Backend (Python/FastAPI)

### 3.1 Responsabilidades
1. **Profile Service**: CRUD de perfiles (nombre, fingerprint JSON, proxy, nivel de anonimato, cookies path, addons activos).
2. **Launcher Service**: por cada "lanzar perfil", ejecuta:
   ```python
   from camoufox.async_api import AsyncCamoufox
   browser = await AsyncCamoufox(
       proxy=perfil.proxy_config,
       geoip=True,
       os=perfil.fingerprint.os,
       fonts=perfil.fingerprint.fonts,
       block_webrtc=perfil.privacy.block_webrtc,
       persistent_context=True,
       user_data_dir=f"./profiles_data/{perfil.id}",
       config=perfil.fingerprint.raw_overrides,
   ).start()
   ```
   [web:17][web:8]
3. **Proxy Orchestrator**: por perfil, levanta un proceso `mitmdump -s intercept_addon.py --listen-port {puerto_unico}` y conecta Camoufox a ese puerto [web:33][web:36].
4. **Anonymity Level Engine**: aplica presets (ver sección 5).
5. **Flow Store**: el addon de mitmproxy escribe cada `flow` (request/response) a SQLite y lo transmite por WebSocket al frontend para la vista tipo "HTTP History" [web:34][web:40].
6. **Interceptor real-time**: usando `flow.intercept()` / `flow.resume()` de mitmproxy se implementa pausa-edición-envío, el equivalente exacto a Burp Proxy [web:40].

### 3.2 Endpoints clave (FastAPI)
- `POST /profiles` — crear perfil
- `GET /profiles/{id}` — detalle
- `POST /profiles/{id}/launch` — lanza Camoufox + mitmproxy asociados
- `POST /profiles/{id}/stop`
- `GET /flows?profile_id=` — histórico de tráfico
- `POST /flows/{id}/replay` — reenvía request modificado (Repeater)
- `PUT /profiles/{id}/anonymity-level` — cambia nivel 1/2/3
- `WS /ws/flows/{profile_id}` — stream en vivo de tráfico

---

## 4. Diseño del Frontend (Electron + React)

### 4.1 Vistas principales
- **Dashboard**: lista de perfiles activos/inactivos, estado de conexión.
- **Profile Manager**: crear/editar perfil — fingerprint (UA, WebGL, fuentes, pantalla), proxy (host/puerto/usuario/pass), cookies (aisladas por `user_data_dir`), nivel de anonimato (slider 1-2-3).
- **Interceptor**: tabla de requests/responses en vivo (columna método, URL, status, tamaño) + panel de edición hexadecimal/texto tipo Repeater + botón "Forward/Drop".
- **Browser View**: viewport embebido mostrando el Camoufox en ejecución (via captura de pantalla remota o `page.screenshot` en loop, o CDP si se expone).
- **Anonymity Settings**: presets visuales de los 3 niveles con explicación de qué protege cada uno.

### 4.2 Comunicación Electron ↔ Python
- Electron `main.ts` lanza el `.exe`/binario de FastAPI empaquetado como proceso hijo al iniciar la app (`backend-spawner.ts`).
- El renderer habla con el backend por HTTP/WebSocket en `localhost:8756`, nunca expone el backend a la red externa.

---

## 5. Los 3 niveles de anonimato (presets aplicados por el Anonymity Engine)

| Nivel | Nombre | Fingerprint | Proxy | Extras |
|---|---|---|---|---|
| 1 | Básico | Fingerprint aleatorio (BrowserForge), 1 por perfil | Opcional | uBlock Origin, cookies aisladas |
| 2 | Medio | Fingerprint + spoof de timezone/geolocalización acorde al proxy (`geoip=True`) [web:17] | Proxy HTTP/SOCKS5 obligatorio | `block_webrtc=True`, rotación de fuentes, headers consistentes |
| 3 | Máximo ("tipo Tor") | Fingerprint uniformizado (todos los perfiles Nivel 3 se ven iguales entre sí, como Tor Browser) | Tor SOCKS5 (`127.0.0.1:9050`) o multi-hop de proxies | `privacy.resistFingerprinting`, bloqueo WebGL/Canvas, sin cache, sin WebRTC, viewport fijo estándar |

---

## 6. Agentes IA gratuitos para desarrollo paralelo

Usa **CrewAI** o **AutoGen** (ambos open-source, gratis, corren con cualquier LLM incluyendo modelos locales via Ollama) para levantar 4 agentes que trabajen en paralelo sobre el repo:

```
agents/orchestrator.py
├── design_agent.py    → genera/ajusta componentes shadcn, revisa UX, contraste, accesibilidad
├── backend_agent.py   → implementa endpoints FastAPI, servicios, migraciones
├── qa_agent.py        → escribe casos de prueba manuales/checklist, revisa flujos de usuario
└── test_agent.py      → genera tests Vitest (frontend) y Pytest (backend), corre CI local
```

**Integraciones GitHub gratuitas recomendadas**:
- **GitHub Copilot** (plan free para estudiantes/open source, o Copilot en modo Chat/Agent gratuito limitado) para autocompletado y refactors guiados por Issues.
- **GitHub Actions** (minutos gratis en repos públicos) para correr `agents-orchestration.yml` disparando los 4 agentes en jobs paralelos cada push.
- **GitHub Projects** (gratis) como tablero Kanban para las fases del plan.
- **Storybook** (gratis, MIT) conectado al repo para que el `design_agent` documente y pruebe componentes UI aislados.
- **shadcn/ui + Radix + Tailwind** como base de componentes ya accesibles (WAI-ARIA) sin costo, en vez de librerías "pro" de pago.

---

## 7. Fases de implementación

### Fase 0 — Preparación (1-2 días)
- Crear repo monorepo con la estructura de la sección 2.
- Configurar `pnpm workspaces` o `turborepo` para frontend, `venv` + `requirements.txt` para backend.
- Instalar Camoufox: `pip install camoufox[geoip]` + `camoufox fetch` [web:18].
- Configurar GitHub Actions básicos (lint + test vacíos) para validar el pipeline desde el día 1.

### Fase 1 — Backend core (perfiles + lanzador)
- Implementar `profile_manager.py`, modelos Pydantic, SQLite con SQLAlchemy.
- Implementar `camoufox_launcher.py`: lanzar/cerrar instancias con fingerprint y `user_data_dir` por perfil [web:17].
- Endpoints REST de CRUD de perfiles + lanzar/detener.
- Tests unitarios del launcher (mock de Camoufox).

### Fase 2 — Proxy Orchestrator + Interceptor (estilo Burp)
- Integrar mitmproxy como subproceso por perfil (`proxy_orchestrator.py`).
- Addon `intercept_addon.py`: captura flows, los guarda en SQLite, los transmite por WebSocket [web:33][web:36].
- Addon `modify_addon.py`: soporte `flow.intercept()`/`resume()` para pausa-edición-reenvío [web:40].
- Instalación automática del certificado CA de mitmproxy dentro del `user_data_dir` de cada Camoufox para evitar errores TLS [web:7][web:13].
- Endpoint `/flows/{id}/replay` (equivalente a Repeater).
- Roadmap operativo detallado: [`docs/phase-2-roadmap.md`](phase-2-roadmap.md).
- Runbook de setup Windows/WSL: [`docs/windows-wsl-runbook.md`](windows-wsl-runbook.md).
- Checklist de agentes para esta fase: [`docs/agent-checklist.md`](agent-checklist.md).

### Fase 3 — Motor de anonimato (3 niveles)
- Implementar `anonymity_presets.py` con las 3 configuraciones de la sección 5.
- Integrar soporte Tor (detectar si Tor Service está corriendo localmente en `9050`, o instrucciones para instalar Tor Expert Bundle gratis).
- Endpoint para cambiar nivel de un perfil en caliente (relanza Camoufox con nueva config).

### Fase 4 — Frontend base (Electron shell)
- Scaffolding Electron + Vite + React + TypeScript.
- Layout general (sidebar, topbar), routing entre vistas.
- Cliente API (`lib/api.ts`) y conexión WebSocket para flows en vivo.
- Integrar shadcn/ui + Tailwind, definir design tokens (colores, tipografía).

### Fase 5 — UI de gestión de perfiles
- `ProfileManager`: formulario completo (fingerprint editor visual, proxy form, selector de nivel de anonimato, cookies status).
- `ProfileCard`: vista resumen con estado (activo/inactivo) y acciones rápidas.
- Persistencia de cambios contra el backend.

### Fase 6 — UI del Interceptor (Burp-like)
- `FlowTable`: tabla en vivo con filtros por método/status/dominio.
- `RequestEditor`: panel dividido request/response editable, botón Forward/Drop/Replay.
- WebSocket listener para actualizar la tabla en tiempo real.

### Fase 7 — Browser View embebido
- Streaming del viewport de Camoufox hacia el renderer (captura periódica de screenshot, o exploración de exposer CDP si se habilita).
- Controles básicos: URL bar, back/forward/reload, indicador de nivel de anonimato activo.

### Fase 8 — QA, testing y agentes automatizados
- Activar `agents/orchestrator.py`: `design_agent` revisa consistencia visual, `backend_agent` cierra endpoints pendientes, `qa_agent` genera checklist de pruebas manuales, `test_agent` escribe/corre Pytest + Vitest + Playwright Test.
- Pipeline CI en GitHub Actions corriendo los 4 agentes en jobs paralelos en cada PR.
- Pruebas E2E: crear perfil → lanzar → interceptar tráfico → cambiar nivel de anonimato → verificar aislamiento de cookies entre perfiles.

### Fase 9 — Empaquetado como ejecutable único
- Backend: `pyinstaller --onefile app/main.py` generando binario standalone (sin requerir Python instalado) [web:44][web:47].
- Frontend: `electron-builder` empaqueta el binario de PyInstaller como recurso interno y lo lanza como proceso hijo al abrir la app [web:43].
- Generar instaladores para Windows (.exe/.msi), y opcionalmente Linux (.AppImage)/macOS (.dmg) desde GitHub Actions (`build-release.yml`).

### Fase 10 — Documentación y hardening final
- Completar `docs/ANONYMITY_LEVELS.md`, `docs/API_REFERENCE.md`, `docs/LEGAL_ETHICS.md` (uso responsable, alcance permitido).
- Revisión de seguridad: el backend nunca debe exponer puertos fuera de `localhost`, certificados CA solo se instalan dentro de los `user_data_dir` gestionados, no en el sistema global.
- Release v1.0 vía GitHub Releases (gratis).

---

## 8. Consideraciones éticas y legales (obligatorias)

- Uso exclusivo en sistemas propios o con autorización explícita por escrito.
- No usar los perfiles de fingerprint spoof para evadir bans, fraude publicitario o suplantación de identidad en servicios de terceros.
- Documentar el proyecto públicamente como herramienta de pentesting/QA/educación, siguiendo el mismo encuadre que Burp Suite Community, OWASP ZAP o mitmproxy — todas herramientas legítimas y ampliamente usadas en la industria [web:34][web:36].
- Incluir en el README un disclaimer claro de uso responsable antes de cualquier release público.
