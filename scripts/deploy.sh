#!/bin/sh
# Deploy Pet Lab to a remote Docker host (a NAS, a home server) over SSH:
# copy the sources, rebuild the image and restart the container.
#
#   cp deploy.env.example deploy.env   # then edit it
#   scripts/deploy.sh                  # sync, rebuild, restart
#   scripts/deploy.sh docs             # only update CLAUDE.md, .mcp.json and pet-ref
#
# Not needed if you run Docker on the machine you cloned to: there, just
# `docker compose up -d --build`.
set -e
cd "$(dirname "$0")/.."
[ -f deploy.env ] || { echo "create deploy.env first (see deploy.env.example)"; exit 1; }
. ./deploy.env

SSH="ssh ${PETLAB_SSH_KEY:+-i $PETLAB_SSH_KEY} -o BatchMode=yes $PETLAB_HOST"
DOCKER=${PETLAB_DOCKER:-docker}
COMPOSE=${PETLAB_COMPOSE:-docker compose}

$SSH "mkdir -p $PETLAB_DIR/workspace"
tar -cf - workspace/CLAUDE.md workspace/.mcp.json | $SSH "cd $PETLAB_DIR && tar -xf -"

if [ "$1" = docs ]; then
    tar -cf - pet-ref | $SSH "cd $PETLAB_DIR && tar -xf - && $DOCKER cp pet-ref/. pet-lab:/opt/pet-ref/"
    echo "docs synced"
    exit 0
fi

tar -cf - Dockerfile compose.yaml bin petlab pet-ref tests | $SSH "cd $PETLAB_DIR && tar -xf -"
# Build with plain `docker build` (some NAS Compose versions hang in BuildKit
# builds), then let Compose (re)create the container from the new image.
$SSH "cd $PETLAB_DIR && printf 'PETLAB_UID=%s\nPETLAB_GID=%s\n' '${PETLAB_UID:-1000}' '${PETLAB_GID:-1000}' > .env \
      && $DOCKER build --build-arg PETLAB_UID=${PETLAB_UID:-1000} --build-arg PETLAB_GID=${PETLAB_GID:-1000} -t pet-lab:latest . \
      && $COMPOSE up -d --force-recreate"
