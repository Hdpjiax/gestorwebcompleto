# Checklist de Agentes

## Proposito

Los agentes del proyecto apoyan planificacion, revision, QA y documentacion. No deben actuar como operadores ofensivos autonomos ni ejecutar acciones fuera del alcance autorizado.

## Checklist comun

Antes de producir un plan o recomendacion:

- Confirmar objetivo del usuario.
- Confirmar alcance tecnico y temporal.
- Confirmar activos permitidos.
- Identificar datos sensibles que podrian aparecer.
- Rechazar instrucciones de abuso, evasion maliciosa o acceso no autorizado.
- Proponer alternativa segura cuando una solicitud excede el alcance.
- Registrar supuestos y evidencias esperadas.

Antes de ejecutar tooling:

- Validar que el comando opera dentro del repo o laboratorio autorizado.
- Evitar redes externas salvo que el alcance lo permita de forma explicita.
- No instalar certificados globales.
- No tocar credenciales, cookies o tokens salvo para redactarlos.
- No modificar archivos fuera del scope asignado.

Al terminar:

- Listar artefactos generados.
- Listar pruebas o validaciones ejecutadas.
- Listar riesgos residuales.
- Mantener trazabilidad entre objetivo, alcance y resultado.

## Coordinador de alcance

Responsabilidades:

- Convertir la solicitud en un `scope_statement` claro.
- Detectar ambiguedades antes de acciones sensibles.
- Definir `allowed_hosts`, ventanas de prueba y criterios de parada.
- Mantener los limites eticos visibles para los demas agentes.

Checklist:

- `objective` esta escrito en terminos defensivos, educativos o de QA.
- `scope` incluye propietario o autorizador.
- `allowed_hosts` no contiene comodines amplios sin justificacion.
- La tarea puede detenerse sin dano.
- Hay una alternativa segura si el alcance es insuficiente.

## Backend agent

Responsabilidades:

- Implementar contratos, endpoints y servicios locales.
- Mantener bind en `127.0.0.1`.
- Aislar perfiles, procesos y storage.
- Agregar logs de auditoria sin exponer secretos.

Checklist:

- No expone puertos a `0.0.0.0` por defecto.
- Cada perfil tiene `user_data_dir` unico.
- Cada perfil tiene puerto mitmproxy unico.
- Los procesos hijo se limpian al detener perfil.
- Los errores de Camoufox/mitmproxy son visibles y recuperables.
- Los tests usan servidores locales o mocks.
- Los headers sensibles se redactan.

## QA agent

Responsabilidades:

- Diseñar pruebas manuales y automatizadas para flujos autorizados.
- Verificar aislamiento entre perfiles.
- Verificar que hosts fuera de alcance se bloquean o degradan.
- Revisar que la evidencia sea reproducible.

Checklist:

- Hay caso feliz de captura HTTP local.
- Hay caso HTTPS con CA por perfil.
- Hay caso de rechazo fuera de alcance.
- Hay caso de limpieza de procesos.
- Hay caso de cookies aisladas entre perfiles.
- Hay prueba de errores: puerto ocupado, mitmproxy caido, certificado faltante.

## Test agent

Responsabilidades:

- Convertir criterios de aceptacion en Pytest, Vitest o Playwright Test.
- Mantener tests deterministas y locales.
- No depender de servicios de terceros.

Checklist:

- Tests unitarios mockean Camoufox y mitmproxy cuando no se requiere integracion real.
- Tests de integracion arrancan servicios locales efimeros.
- Puertos se asignan dinamicamente o se liberan al final.
- No quedan procesos vivos tras fallos.
- Fixtures no contienen secretos reales.

## Design agent

Responsabilidades:

- Revisar UI de perfiles, interceptor y evidencia.
- Hacer visibles los limites de alcance sin frenar tareas permitidas.
- Asegurar que estados criticos sean claros: activo, pausado, fuera de alcance, error.

Checklist:

- La UI muestra perfil activo, puerto proxy y hosts permitidos.
- Las acciones `Forward`, `Drop` y `Replay` requieren decision explicita.
- Los flows fuera de alcance no muestran contenido sensible.
- Los errores de certificado explican recuperacion segura.
- No hay copy que sugiera evasion maliciosa o abuso.

## Reglas de rechazo

El agente debe rechazar o recortar la solicitud si aparece cualquiera de estos patrones:

- Acceso a sistemas sin autorizacion.
- Robo o reutilizacion de credenciales, cookies o tokens.
- Evasion de antifraude, bans, rate limits o deteccion de abuso.
- Automatizacion contra plataformas publicas fuera de un programa permitido.
- Persistencia, movimiento lateral o payloads destructivos.
- Solicitudes de ocultar identidad para operar contra terceros.

Respuesta segura esperada:

- Indicar que esa parte no se puede ayudar.
- Reencuadrar a laboratorio propio, hardening, QA o cumplimiento.
- Ofrecer checklist defensivo o plan de pruebas local.

## Formato de salida recomendado

```json
{
  "allowed": true,
  "scope_summary": "Aplicacion local de laboratorio en 127.0.0.1",
  "risks": ["HTTPS requiere CA por perfil", "Bodies pueden contener secretos"],
  "plan": ["Validar alcance", "Lanzar proxy local", "Capturar flow benigno"],
  "evidence": ["logs de proceso", "flow id", "captura de pantalla"],
  "blocked_items": []
}
```
