# ECU Vías Bot

Bot de Telegram para consultar y notificar estado de vías del Ecuador.

## Enfoque de traducciones (local-first)

El proyecto usa archivos estáticos locales en `locale/*.json` como fuente principal de traducción.

- ✅ **Flujo principal**: archivos JSON locales.
- ⚠️ **Servidor de traducción**: opcional y fuera del flujo normal del bot.
- ✅ El bot debe iniciar y funcionar sin depender de Docker/servidor de traducción.

## Build

```bash
docker build -t ecuvias-bot .
```

## Run

```bash
docker run -p 80:80 ecuvias-bot
```

## Redis (opcional para persistencia)

```bash
docker run --name redis-vias-bot -p 6379:6379 -v vol-vias-bot:/data -d redis
```
