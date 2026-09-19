# Debugando com Docker

O Compose de desenvolvimento está em **`docker/docker-compose.yml`** (não na raiz do repositório). Suba a partir da pasta `docker/`:

```bash
cd docker
docker compose up
```

## Debug Remoto no VS Code (usando `debugpy`)

O serviço **web** já inicia com `debugpy` na porta **5678** e o **worker** na **5679** — não é necessário alterar o compose para depuração local.

Trecho atual (referência):

```yaml
  web:
    command: >
      sh -c "python manage.py migrate && python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --nothreading"
    ports:
      - '8000:8000'
      - '5678:5678'

  worker:
    command: python -m debugpy --listen 0.0.0.0:5679 manage.py celery_worker -- --pool=prefork --concurrency=${CELERY_CONCURRENCY:-4}
    ports:
      - '5679:5679'
```

### Configuração no `.vscode/launch.json`

Adicione (ou alinhe) as configurações de attach:

```json
{
  "name": "Django Docker",
  "type": "debugpy",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ],
  "django": true
},
{
  "name": "Celery Docker",
  "type": "debugpy",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5679
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ],
  "django": false,
  "subProcess": true
}
```

### Passos

1. Suba o Compose (`docker compose up` em `docker/`).
2. No VS Code, inicie a depuração com **"Django Docker"** (API) e/ou **"Celery Docker"** (tarefas assíncronas).
3. Coloque breakpoints no código montado em `/app` no container.
