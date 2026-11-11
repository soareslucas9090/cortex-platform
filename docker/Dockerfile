FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/

# collectstatic não abre conexão com o banco. DEBUG fica ligado só neste passo.
ENV DJANGO_SECRET_KEY=collectstatic-build-only
ENV DJANGO_DEBUG=True
RUN python manage.py collectstatic --noinput \
    && chmod +x /app/docker/entrypoint-web.sh /app/docker/producao.sh

ENV DJANGO_DEBUG=False
ENV DJANGO_SECRET_KEY=TROQUE-ESTA-CHAVE-NO-ENV-ANTES-DE-SUBIR-PARA-PRODUCAO

EXPOSE 8000

CMD ["/app/docker/entrypoint-web.sh"]
