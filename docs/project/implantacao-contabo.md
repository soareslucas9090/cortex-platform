# Implantação na Contabo

Este guia deixa a API do Cortex no ar numa VPS da Contabo, em Docker, junto com outro projeto. Os dois ficam atrás de um único Caddy, que emite o HTTPS. PostgreSQL e Redis do Cortex não recebem porta pública.

A API deste projeto escuta só em `127.0.0.1:8010`. O outro projeto usa outra porta de localhost, por exemplo `127.0.0.1:8020`.

O código já está na VPS (neste guia, em `/opt/cortex`) e o banco já tem os dados no volume do Postgres. Os comandos partem do usuário `deploy`. Troque o domínio `api.seudominio.com` pelo seu.

O atalho `sh docker/producao.sh` sempre lê `docker/docker-compose-production.yml` e `docker/.env.docker`. O arquivo `docker/docker-compose.yml` é o ambiente local, com depurador e portas abertas. Na VPS ele não entra.

| Peça | Onde |
| --- | --- |
| API, worker, Beat, Postgres 18 e Redis | `docker/docker-compose-production.yml` |
| Variáveis da VPS | `docker/.env.docker`, a partir de `docker/.env.production.example` |
| Atalho de produção | `docker/producao.sh` |
| HTTPS da VPS, dos dois projetos | `docker/edge/` |

## 1. Usuário de trabalho

**Para que serve.** A VPS chega com acesso de root. O restante do guia roda com um usuário comum que pode usar `sudo` e, no passo seguinte, o Docker. Assim o dia a dia da API não fica na conta de root.

```bash
apt update && apt upgrade -y
adduser deploy
usermod -aG sudo deploy
```

Se a entrada for por chave SSH, copie a chave para o usuário novo antes de sair da sessão do root:

```bash
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

**Depois deste passo.** O sistema está atualizado. Existe o usuário `deploy`, com sudo. A sessão seguinte é `ssh deploy@IP_DA_VPS`. Root continua existindo, mas não é mais a conta dos comandos abaixo.

## 2. Firewall

**Para que serve.** A VPS só precisa receber SSH, o HTTP (para o Caddy pedir o certificado) e o HTTPS (para o público chegar na API). Banco, Redis e a porta 8010 ficam de fora: a API é alcançada pelo Caddy, na própria máquina.

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

**Depois deste passo.** Novas conexões de fora só entram nas portas 22, 80 e 443. O que já estava liberado pelo OpenSSH permanece. Ainda não há Docker, API nem certificado.

## 3. Docker

**Para que serve.** Instala o Docker Engine e o plugin Compose na Ubuntu ou Debian. É o runtime de todos os containers deste projeto e do outro.

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

**Depois deste passo.** `deploy` consegue rodar `docker` e `docker compose` sem sudo. Nenhum container do Cortex está no ar. O firewall do passo anterior continua valendo.

## 4. DNS

**Para que serve.** O Caddy só emite o certificado se o domínio já apontar para o IP público da VPS. Este passo é no provedor do domínio, não na VPS.

| Nome | Tipo | Valor |
| --- | --- | --- |
| `api` | A | IP público da VPS |

O outro projeto ganha outro nome (`app`, `outro`, etc.) no mesmo IP. Espere o nome responder antes de subir o Caddy:

```bash
ping api.seudominio.com
```

**Depois deste passo.** `api.seudominio.com` resolve para a VPS. Ainda não há serviço escutando em 80 ou 443, então o navegador não abre a API.

## 5. Variáveis de produção

**Para que serve.** O Compose de produção lê `docker/.env.docker`. Esse arquivo guarda o domínio, a senha do Postgres, a chave do Django, o CORS e as credenciais de e-mail e S3. Ele não entra no Git.

Na pasta do projeto:

```bash
cd /opt/cortex
cp docker/.env.production.example docker/.env.docker
nano docker/.env.docker
```

Ajuste:

- `DJANGO_SECRET_KEY`: a chave real do ambiente. Uma chave nova invalida os tokens JWT já emitidos.
- `SIMPLE_JWT_SIGNING_KEY`: a chave dedicada do JWT, se existir. Vazia, o Cortex usa a `DJANGO_SECRET_KEY`.
- `ALLOWED_HOSTS=api.seudominio.com`
- `CSRF_TRUSTED_ORIGINS=https://api.seudominio.com`
- `CORTEX_PUBLIC_BASE_URL=https://api.seudominio.com`
- `CORS_ALLOW_ALL_ORIGINS=False` e `CORS_ORIGIN_WHITELIST` com a origem exata do frontend (`https://...`). Várias origens vão separadas por vírgula.
- `DATABASE_PASSWORD` e `POSTGRES_PASSWORD`: a mesma senha. Os dois nomes existem porque o Django lê um e a imagem do Postgres lê o outro.
- `DATABASE_NAME`, `DATABASE_USER`, `POSTGRES_DB` e `POSTGRES_USER`: os quatro como `cortex`, a menos que todos mudem juntos.
- `CORTEX_HTTP_PORT=8010`, para deixar `8020` livre para o outro projeto.
- E-mail e `AWS_*`: os valores do armazenamento e do SMTP já usados pela API.

