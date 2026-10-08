#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env.production ]; then
  echo "Arquivo .env.production não encontrado." >&2
  exit 1
fi
set -a
# shellcheck source=/dev/null
source .env.production
set +a
mkdir -p backups
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="backups/cortex-${STAMP}.sql"
docker compose -f docker-compose-production.yml --env-file .env.production exec -T db \
  pg_dump -U "$DATABASE_USER" -d "$DATABASE_NAME" --no-owner > "$OUT"
echo "Backup salvo em: $OUT"
