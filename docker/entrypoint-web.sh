#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn Cortex.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --forwarded-allow-ips "${GUNICORN_FORWARDED_ALLOW_IPS:-*}" \
  --access-logfile - \
  --error-logfile -
