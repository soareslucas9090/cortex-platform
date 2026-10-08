#!/bin/sh
set -eu
export CORTEX_DOMAIN="${CORTEX_DOMAIN:-_}"
if [ -f "/etc/letsencrypt/live/${CORTEX_DOMAIN}/fullchain.pem" ]; then
  template=/etc/nginx/templates-src/https.conf.template
else
  template=/etc/nginx/templates-src/http.conf.template
fi
envsubst '${CORTEX_DOMAIN}' < "$template" > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
