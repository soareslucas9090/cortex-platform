#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec docker compose -f docker-compose-production.yml --env-file .env.production "$@"
