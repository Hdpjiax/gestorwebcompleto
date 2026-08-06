# Fase 2: Roadmap Tecnico Camoufox + mitmproxy

## Objetivo

Convertir los stubs actuales en una integracion real, local y auditable entre Camoufox, mitmproxy y el backend, manteniendo el uso limitado a laboratorios, QA y auditorias autorizadas.

La fase 2 no debe producir capacidades autonomas de ataque. Su resultado esperado es un interceptor controlado por el operador para observar, pausar, reenviar y documentar trafico HTTP(S) dentro de un alcance declarado.

## Principios de seguridad

- Ejecutar todo en `127.0.0.1` por defecto.
- Exigir `scope` antes de lanzar navegador o proxy.
- Aislar cada perfil con `user_data_dir`, puerto proxy y almacenamiento propios.
- Instalar certificados solo dentro del perfil gestionado, nunca en el trust store global del sistema.
- Registrar decisiones relevantes: perfil, puerto, dominios permitidos, hora de inicio, hora de fin y operador.
- Bloquear o degradar a modo lectura cuando el alcance no incluya autorizacion escrita.
- Evitar cualquier funcion orientada a evadir bans, antifraude, deteccion de abuso o controles de terceros.

## Entregables

1. Servicio `CamoufoxLauncher` real: crea, inicia, detiene y consulta instancias por perfil.
2. Servicio `ProxyOrchestrator` real: reserva puertos, lanza mitmproxy, supervisa salud y limpia procesos.
3. Addon mitmproxy de captura: serializa request/response, guarda metadatos y emite eventos.
4. Addon de intercepcion: pausa flows segun reglas autorizadas, permite forward/drop y conserva auditoria.
5. Flujo de certificado por perfil: genera o reutiliza CA local de mitmproxy y la instala solo en el perfil.
6. Contratos de datos: perfiles, procesos, flows, decisiones de intercepcion y errores operativos.
7. Pruebas de integracion contra un servidor local deliberadamente controlado.

## Hito 2.1: contratos y storage

Definir contratos antes de implementar procesos externos.

Modelo minimo de perfil:

- `id`
- `name`
- `scope_statement`
- `allowed_hosts`
- `user_data_dir`
- `proxy_port`
- `anonymity_level`
- `created_at`
- `last_launched_at`

Modelo minimo de proceso:

- `profile_id`
- `kind`: `camoufox` o `mitmproxy`
- `pid`
- `port`
- `status`
- `started_at`
- `stopped_at`
- `last_error`

Modelo minimo de flow:

- `id`
- `profile_id`
- `method`
- `scheme`
- `host`
- `path`
- `status_code`
- `request_headers`
- `response_headers`
- `request_body_ref`
- `response_body_ref`
- `captured_at`
- `intercept_decision`

Criterios de aceptacion:

- Los contratos se validan con Pydantic o equivalente.
- No se guarda material sensible sin clasificacion.
- Los bodies grandes se guardan por referencia o se truncaran con politica documentada.

## Hito 2.2: ProxyOrchestrator real

Responsabilidades:

- Reservar un puerto local por perfil.
- Lanzar `mitmdump` con addon controlado por el proyecto.
- Pasar configuracion por variables de entorno o archivo temporal con permisos restringidos.
- Leer stdout/stderr y exponer estado de salud.
- Detener procesos al cerrar perfil o backend.
- Evitar puertos externos; bind explicito a `127.0.0.1`.

Comando base esperado:

```bash
mitmdump \
  --listen-host 127.0.0.1 \
  --listen-port <profile_proxy_port> \
  -s <path_to_intercept_addon>
```

Criterios de aceptacion:

- Un perfil activo crea exactamente un proceso mitmproxy.
- Dos perfiles activos usan puertos distintos.
- Al detener el perfil, el puerto queda liberado.
- Si mitmproxy falla al iniciar, el launcher de Camoufox no arranca.

## Hito 2.3: addon de captura

Responsabilidades:

- Capturar metadatos de request y response.
- Emitir eventos hacia el backend o escribir en cola local.
- Aplicar allowlist de hosts antes de almacenar contenido.
- Redactar cabeceras sensibles por defecto: `Authorization`, `Cookie`, `Set-Cookie`, tokens y secretos conocidos.
- Marcar flows fuera de alcance como `out_of_scope` y no exponer replay.

Criterios de aceptacion:

- Navegar un sitio local produce filas de historial.
- HTTPS funciona dentro del perfil con CA instalada.
- Hosts no autorizados se registran solo con metadatos minimos.

## Hito 2.4: intercepcion y replay autorizados

Responsabilidades:

- Permitir reglas de intercepcion por metodo, host y path dentro de `allowed_hosts`.
- Implementar decisiones explicitas: `forward`, `drop`, `replay`.
- Asociar cada decision a operador, timestamp y perfil.
- Rechazar replay si el flow esta fuera de alcance.

Limites:

- No automatizar fuerza bruta, enumeracion agresiva, evasion de rate limits ni bypass de controles de terceros.
- No guardar credenciales capturadas como valores reutilizables.
- No generar payloads ofensivos; para pruebas educativas usar fixtures benignos y servidores locales.

Criterios de aceptacion:

- Un request pausado no continua hasta recibir decision.
- `drop` corta el flow y deja evidencia.
- `replay` solo acepta cambios manuales dentro de alcance.

## Hito 2.5: CamoufoxLauncher real

Responsabilidades:

- Crear `user_data_dir` por perfil.
- Lanzar Camoufox con proxy local asignado por `ProxyOrchestrator`.
- Aplicar configuracion de privacidad segun nivel documentado.
- Exponer estado: arrancando, listo, detenido, error.
- Cerrar browser/context y limpiar proceso proxy asociado.

Flujo esperado:

1. Validar autorizacion y `allowed_hosts`.
2. Reservar puerto y arrancar mitmproxy.
3. Preparar certificado dentro del perfil.
4. Lanzar Camoufox apuntando a `http://127.0.0.1:<port>`.
5. Registrar procesos y emitir evento de perfil listo.

Criterios de aceptacion:

- El navegador de un perfil usa su proxy y storage aislado.
- Reiniciar un perfil conserva cookies solo dentro de su propio directorio.
- Un error de certificado falla de forma visible y recuperable.

## Hito 2.6: pruebas de integracion

Usar un servidor local controlado para evitar tocar sistemas de terceros.

Casos minimos:

- Crear perfil con `allowed_hosts=["127.0.0.1", "localhost"]`.
- Lanzar mitmproxy y Camoufox.
- Visitar endpoint HTTP local y capturar flow.
- Visitar endpoint HTTPS local con certificado gestionado.
- Pausar request permitido, modificar header benigno y reenviar.
- Intentar replay contra host fuera de alcance y verificar rechazo.
- Detener perfil y comprobar limpieza de procesos.

## Riesgos tecnicos

- Instalacion de CA en perfiles Firefox/Camoufox puede variar por version.
- Windows/WSL requiere cuidado con rutas, puertos y procesos hijo.
- Capturar bodies completos puede crecer rapido; definir cuotas desde el inicio.
- El streaming en vivo debe tolerar desconexiones del frontend.
- Los stubs de agentes deben mantenerse como revisores y no como ejecutores autonomos.

## Definicion de terminado

La fase 2 termina cuando un operador puede crear un perfil autorizado, lanzar Camoufox con mitmproxy local, ver historial de trafico, pausar un request permitido, reenviarlo manualmente, detener el perfil y obtener logs de auditoria reproducibles sin modificar trust stores globales ni tocar activos fuera de alcance.
