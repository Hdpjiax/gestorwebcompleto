# Etica y Seguridad

## Politica de uso

Este proyecto esta limitado a ciberseguridad autorizada, educacion, laboratorios propios y operaciones profesionales con permiso documentado.

Antes de ejecutar una accion sensible, el sistema debe poder responder:

- Quien autorizo la actividad.
- Cual es el alcance tecnico y temporal.
- Que activos estan permitidos.
- Que evidencia se va a recolectar.
- Como se detiene la actividad si aparece riesgo.

## No permitido

- Acceso no autorizado a sistemas, cuentas o datos.
- Exfiltracion, robo de credenciales o evasion maliciosa.
- Persistencia, movimiento lateral o payloads destructivos fuera de laboratorios controlados.
- Automatizacion de abuso contra plataformas publicas.
- Uso de Camoufox para ocultar actividad ofensiva o saltar controles antifraude.

## Permitido

- Laboratorios locales o deliberadamente vulnerables.
- Auditorias con permiso escrito.
- QA de aplicaciones propias.
- Generacion de reportes, checklists y materiales educativos.
- Validaciones defensivas de configuracion y cumplimiento.

## Requisitos de implementacion

- Variables de entorno seguras por defecto.
- Confirmacion explicita de alcance para acciones sensibles.
- Logs de auditoria para ejecuciones automatizadas.
- Mensajes de error que expliquen limites sin ofrecer instrucciones abusivas.
