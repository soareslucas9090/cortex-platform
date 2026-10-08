#!/bin/sh
set -eu

if [ "${SKIP_DROP_PRIVILEGES:-0}" = "1" ]; then
  if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    python manage.py migrate --noinput
  fi
  exec "$@"
fi

mkdir -p /app/media /var/lib/celery
chown cortex:cortex /app/media /var/lib/celery

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  runuser --user cortex -- python manage.py migrate --noinput
fi

exec runuser --user cortex -- "$@"
