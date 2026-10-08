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
docker compose -f docker-compose-production.yml --env-file .env.production --profile tools run --rm certbot renew \
  --webroot -w /var/www/certbot
docker compose -f docker-compose-production.yml --env-file .env.production exec nginx nginx -s reload
echo "Nginx recarregado com o certificado renovado."
