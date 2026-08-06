# Runbook Windows/WSL

## Alcance

Este runbook prepara un entorno local de desarrollo para la fase 2 en Windows con WSL. Debe usarse solo contra laboratorios propios, aplicaciones internas autorizadas o servicios locales de prueba.

No ejecutar interceptacion contra cuentas, plataformas o sistemas de terceros sin permiso escrito.

## Topologia recomendada

- Codigo fuente en WSL bajo `/mnt/c/Users/Antonio Garcia/Documents/gestorwebcompleto` o en el filesystem nativo de WSL.
- Backend Python, Camoufox y mitmproxy ejecutandose desde WSL.
- Frontend o navegador de pruebas apuntando a `127.0.0.1`.
- Puertos locales reservados por perfil, nunca expuestos a `0.0.0.0`.

## Requisitos Windows

- Windows 11 o Windows 10 actualizado.
- WSL 2 habilitado.
- Ubuntu LTS en WSL.
- Python 3.10+ en WSL.
- Node.js 20+ si se trabaja en frontend.
- Git instalado.

Comprobaciones basicas:

```bash
wsl --status
python3 --version
node --version
git --version
```

## Preparar WSL

Actualizar paquetes:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git ca-certificates curl
```

Instalar dependencias comunes de navegadores Playwright/Camoufox cuando aplique:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install playwright
python3 -m playwright install-deps
```

## Preparar el repo

Desde el directorio del proyecto:

```bash
cd "/mnt/c/Users/Antonio Garcia/Documents/gestorwebcompleto"
./scripts/setup.sh
```

Activar entorno virtual si el script lo creo:

```bash
source .venv/bin/activate
```

Instalar dependencias planeadas para fase 2 cuando existan los manifests correspondientes:

```bash
python3 -m pip install camoufox mitmproxy fastapi uvicorn pydantic
camoufox fetch
```

Si el proyecto define `requirements.txt` en el backend, preferir ese archivo:

```bash
python3 -m pip install -r apps/backend/requirements.txt
```

## Verificar mitmproxy local

Arrancar un proxy de prueba solo en localhost:

```bash
mitmdump --listen-host 127.0.0.1 --listen-port 8899
```

En otra terminal WSL, probar conectividad contra un endpoint local o de laboratorio autorizado:

```bash
curl --proxy http://127.0.0.1:8899 http://127.0.0.1:8000/health
```

Detener mitmproxy con `Ctrl+C` al terminar.

## Certificados por perfil

mitmproxy genera su CA local normalmente bajo `~/.mitmproxy`. Para la app, la fase 2 debe copiar o instalar la confianza solo dentro del perfil Camoufox gestionado.

Reglas:

- No instalar la CA de desarrollo en Windows global.
- No instalar la CA en el Firefox personal del operador.
- No reutilizar perfiles personales como `user_data_dir`.
- Documentar huella, fecha de creacion y perfil asociado.

Verificacion esperada:

```bash
ls -la ~/.mitmproxy
```

La automatizacion final debe encargarse de importar la CA al almacen del perfil de prueba. Hasta que eso exista, mantener HTTPS como caso manual documentado.

## Puertos y firewall

Usar rangos locales dedicados:

- Backend API: `127.0.0.1:8756`
- mitmproxy por perfil: `127.0.0.1:8800-8899`
- servidores locales de prueba: `127.0.0.1:8000-8099`

Comprobar puertos:

```bash
ss -ltnp | grep -E '8756|88[0-9][0-9]|80[0-9][0-9]'
```

Si Windows Firewall pregunta por acceso de red, negar redes publicas y permitir solo el entorno local cuando sea necesario.

## Flujo de prueba recomendado

1. Crear o arrancar una app local de laboratorio.
2. Confirmar `scope_statement` y `allowed_hosts`.
3. Iniciar backend en `127.0.0.1`.
4. Iniciar perfil Camoufox desde el launcher.
5. Confirmar que mitmproxy escucha en el puerto asignado.
6. Navegar solo a hosts permitidos.
7. Revisar historial de flows.
8. Probar intercepcion manual con un request benigno.
9. Exportar evidencia.
10. Detener perfil y comprobar que no quedan procesos.

## Limpieza

Buscar procesos:

```bash
ps aux | grep -E 'mitmdump|camoufox|firefox' | grep -v grep
```

Detener procesos solo si pertenecen al perfil de prueba:

```bash
kill <pid>
```

Eliminar perfiles temporales solo cuando no contengan evidencia requerida:

```bash
rm -rf .local/profiles/<profile_id>
```

## Problemas comunes

- `camoufox fetch` falla: revisar conectividad de WSL y version de Python.
- mitmproxy no captura HTTPS: falta instalar CA en el perfil gestionado.
- El puerto ya esta ocupado: liberar proceso anterior o asignar otro puerto.
- Windows no abre la UI del backend WSL: confirmar bind a `127.0.0.1` y no a una interfaz externa.
- Rutas con espacios: envolver paths de Windows entre comillas.

## Checklist antes de operar

- Hay autorizacion documentada.
- `allowed_hosts` contiene solo activos propios o aprobados.
- mitmproxy escucha en `127.0.0.1`.
- El perfil Camoufox no comparte cookies con perfiles personales.
- La CA no fue instalada globalmente.
- Existe plan de parada y limpieza.
