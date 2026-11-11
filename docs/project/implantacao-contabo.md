# Implantação na Contabo

Este guia sobe o Cortex numa VPS da Contabo, em Docker, junto com outro projeto. Os dois ficam atrás de um único Caddy, que emite o HTTPS. PostgreSQL e Redis do Cortex não ficam expostos na internet.

A API deste projeto escuta só em `127.0.0.1:8010`. O outro projeto deve usar outra porta de localhost, por exemplo `127.0.0.1:8020`.

## O que já fica pronto no repositório

| Peça | Onde |
| --- | --- |
| API, worker, Beat, Postgres e Redis | `docker/docker-compose-production.yml` |
| Variáveis da VPS | `docker/.env.production.example` |
| Atalho de produção | `docker/producao.sh` |
| HTTPS da VPS (os dois projetos) | `docker/edge/` |

O Compose de desenvolvimento (`docker/docker-compose.yml`) continua para a máquina local. Não use esse arquivo na VPS: ele abre Postgres, Redis e o depurador na rede.

## Antes de começar

Tenha em mãos:

- o IP público da VPS e um usuário com sudo;
- um domínio (ou subdomínio) só da API, por exemplo `api.seudominio.com`;
- o domínio do frontend, se existir, para o CORS;
- as Variables do serviço na Railway: `DJANGO_SECRET_KEY`, `SIMPLE_JWT_SIGNING_KEY`, e-mail e as chaves S3;
- a URL **pública** do Postgres da Railway (não a URL interna `*.railway.internal`).

A senha do Postgres da Contabo é nova. Não reutilize a senha da Railway no `DATABASE_PASSWORD` da VPS.

Recomendado: 4 GB de RAM ou mais, porque esta VPS roda dois projetos, cada um com banco, Redis e workers.

## 1. Primeiro acesso na VPS

Entre por SSH. Nos exemplos, o usuário é `deploy` e o IP é `203.0.113.10`. Troque pelos seus.

```bash
ssh root@203.0.113.10
```

Atualize o sistema e crie um usuário de trabalho:

```bash
apt update && apt upgrade -y
adduser deploy
usermod -aG sudo deploy
```

Se você usa chave SSH, copie a chave para o usuário novo antes de sair da sessão do root:

```bash
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Entre de novo como `deploy` e siga o resto do guia com esse usuário.

## 2. Firewall

Libere só SSH, HTTP e HTTPS. Não abra 5432, 6379 nem 8010.

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 3. Instalar o Docker

```bash
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
. /etc/os-release
sudo curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker deploy
```

Saia do SSH e entre de novo, para o grupo `docker` valer. Confirme:

```bash
docker compose version
```

## 4. DNS

No provedor do domínio, crie um registro **A**:

| Nome | Tipo | Valor |
| --- | --- | --- |
| `api` | A | IP público da VPS |

O mesmo IP recebe o domínio do outro projeto, em outro nome (`outro`, `app`, etc.). Espere o DNS responder antes de subir o Caddy. Da sua máquina:

```bash
ping api.seudominio.com
```

## 5. Código na VPS

```bash
sudo mkdir -p /opt/cortex
sudo chown deploy:deploy /opt/cortex
git clone <URL-DO-REPOSITORIO> /opt/cortex
cd /opt/cortex
```

## 6. Variáveis de produção

```bash
cp docker/.env.production.example docker/.env.docker
nano docker/.env.docker
```

Ajuste, no mínimo:

- `DJANGO_SECRET_KEY`: a mesma da Railway, ou uma nova (`python3 -c "import secrets; print(secrets.token_urlsafe(64))"`). Uma chave nova invalida os tokens JWT já emitidos; os usuários entram de novo.
- `SIMPLE_JWT_SIGNING_KEY`: copie a da Railway se ela existir lá. Se ficar vazia, o Cortex usa a `DJANGO_SECRET_KEY`.
- `ALLOWED_HOSTS=api.seudominio.com`
- `CSRF_TRUSTED_ORIGINS=https://api.seudominio.com`
- `CORS_ORIGIN_WHITELIST=https://app.seudominio.com` (o site que chama a API; vários origens separados por vírgula)
- `CORS_ALLOW_ALL_ORIGINS=False`
- `CORTEX_PUBLIC_BASE_URL=https://api.seudominio.com`
- `DATABASE_PASSWORD` e `POSTGRES_PASSWORD`: a mesma senha forte, nova
- `DATABASE_NAME`, `DATABASE_USER`, `POSTGRES_DB` e `POSTGRES_USER`: deixe `cortex` nos quatro, a menos que mude todos juntos
- e-mail e variáveis `AWS_*`: os mesmos valores da Railway

