# Deploy em VPS (Docker)

Tutorial operacional para subir o Cortex em produção com Docker Compose na própria VPS.

## 1. O que sobe na VPS

| Componente | Função | Exposição |
| --- | --- | --- |
| **nginx** | Proxy reverso, TLS, rate limit em login | Portas **80** e **443** no host |
| **web** | Django + Gunicorn | Só rede interna do Compose |
| **worker** | Celery worker (prefork) | Interno |
| **beat** | Celery Beat (uma única instância) | Interno |
| **db** | PostgreSQL 16 | Interno (sem porta no host) |
| **redis** | Broker/backend Celery | Interno (sem porta no host) |
| **media_data** | Uploads privados de importação (FileField) | Volume montado em web e worker; **não** servido pelo Nginx |
| **certbot** | Emissão/renovação TLS (profile `tools`) | Sob demanda via `compose run` |

Fotos de perfil vão para S3 via API; o volume de media não substitui o bucket.

## 2. Pré-requisitos

- Ubuntu (ou distro compatível) na VPS.
- [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) e plugin **Compose v2** (`docker compose`).
- Registro DNS **A** do domínio da API apontando para o IP público da VPS.
- Firewall liberando **80** e **443**; **não** abra **5432** nem **6379** para a internet.

## 3. Preparar o servidor

```bash
sudo apt update && sudo apt install -y git
sudo mkdir -p /opt/cortex
sudo chown "$USER":"$USER" /opt/cortex
git clone <url-do-repositorio> /opt/cortex
cd /opt/cortex/docker
cp .env.production.example .env.production
```

Gere chaves fortes (execute duas vezes, uma para cada variável):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Edite `.env.production`:

- `DJANGO_SECRET_KEY` e `SIMPLE_JWT_SIGNING_KEY` com os valores gerados.
- `DATABASE_PASSWORD` forte.
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ORIGIN_WHITELIST` alinhados ao domínio real.
- `CORTEX_DOMAIN`, `LETSENCRYPT_EMAIL`, `CORTEX_PUBLIC_BASE_URL` (HTTPS).
- Credenciais `AWS_*` do bucket S3.

O Compose acrescenta `,127.0.0.1` em `ALLOWED_HOSTS` do serviço web para o healthcheck interno.

## 4. Primeira subida (HTTP, sem certificado ainda)

```bash
chmod +x scripts/*.sh
./scripts/prod.sh up -d --build
```

Aguarde o container `cortex_prod_web` ficar **healthy** (`./scripts/prod.sh ps`).

Teste pelo IP ou domínio (ainda sem HTTPS se o certificado não existir):

```bash
curl -fsS http://SEU_IP_OU_DOMINIO/cortex/health/
```

Resposta esperada: `{"status":"ok"}`.

## 5. TLS (Let's Encrypt)

Com DNS propagado e Nginx respondendo em HTTP na porta 80:

```bash
./scripts/issue-certificate.sh
```

O script emite o certificado via webroot e recria o Nginx com o template HTTPS.

Renovação automática (cron no host, exemplo diário às 03:15). O script de renovação recarrega o Nginx sem recriar a stack:

```cron
15 3 * * * cd /opt/cortex/docker && ./scripts/renew-certificate.sh
```

Valide:

```bash
curl -fsS https://api.seudominio.com/cortex/health/
```

Documentação interativa: `https://api.seudominio.com/cortex/api/schema/swagger/`.

## 6. Processos e logs

```bash
./scripts/prod.sh ps
./scripts/prod.sh logs -f web worker beat
```

No **beat**, a cada cinco minutos deve aparecer atividade da tarefa `gerar-execucoes-rotas-pelo-calendario`.

**Nunca** escale o beat: `docker compose scale beat=2` é erro (agenda duplicada).

## 7. Atualizar versão

```bash
cd /opt/cortex
git pull
cd docker
./scripts/prod.sh up -d --build
```

Migrações rodam só no **web** (`RUN_MIGRATIONS=1` no entrypoint) antes do Gunicorn. Worker e beat dependem do web **healthy**.

## 8. Backup e restore

Backup:

```bash
./scripts/backup-db.sh
```

Restore (para dump completo, pare web, worker e beat antes):

```bash
./scripts/prod.sh stop web worker beat
./scripts/prod.sh exec -T db psql -U cortex -d cortex < backups/arquivo.sql
./scripts/prod.sh up -d
```

Agende `backup-db.sh` no cron do host.

## 9. Sair da Railway

1. No Railway, gere dump do Postgres (`pg_dump` pela connection string pública, CLI `railway connect` ou painel).
2. Copie o `.sql` para a VPS.
3. Suba a stack com banco vazio; pare web, worker e beat.
4. Restaure no serviço `db`: `./scripts/prod.sh exec -T db psql -U cortex -d cortex < arquivo.sql`.
5. Suba de novo os serviços.
6. Replique variáveis de ambiente (S3, e-mail, secrets). Pode manter o `DJANGO_SECRET_KEY` da Railway para não invalidar JWT/sessões em trânsito; se trocar, usuários precisam autenticar de novo.
7. Aponte o DNS da API para a VPS **somente** após `curl` HTTPS em `/cortex/health/` ok.

**Media de importação** no disco da Railway **não** vem no dump SQL. Se esses arquivos importam, copie o diretório `media` para o volume (`docker compose cp` ou container temporário). Fotos no S3 permanecem no bucket se as credenciais forem as mesmas.

## 10. Variáveis forçadas pelo Compose

Não adianta sobrescrever no `.env.production` para estes casos no stack de produção:

- `DATABASE_HOST=db`
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` = `redis://redis:6379/0`
- `DJANGO_DEBUG=False` em web, worker e beat

## 11. O que não fica exposto

- PostgreSQL e Redis sem `ports` no host.
- Gunicorn só na rede Docker (`web:8000`).
- Arquivos em `/app/media/` não são publicados pelo Nginx (`/media/` não é rota pública).

## 12. Desenvolvimento local

Continue usando `docker/docker-compose.yml`:

```bash
cd docker
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

Depuração com debugpy: [debug-docker.md](../debug-docker.md).
