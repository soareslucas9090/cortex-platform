#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env.production ]; then
  echo "Arquivo .env.production não encontrado. Copie de .env.production.example e preencha." >&2
  exit 1
fi
set -a
# shellcheck source=/dev/null
source .env.production
set +a
if [ -z "${CORTEX_DOMAIN:-}" ] || [ "${CORTEX_DOMAIN}" = "_" ]; then
  echo "Defina CORTEX_DOMAIN em .env.production." >&2
  exit 1
fi
if [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
  echo "Defina LETSENCRYPT_EMAIL em .env.production." >&2
  exit 1
fi
docker compose -f docker-compose-production.yml --env-file .env.production --profile tools run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$CORTEX_DOMAIN" \
  --email "$LETSENCRYPT_EMAIL" \
  --agree-tos --no-eff-email --non-interactive
docker compose -f docker-compose-production.yml --env-file .env.production up -d --force-recreate --no-deps nginx
echo "Nginx recriado com HTTPS (certificado em /etc/letsencrypt/live/${CORTEX_DOMAIN}/)."