`CORTEX_HTTP_PORT=8010` deixa a porta 8020 livre para o outro projeto.

O arquivo `docker/.env.docker` não entra no Git.

## 7. Dump do banco da Railway

Rode na sua máquina (ou na VPS), com Docker instalado. Use a URL pública do plugin Postgres, no painel da Railway: Postgres → Connect → Public Network.

A URL se parece com:

```text
postgresql://postgres:SENHA@roundhouse.proxy.rlwy.net:12345/railway
```

Se a senha tiver `@`, `#` ou espaços, não cole a URL. Use o comando com `PGPASSWORD` abaixo e troque host, porta, usuário e banco.

**Na sua máquina Windows (PowerShell), na pasta onde o arquivo deve cair:**

```powershell
docker run --rm -e PGPASSWORD="SENHA_DA_RAILWAY" -e PGSSLMODE=require -v "${PWD}:/backup" postgres:16 pg_dump -h HOST_PUBLICO -p PORTA -U USUARIO -d BANCO --format=custom --no-owner --no-acl --verbose --file=/backup/cortex.dump
```

**No Linux ou no Git Bash:**

```bash
docker run --rm \
  -e PGPASSWORD='SENHA_DA_RAILWAY' \
  -e PGSSLMODE=require \
  -v "$PWD:/backup" \
  postgres:16 \
  pg_dump -h HOST_PUBLICO -p PORTA -U USUARIO -d BANCO \
  --format=custom --no-owner --no-acl --verbose \
  --file=/backup/cortex.dump
```

`--no-owner` e `--no-acl` existem porque o usuário `postgres` da Railway não existe na Contabo. O arquivo gerado é `cortex.dump`.

Envie o arquivo para a VPS, se o dump foi feito na sua máquina:

```powershell
scp .\cortex.dump deploy@203.0.113.10:/opt/cortex/cortex.dump
```

## 8. Subir só o Postgres e restaurar o dump

Na VPS, ainda **sem** a API:

```bash
cd /opt/cortex
sh docker/producao.sh up -d db
sh docker/producao.sh ps
```

Espere o status `healthy` de `cortex_db`. A primeira subida cria o banco vazio `cortex`.

**Instalar o dump nesse banco:**

```bash
docker exec -i cortex_db pg_restore -U cortex -d cortex --no-owner --no-acl --verbose < /opt/cortex/cortex.dump
```

Esse comando vale para o primeiro restore, com o banco vazio. Mensagens de aviso sobre objetos que o papel da Railway não possui podem aparecer; o restore segue. Confira no final se as tabelas existem:

```bash
docker exec -it cortex_db psql -U cortex -d cortex -c '\dt'
```

Se precisar repetir o restore em cima de um banco que já tem dados, acrescente `--clean --if-exists` antes de `<`. Isso apaga os objetos atuais e recria a partir do dump.

Apague o dump da VPS quando a conferência terminar. Ele contém a base inteira:

```bash
rm /opt/cortex/cortex.dump
```

## 9. Subir a API, o worker e o Beat

```bash
cd /opt/cortex
sh docker/producao.sh up -d --build
sh docker/producao.sh ps
sh docker/producao.sh logs -f web
```

O serviço `web` aplica as migrações e o `collectstatic` antes do Gunicorn. O worker e o Beat só sobem depois que `http://127.0.0.1:8000/health/` responde dentro do container.

Na própria VPS:

```bash
curl -sS http://127.0.0.1:8010/health/
```