**Depois deste passo.** Existe `docker/.env.docker` só nesta máquina. Nenhum container subiu. A senha escrita aqui é a senha do Postgres que o container vai usar quando for criado pela primeira vez.

## 6. Postgres

**Para que serve.** Sobe só o banco, para confirmar que o container fica saudável antes da API. A imagem é `postgres:18`. O volume tem de estar em `/var/lib/postgresql`. No Postgres 18, montar em `/var/lib/postgresql/data` faz o container sair com código 1 e o status ficar `Restarting`.

```bash
cd /opt/cortex
sh docker/producao.sh up -d db
sh docker/producao.sh ps
```

Espere `cortex_db` em `healthy`.

**Depois deste passo.** Existe o container `cortex_db` e o volume `cortex_postgres_data`. Se esse volume já tinha dados, o Postgres 18 abre esse cluster. Se o volume é novo, a imagem cria o banco e o usuário definidos em `POSTGRES_DB` e `POSTGRES_USER`. Não há porta publicada no host: de fora da VPS o Postgres não responde. A API, o worker, o Beat, o Redis e o Caddy continuam desligados.

`sh docker/producao.sh down -v` apaga esse volume. Use isso só quando a intenção for descartar o banco.

## 7. API, worker e Beat

**Para que serve.** Constrói a imagem da API e sobe os três processos do Cortex, mais o Redis. O `web` aplica as migrações e coleta os arquivos estáticos antes do Gunicorn. O worker e o Beat só entram depois que `http://127.0.0.1:8000/health/` responde dentro do container.

```bash
cd /opt/cortex
sh docker/producao.sh up -d --build
sh docker/producao.sh ps
curl -sS http://127.0.0.1:8010/health/
```

A resposta do `curl` é `{"status": "ok"}`.

Há uma réplica só do Beat. Uma segunda réplica dispararia a mesma tarefa periódica duas vezes.

**Depois deste passo.** Estão no ar `cortex_db`, `cortex_redis`, `cortex_web`, `cortex_worker` e `cortex_beat`, na rede Docker `cortex_internal`. A API responde em `http://127.0.0.1:8010` nesta VPS. Da internet ela ainda não abre: a porta 8010 não está no firewall e o container só escuta em localhost. O volume `cortex_media_data` guarda os uploads locais. O volume `cortex_beat_schedule` guarda o relógio do Beat. Redis e Postgres continuam sem porta no host.

## 8. HTTPS

**Para que serve.** O Caddy é a porta de entrada da VPS inteira, não só do Cortex. Ele escuta 80 e 443, pede o certificado na Let's Encrypt e encaminha `api.seudominio.com` para `127.0.0.1:8010`. O outro projeto entra como mais um bloco no mesmo `Caddyfile`.

```bash
cd /opt/cortex/docker/edge
cp .env.example .env
nano .env
```

```text
ACME_EMAIL=voce@seudominio.com
CORTEX_DOMAIN=api.seudominio.com
CORTEX_HTTP_PORT=8010
```

`CORTEX_HTTP_PORT` é o mesmo valor de `docker/.env.docker`. O DNS do passo 4 já aponta para a VPS.

