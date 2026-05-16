#!/bin/bash
# Construye y sube las imágenes Docker a DockerHub
# Usage: ./scripts/build-and-push.sh [tag]
# Default tag: latest

TAG=${1:-latest}
DOCKERHUB_USER=maosuarez

# sticker-api
docker build -t $DOCKERHUB_USER/sticker-api:$TAG ./sticker-api
docker push $DOCKERHUB_USER/sticker-api:$TAG

# sticker-db-service (cuando Nico lo entregue)
if [ -d "./sticker-db-service" ]; then
  docker build -t $DOCKERHUB_USER/sticker-db-service:$TAG ./sticker-db-service
  docker push $DOCKERHUB_USER/sticker-db-service:$TAG
fi

echo "Images pushed: $DOCKERHUB_USER/sticker-api:$TAG"
