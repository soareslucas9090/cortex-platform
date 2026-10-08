FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/sh cortex

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/static /app/staticfiles /app/media /var/lib/celery \
    && DJANGO_DEBUG=True DJANGO_SECRET_KEY=collectstatic-build-only \
       python manage.py collectstatic --noinput \
    && chmod -R a+rX /app/staticfiles \
    && chown -R cortex:cortex /app/media /var/lib/celery \
    && sed -i 's/\r$//' /app/docker/entrypoint.sh \
    && cp /app/docker/entrypoint.sh /entrypoint.sh \
    && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-c", "/app/docker/gunicorn.conf.py", "Cortex.wsgi:application"]