```bash
docker compose up -d
docker compose logs -f caddy
```

Abra:

```text
https://api.seudominio.com/health/
https://api.seudominio.com/cortex/api/schema/swagger/
```

**Depois deste passo.** O container `contabo_caddy` escuta 80 e 443 no host. O certificado de `api.seudominio.com` fica no volume `contabo_caddy_data`. Quem acessa o domínio cai na API do Cortex. O HTTP é encaminhado para HTTPS pelo Caddy. A porta 8010 continua só em localhost.

Para incluir o outro projeto, descomente o bloco dele em `docker/edge/Caddyfile` e recrie o proxy:

```bash
cd /opt/cortex/docker/edge
docker compose up -d
```

## 9. Conferir o Celery

**Para que serve.** Confirma que o Beat carregou a agenda e que o worker recebe as tarefas. A regra das rotas está em [Configuração do Celery Beat](configuracao-celery-beat.md).

```bash
cd /opt/cortex
sh docker/producao.sh logs -f beat worker
```

No Beat, a cada cinco minutos aparece o envio de `gerar-execucoes-rotas-pelo-calendario`, e a cada minuto o de `expirar-eventos-acesso`. No worker aparece o recebimento da tarefa.

**Depois deste passo.** Nada novo é instalado. Os mesmos cinco containers do passo 7 seguem no ar, e os logs mostram a agenda funcionando.

## 10. Usuário do admin

**Para que serve.** Cria um superusuário do Django no banco que já está no volume, para entrar no admin.

```bash
cd /opt/cortex
sh docker/producao.sh exec web python manage.py createsuperuser
```

O admin fica em `https://api.seudominio.com/cortex/admin/`.

**Depois deste passo.** Existe um usuário administrador no Postgres. Os containers não são recriados.

## 11. Publicar uma versão nova

**Para que serve.** Troca o código em execução pela revisão nova e recria os containers da API. As migrações rodam de novo na subida do `web`.

```bash
cd /opt/cortex
git pull
sh docker/producao.sh up -d --build
```

**Depois deste passo.** `cortex_web`, `cortex_worker` e `cortex_beat` rodam a imagem nova. Os volumes `cortex_postgres_data`, `cortex_media_data` e `cortex_beat_schedule` permanecem. O Caddy não precisa subir de novo se o domínio e a porta 8010 não mudaram.

## 12. Segundo projeto

**Para que serve.** Coloca o outro sistema na mesma VPS sem ocupar 80, 443 ou 8010 e sem um segundo Caddy.

- Outro diretório, por exemplo `/opt/outro-projeto`, com o Compose dele.
- Banco e Redis próprios, sem porta no host.
- A API dele só em `127.0.0.1:8020`.
- Um bloco novo no `docker/edge/Caddyfile`, como no passo 8.
- Outro registro A no DNS, no mesmo IP.

**Depois deste passo.** Os containers do Cortex seguem como estavam. O Caddy passa a ter dois sites. Cada projeto tem a sua rede, o seu banco e o seu Redis.

## Se algo falhar

| Sintoma | O que olhar |
| --- | --- |
| `cortex_db` em `Restarting (1)` com `postgres:18` | o volume do serviço `db` tem de ser `/var/lib/postgresql` |
| `sh docker/producao.sh` sobe uma imagem antiga | o atalho lê `docker/docker-compose-production.yml`, não `docker/docker-compose.yml` |
| `web` reinicia com `ALLOWED_HOSTS` ou `SECRET_KEY` | `docker/.env.docker` e `sh docker/producao.sh logs web` |
| `curl` em `127.0.0.1:8010` falha e o container está healthy | a porta publicada é a de `CORTEX_HTTP_PORT` |
| certificado não sai | DNS ainda não aponta para a VPS, ou 80/443 ocupados (`sudo ss -tlnp`) |
| o navegador mistura http | `CSRF_TRUSTED_ORIGINS` e `CORTEX_PUBLIC_BASE_URL` com `https://` |
| frontend bloqueado | `CORS_ORIGIN_WHITELIST` com a origem exata, incluindo `https://` |
| worker não conecta no Redis | o Compose já define `CELERY_BROKER_URL=redis://redis:6379/0` |