A resposta esperada é `{"status": "ok"}`.

Há uma réplica só do Beat. Não suba uma segunda.

## 10. HTTPS com o Caddy

Este Caddy é da VPS, não só do Cortex. O outro projeto entra como mais um bloco no mesmo `Caddyfile`.

```bash
cd /opt/cortex/docker/edge
cp .env.example .env
nano .env
```

`.env` do edge:

```text
ACME_EMAIL=voce@seudominio.com
CORTEX_DOMAIN=api.seudominio.com
CORTEX_HTTP_PORT=8010
```

`CORTEX_HTTP_PORT` tem de ser o mesmo valor de `docker/.env.docker`.

Suba o proxy:

```bash
docker compose up -d
docker compose logs -f caddy
```

O Caddy pede o certificado na Let's Encrypt sozinho, desde que a porta 80 esteja livre e o DNS já aponte para a VPS. Abra no navegador:

```text
https://api.seudominio.com/health/
https://api.seudominio.com/cortex/api/schema/swagger/
```

Quando o outro projeto estiver no ar em `127.0.0.1:8020`, edite `docker/edge/Caddyfile`, descomente o bloco do segundo domínio e recarregue:

```bash
cd /opt/cortex/docker/edge
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Com `network_mode: host` o `exec` acima pode falhar em algumas versões. Nesse caso:

```bash
docker kill --signal=HUP contabo_caddy
```

Ou recrie o container: `docker compose up -d`.

## 11. Conferir o Celery

```bash
cd /opt/cortex
sh docker/producao.sh logs -f beat worker
```

O Beat deve registrar o agendamento. A cada cinco minutos aparece o envio de `gerar-execucoes-rotas-pelo-calendario`, e a cada minuto `expirar-eventos-acesso`. O worker registra o recebimento. Detalhe da regra de rotas: [Configuração do Celery Beat](configuracao-celery-beat.md).

## 12. Admin

```bash
sh docker/producao.sh exec web python manage.py createsuperuser
```

O admin fica em `https://api.seudominio.com/cortex/admin/`.

## 13. Atualizar uma versão nova

```bash
cd /opt/cortex
git pull
sh docker/producao.sh up -d --build
```

As migrações rodam na subida do `web`. O volume `cortex_postgres_data` e o volume de mídia `cortex_media_data` permanecem.

## 14. Segundo projeto, sem derrubar este

- outro diretório, por exemplo `/opt/outro-projeto`, com o Compose dele;
- banco e Redis próprios, sem publicar porta no host;
- a API dele só em `127.0.0.1:8020` (não use 80, 443 nem 8010);
- um bloco novo no `docker/edge/Caddyfile`;
- outro registro A no DNS, no mesmo IP.

Não suba um segundo Caddy. Não use o `docker-compose.yml` de desenvolvimento de nenhum dos dois na VPS.

## 15. Se algo falhar

| Sintoma | O que olhar |
| --- | --- |
| `web` reinicia com `ALLOWED_HOSTS` ou `SECRET_KEY` | `docker/.env.docker` e `sh docker/producao.sh logs web` |
| `curl` em `127.0.0.1:8010` falha, o container está healthy | a porta publicada é a de `CORTEX_HTTP_PORT` |
| certificado não sai | DNS ainda não aponta para a VPS, ou 80/443 ocupados (`sudo ss -tlnp`) |
| API abre no domínio e o navegador mistura http | `CSRF_TRUSTED_ORIGINS` e `CORTEX_PUBLIC_BASE_URL` com `https://` |
| frontend bloqueado | `CORS_ORIGIN_WHITELIST` com a origem exata, incluindo `https://` |
| worker não conecta no Redis | não troque `CELERY_BROKER_URL`; o Compose já aponta para `redis://redis:6379/0` |
| restore reclama de papel ou permissão | rode de novo com `--no-owner --no-acl`; não restaure como superusuário da Railway |

A Railway pode ficar ligada até você validar o domínio, o login e um fluxo real. Só então desligue o serviço de lá, para não ter dois ambientes recebendo escrita.
