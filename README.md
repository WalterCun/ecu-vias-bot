# ECU Vías Bot

Bot de Telegram para consultar y notificar estado de vías del Ecuador.

## Traducciones (ToolsTranslator)

Este proyecto usa **ToolsTranslator** como única capa de traducciones.

- Fuente principal: archivos locales `locale/*.json`.
- Flujo por defecto: local-first (sin dependencia de server).
- Server de traducción: opcional, para tareas asistidas/CLI.

### Principios

- El bot debe iniciar y operar normalmente solo con archivos locales.
- El cambio de idioma en caliente se hace por instancia (`trans.lang = "es"`, etc.).
- Claves faltantes se manejan según configuración de ToolsTranslator (`auto_add_missing_keys=False`).

## Build

```bash
docker build -t ecuvias-bot .
```

## Run

```bash
docker run -p 80:80 ecuvias-bot
```

## Redis (opcional para persistencia de estado)

```bash
docker run --name redis-vias-bot -p 6379:6379 -v vol-vias-bot:/data -d redis
```
