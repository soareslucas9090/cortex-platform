#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec docker compose --env-file docker/.env.docker -f docker/docker-compose-production.yml "$@"
