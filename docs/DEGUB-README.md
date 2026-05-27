# Debugando com Docker

## Debug Remoto no VS Code (usando `debugpy`)

Para debugar usando breakpoints visuais na interface do VS Code:

1. **Instale temporariamente o `debugpy` e configure a execução**:
   No `docker-compose.yml`, ajuste o `command` do serviço `web` para executar através do `debugpy` e adicione a porta `5678`:

   ```yaml
     web:
       ...
       command: python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --nothreading --noreload
       ports:
         - '8000:8000'
         - '5678:5678'
   ```

   Exponha a porta de depuração do Celery (`5679`) e altere o `command` para rodar sob o `debugpy` mantendo o pool `prefork`:

   ```yaml
     worker:
       ...
       ports:
         - '5679:5679'
       command: python -m debugpy --listen 0.0.0.0:5679 -m celery -A Cortex worker -l INFO --pool=prefork --concurrency=${CELERY_CONCURRENCY:-4}
   ```

2. **Adicione a configuração no seu `.vscode/launch.json`**:
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
3. Suba o Docker Compose (`docker compose up`) e inicie a depuração no VS Code selecionando a configuração **"Django: Docker Attach"** e/ou **"Celery Docker"**.
