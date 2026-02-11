# Análisis técnico de ECU Vías Bot (enfoque producción 24/7)

## 1) Diagnóstico de arquitectura actual

- El proyecto mezcla en `main.py` responsabilidades de arranque del bot, inicialización ORM, configuración de persistencia, y control del ciclo de vida del proceso.
- La sincronización de datos (`sync_db`) se ejecuta en un hilo aparte con un event loop independiente, mientras el bot usa su propio loop principal.
- El scraping y persistencia histórica se acoplan de forma directa en `bot/db/manager.py`.
- La configuración depende de `pydantic-settings`, pero hay claves rotas/inconsistentes y rutas no válidas.

## 2) Hallazgos críticos

### Concurrencia y estabilidad
- `sync_db()` es una corrutina `async`, pero usa `time.sleep()` en bucle infinito. Esto bloquea el hilo/event-loop de sincronización y dificulta cancelación limpia.
- El flujo de notificaciones usa datos en `context.user_data`, no una capa de dominio persistente de suscripciones.

### Bugs funcionales graves
- `alarm_notifications` usa un string literal (`"ONCE_A_DAY[time]"`) en lugar de `datetime.time`, lo que rompe `job_queue.run_daily`.
- `notifications` sobrescribe `context.user_data['times']` con el string `'times'`.
- `unsubscription` retorna estados (`settings.UNSUBSCRIBE`) no definidos en settings.
- `config` está sin implementación (`pass`).

### Consistencia de i18n y UX
- Menús y textos tienen referencias incompatibles con `locale/es.json` (ej. `trans.suscriptor.sms_continue` no existe).
- El fallback del ConversationHandler compara con un texto de “stop” que no coincide con el botón real del menú principal.

### Persistencia y scheduler
- Las suscripciones no están modeladas en DB; la configuración de usuario depende de memoria/persistence del bot.
- No existe recuperación explícita de trabajos al reiniciar proceso.

### Scraping y resiliencia externa
- Scraping usa `verify=False` para TLS, sin validación robusta ni estrategia de retry/backoff.
- No hay manejo de “schema drift” si cambia el JSON remoto (acceso profundo con `get` encadenado y supuestos de estructura).

### Deploy
- `Dockerfile` referencia `requirements.txt` y `COPY ecuvias-bot .` que no existen/son inconsistentes con el repo actual.
- `compose.yaml` usa `build.context: ecuvias-bot`, también inconsistente.

## 3) Riesgos para producción

- Pérdida de notificaciones o programación inválida por errores de scheduler.
- Bot caído ante cambios menores del endpoint ECU911.
- Estados conversacionales corruptos por inconsistencias de traducciones y claves.
- Dificultad para escalar por ausencia de un modelo de suscripción normalizado y jobs persistentes.
- Observabilidad insuficiente para operar 24/7 (logs sin estructura ni alerting).

## 4) Propuesta de arquitectura objetivo

### Componentes
1. **Bot API layer** (Telegram handlers)
   - Solo validación de input + delegación a servicios.
2. **Application services**
   - `SubscriptionService`, `NotificationService`, `RoadStateService`.
3. **Data ingestion worker**
   - Proceso independiente para scraping periódico y deduplicación de cambios.
4. **Scheduler worker**
   - APScheduler con JobStore SQL o Celery Beat + Workers.
5. **Persistence layer**
   - PostgreSQL (producción) + Redis (cache/locks/rate-limits).

### Modelo mínimo de datos
- `users(id, telegram_id, language, timezone, created_at)`
- `subscriptions(id, user_id, province, via_filter, active)`
- `notification_policies(id, user_id, cron_expr, only_on_change, priority)`
- `road_events(id, province, via, state, observations, source_ts, hash)`
- `delivery_log(id, user_id, policy_id, event_id, sent_at, status, error)`

## 5) Rendimiento y optimización

- Cambiar polling de scraping a un **intervalo adaptativo** + jitter.
- Implementar **conditional fetch** (ETag/If-Modified-Since si el proveedor lo soporta).
- Calcular hash por evento para notificar solo cambios.
- Desacoplar scraping del bot para evitar que latencias externas afecten la UX.
- Limitar fanout de notificaciones con colas (batching por usuario/provincia).

## 6) Seguridad

- Token del bot solo por variables de entorno/secret manager.
- Rate limiting por usuario/chat (Redis token bucket).
- Validación estricta de entradas (white-list para comandos y opciones de teclado).
- Evitar `pickle` para persistencia de datos si no es estrictamente necesario.
- Hardening de dependencias y fijar versiones.

## 7) Plan de migración incremental

1. Corregir bugs críticos de conversación/notificaciones.
2. Introducir capa de servicios + repositorio.
3. Persistir suscripciones y políticas en DB.
4. Mover scraping a worker separado con retries y circuit-breaker.
5. Migrar scheduler a APScheduler/Celery con persistencia.
6. Añadir observabilidad (logs JSON + métricas + alertas).
7. Ajustar Docker/Compose/CI para despliegue reproducible.

## 8) Checklist de producción 24/7

- Healthchecks de bot, worker y scheduler.
- Retries con backoff exponencial + dead letter policy.
- Idempotencia en envíos (`delivery_log` + unique constraints).
- Alertas (Sentry/Prometheus/Grafana) para errores y retrasos de scraping.
- Backups de base de datos y política de retención.
