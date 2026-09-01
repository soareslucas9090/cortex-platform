# Cortex

Sistema backend para gestão institucional/acadêmica, construído com Django + DRF. Organiza identidade de usuários, vínculos organizacionais, perfis institucionais e vínculos acadêmicos em torno de uma entidade central de usuário.

---

## Architecture Highlights

- Monólito modular organizado por domínios de negócio
- Arquitetura em camadas: View → Business → Rules → Helpers
- Framework interno reutilizável (AppCore)
- Autenticação JWT com login por CPF (ou matrícula)
- Documentação OpenAPI com Swagger/ReDoc
- Estrutura escalável preparada para integrações institucionais

---

## Sumário

- [Visão Geral](#visão-geral)
- [Stack Técnica](#stack-técnica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Rodando o Projeto](#rodando-o-projeto)
- [Endpoints da API](#endpoints-da-api)
- [Autenticação](#autenticação)
- [Arquitetura em Camadas](#arquitetura-em-camadas)
- [Domínios](#domínios)
- [Decisões Técnicas](#decisões-técnicas)

---

## Visão Geral

O Cortex representa de forma consistente:

- **Quem são** os usuários e seus dados de identificação
- **Quais perfis** eles possuem (servidor, aluno, terceirizado, estagiário)
- **Como se vinculam** à instituição — setores, cargos, funções
- **Vínculos acadêmicos** — cursos, matrículas

O login é feito por **CPF** ou **Matrícula** (não e-mail). Usuários são criados por administradores — não há auto-cadastro.

---

## Stack Técnica

| Componente       | Versão / Tecnologia                         |
| ---------------- | ------------------------------------------- |
| Linguagem        | Python 3.12+                                |
| Framework        | Django 5.2.7 + Django REST Framework 3.16.1 |
| Autenticação     | SimpleJWT 5.5.1 (tokens Bearer)             |
| Login social     | django-allauth 65.9.0                       |
| Banco de dados   | PostgreSQL                                  |
| Documentação API | drf-spectacular 0.28.0 (Swagger / ReDoc)    |
| Auditoria        | django-simple-history 3.10.1                |
| CORS             | django-cors-headers 4.9.0                   |
| Deploy           | Gunicorn (Linux) / Waitress (Windows)       |
| Assets estáticos | WhiteNoise 6.11.0                           |

---

## Estrutura do Projeto

O projeto é organizado por **domínios de negócio** — cada domínio é um pacote Python com inicial maiúscula, contendo um ou mais apps Django em minúsculo.

```
cortex-plataform/
│
├── AppCore/                    # Framework interno reutilizável
│   ├── basics/                 # Views base, mixins, paginação, auth, modelos base
│   └── core/                   # Business, Rules, Helpers, State, exceções
│
├── Auth/                       # Autenticação JWT (ponto de customização do projeto)
│
├── Cortex/                     # Configurações do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── Identidade/                 # Domínio: identidade base do usuário (módulo agregador)
│   ├── urls.py
│   ├── usuarios/               # App Django do model Usuario (com business.py, rules.py, etc.)
│   ├── contatos/               # App Django do model Contato
│   ├── enderecos/              # App Django do model Endereco
│   └── matriculas/             # App Django do model Matricula
│
├── Organizacional/             # Domínio: setores, funções, vínculos (módulo agregador)
│   ├── urls.py
│   ├── setores/                # App Django do model Setor
│   ├── funcoes/                # App Django do model Funcao
│   └── vinculos/               # App Django do model SetorVinculo
├── PessoasInstitucionais/      # Domínio: servidores, terceirizados, cargos
│   ├── urls.py
│   ├── cargos/
│   ├── servidores/
│   ├── empresas_instituicoes/
│   └── terceirizados/
├── Academico/                  # Domínio: alunos, cursos, vínculos acadêmicos
│   ├── urls.py
│   ├── alunos/
│   ├── cursos/
│   └── aluno_cursos/
├── Infraestrutura/             # Domínio: blocos, salas, recursos, empréstimos
│   ├── urls.py
│   ├── blocos/
│   ├── salas/
│   ├── recursos/
│   ├── permissoes/             # capacidades por função (sem rotas HTTP)
│   ├── autorizacoes/
│   └── emprestimos/
├── Transporte/                 # Domínio do transporte universitário e tickets
│   ├── urls.py
│   ├── percursos/
│   ├── rotas/
│   ├── execucoes_rotas/
│   ├── tickets/
│   ├── strikes/
│   └── justificativas/
│
├── docs/                       # Documentação do projeto
│   ├── decisions/              # ADRs (Architecture Decision Records)
│   ├── diagrams/               # Visão geral, bounded contexts, ERD
│   ├── planning/               # Planos de implementação
│   └── project/                # Checklists, riscos, análise do AppCore
│
├── manage.py
├── requirements.txt
└── .env                        # Não versionado — veja .env.example
```

---

## Configuração do Ambiente

### Pré-requisitos

- Python 3.12+
- PostgreSQL

### Instalação

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd cortex-plataform

# 2. Criar e ativar o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com as configurações do seu ambiente

# 5. Aplicar migrations
python manage.py migrate

# 6. Criar superusuário
python manage.py createsuperuser
```

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Django
DJANGO_SECRET_KEY=sua-chave-secreta-aqui
DJANGO_DEBUG=True

# Banco de dados
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=cortex_db
DATABASE_USER=postgres
DATABASE_PASSWORD=sua_senha
DATABASE_HOST=localhost
DATABASE_PORT=5432

# JWT (opcional em dev — usa DJANGO_SECRET_KEY como fallback)
SIMPLE_JWT_SIGNING_KEY=chave-dedicada-para-jwt

# CORS
CORS_ALLOW_ALL_ORIGINS=True          # apenas em dev
CORS_ORIGIN_WHITELIST=https://meudominio.com

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1

# E-mail (SMTP Gmail por padrão)
DEFAULT_FROM_EMAIL=noreply@meudominio.com
EMAIL_HOST_USER=seu@gmail.com
EMAIL_HOST_PASSWORD=senha-de-app
EMAIL_HOST=smtp.gmail.com
```

> **Em produção:** `DJANGO_SECRET_KEY` é obrigatória. O servidor recusará inicializar sem ela quando `DJANGO_DEBUG=False`.

---

## Rodando o Projeto

```bash
# Servidor de desenvolvimento
python manage.py runserver

# Criar novas migrations após alterar models
python manage.py makemigrations
python manage.py migrate

# Coletar arquivos estáticos (produção)
python manage.py collectstatic
```

### Rodando com Docker + Celery prefork

Use Docker quando quiser rodar o worker Celery com `prefork`, já que esse pool funciona corretamente em ambiente Linux e entrega paralelismo real entre processos. O comando `python manage.py celery_worker` foi criado para rodar o worker integrado ao autoreload do Django (e faz fallback automático para o pool `solo` quando executado localmente no Windows).

```bash
# 1. Criar o arquivo de ambiente para o cenário Docker
copy .env.docker.example .env.docker

# 2. Subir API, PostgreSQL, Redis e worker
docker compose up --build
```

Serviços disponíveis:

- API Django: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

O worker sobe usando um comando customizado do Django que adiciona suporte a autoreload, já configurado no `docker-compose.yml`:

```bash
python manage.py celery_worker -- --pool=prefork --concurrency=4
```

Para ajustar o número de processos, altere `CELERY_CONCURRENCY` no arquivo `.env.docker`.

> Importante: para usar `prefork` com segurança e ganho real, prefira PostgreSQL no Docker. SQLite não é uma boa base para múltiplos processos de worker concorrendo.

---

## Endpoints da API

### Documentação interativa

| URL                    | Descrição                  |
| ---------------------- | -------------------------- |
| `/cortex/api/schema/swagger/` | Swagger UI                 |
| `/cortex/api/schema/redoc/`   | ReDoc                      |
| `/cortex/api/schema/`         | Schema OpenAPI (JSON/YAML) |

Para gerar o arquivo de schema estático (`schema.yaml`) localmente via linha de comando:

```bash
python manage.py spectacular --file schema.yaml
```

### Autenticação

| Método | URL                        | Descrição                      |
| ------ | -------------------------- | ------------------------------ |
| POST   | `/cortex/auth/token_jwt/`         | Login — obtém access + refresh |
| POST   | `/cortex/auth/token_jwt/refresh/` | Renova o access token          |
| POST   | `/cortex/auth/token_jwt/verify/`  | Verifica validade do token     |

### Identidade — Usuários

| Método | URL                                                    | Descrição                   |
| ------ | ------------------------------------------------------ | --------------------------- |
| GET    | `/cortex/identidade/usuarios/`                                | Listar usuários             |
| POST   | `/cortex/identidade/usuarios/`                                | Criar usuário               |
| GET    | `/cortex/identidade/usuarios/<pk>/`                           | Detalhar usuário            |
| PATCH  | `/cortex/identidade/usuarios/<pk>/`                           | Atualizar usuário           |
| POST   | `/cortex/identidade/usuarios/<pk>/desativar/`                 | Desativar usuário           |
| POST   | `/cortex/identidade/usuarios/<pk>/reativar/`                  | Reativar usuário            |
| GET    | `/cortex/identidade/usuarios/<pk>/contatos/`                  | Listar contatos             |
| POST   | `/cortex/identidade/usuarios/<pk>/contatos/`                  | Adicionar contato           |
| GET    | `/cortex/identidade/usuarios/<pk>/endereco/`                  | Obter endereço              |
| PUT    | `/cortex/identidade/usuarios/<pk>/endereco/`                  | Criar ou atualizar endereço |
| GET    | `/cortex/identidade/usuarios/<pk>/matriculas/`                | Listar matrículas           |
| POST   | `/cortex/identidade/usuarios/<pk>/matriculas/`                | Adicionar matrícula         |
| POST   | `/cortex/identidade/usuarios/<pk>/matriculas/<pk>/desativar/` | Desativar matrícula         |

---

## Autenticação

O sistema usa **JWT Bearer Tokens** com SimpleJWT:

- **Access token:** válido por 1 dia
- **Refresh token:** válido por 7 dias
- **Header:** `Authorization: Bearer <token>`

O login é feito por **CPF** ou **Matrícula**. O backend `EmailOrCpfBackend` suporta login por CPF, Matrícula ou E-mail.

```bash
# Exemplo de login
curl -X POST /auth/token_jwt/ \
  -H "Content-Type: application/json" \
  -d '{"login": "12345678901", "password": "SuaSenha@123"}'
```

---

## Arquitetura em Camadas

Cada domínio segue uma arquitetura de 4 camadas. **Views são leves** — nunca contêm queries ORM ou lógica de negócio.

```
View  →  Business  →  Rules / Helpers / State
```

| Camada       | Arquivo       | Responsabilidade                                      |
| ------------ | ------------- | ----------------------------------------------------- |
| **View**     | `views.py`    | Recebe request, valida serializer, delega ao Business |
| **Business** | `business.py` | Orquestra operações, coordena Rules e Helpers         |
| **Rules**    | `rules.py`    | Valida SE uma ação pode ser executada                 |
| **Helpers**  | `helpers.py`  | Queries reutilizáveis e utilitários                   |
| **State**    | `state.py`    | Máquina de estados (futuro)                           |

As views herdam das views base do `AppCore` (`BasicPostAPIView`, `BasicGetAPIView`, `BasicRetrieveAPIView`, `BasicPutAPIView`, `BasicPatchAPIView`, `BasicDeleteAPIView`), que gerenciam transações, tratamento de exceções e paginação automaticamente.

### Exceções

O AppCore define exceções semânticas mapeadas para HTTP:

| Exceção                  | HTTP |
| ------------------------ | ---- |
| `BusinessRuleException`  | 400  |
| `ValidationException`    | 400  |
| `AuthorizationException` | 403  |
| `NotFoundException`      | 404  |
| `SystemErrorException`   | 500  |

---

## Domínios

### Identidade _(implementado)_

Cadastro base da pessoa no sistema.

- `Usuario` — entidade central, login por CPF ou Matrícula
- `Contato` — e-mails e telefone
- `Endereco` — endereço residencial
- `Matricula` — carteirinha/matrícula institucional

### Organizacional _(implementado)_

Estrutura organizacional da instituição.

- `Setor` — setor dentro de um campus (em `Organizacional.setores`)
- `Funcao` — função institucional/organizacional (em `Organizacional.funcoes`)
- `SetorVinculo` — vínculo entre usuário e setor, com papel de responsável e/ou monitor (em `Organizacional.vinculos`)

### PessoasInstitucionais _(implementado)_

Perfis institucionais dos usuários.

- `Servidor` — servidor público (jornada 20h, 40h, DE)
- `Cargo` — posição formal do servidor
- `Terceirizado` — funcionário de empresa terceirizada
- `EmpresaInstituicao` — empresa ou instituição parceira

### Academico _(implementado)_

Perfil e vínculos acadêmicos.

- `Aluno` — aluno matriculado
- `Curso` — curso oferecido pela instituição
- `AlunoCurso` — vínculo entre aluno e curso

### Infraestrutura _(implementado — v1)_

Cadastro de espaço físico, recursos, autorizações e empréstimos.

- `Bloco` — bloco físico do campus
- `Sala` / `SalaSetor` — salas e vínculo sala–setor
- `Recurso` — chaves e demais recursos emprestáveis
- `Autorizacao` — autorização por sala ou recurso
- `Emprestimo` — retirada e devolução multi-item
- `PermissaoFuncaoInfraestrutura` — capacidades por função (app interno sem rotas HTTP)

### Transporte _(implementado — rotas, tickets e embarque)_

Cadastro administrativo de percursos, rotas e execuções; alunos elegíveis podem
reservar tickets, acompanhar a fila PcD/FIFO e apresentar justificativas.

- `Percurso` — apelido, descrição do trajeto e status ativo/inativo
- `Rota` — percurso, horário de saída, dia da semana, quantidade de vagas e status ativo/inativo
- `ExecucaoRota` — ocorrência datada com horário e capacidade congelados
- `Ticket` — reserva, fila, cancelamento, embarque por QR Code ou ausência
- `Strike` e `Justificativa` — bloqueio após três faltas ativas e revisão por L3

## Decisões Técnicas

### Por que domínios modulares?

Cada contexto de negócio (Identidade, Organizacional, Acadêmico) cresce de forma independente. Novos domínios são adicionados sem tocar no código existente — sem acoplamento entre contextos, sem efeitos colaterais inesperados.

### Por que arquitetura em camadas?

Views que fazem queries ORM diretamente são um passivo de manutenção. Separar View, Business, Rules e Helpers garante que cada arquivo tenha uma única responsabilidade, facilita testes e torna o comportamento do sistema previsível.

### Por que login por CPF (ou Matrícula)?

O sistema é institucional e fechado — usuários são criados por administradores, não por auto-cadastro. O CPF é o identificador único institucional já consolidado nesse contexto. Para casos específicos onde o usuário ainda não possui CPF, o sistema permite o login através da matrícula. O e-mail torna-se irrelevante como chave principal de autenticação.
