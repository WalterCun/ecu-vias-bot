# Build

docker build -t ecuvias-bot .


# Deploy

docker run -p 80:80 ecuvias_bot

docker run -it nombre-del-bot:latest


# Build and Deploy
``` yml

docker build -t ecuvias-bot . && docker run -it -p 80:80 --name bot ecuvias-bot

docker run --name redis-vias-bot -p 6379:6379 -v vol-vias-bot:/data -d redis

```
