# Cortex

Sistema backend para gestão institucional/acadêmica, construído com Django + DRF. Organiza identidade de usuários, vínculos organizacionais, perfis institucionais e vínculos acadêmicos em torno de uma entidade central de usuário.

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

---

## Visão Geral

O Cortex representa de forma consistente:

- **Quem são** os usuários e seus dados de identificação
- **Quais perfis** eles possuem (servidor, aluno, terceirizado, estagiário)
- **Como se vinculam** à instituição — setores, cargos, funções
- **Vínculos acadêmicos** — cursos, matrículas

O login é feito por **CPF** (não e-mail). Usuários são criados por administradores — não há auto-cadastro.

---

## Stack Técnica

| Componente       | Versão / Tecnologia                         |
| ---------------- | ------------------------------------------- |
| Linguagem        | Python 3.12+                                |
| Framework        | Django 5.2.7 + Django REST Framework 3.16.1 |
| Autenticação     | SimpleJWT 5.5.1 (tokens Bearer)             |
| Login social     | django-allauth 65.9.0                       |
| Banco de dados   | PostgreSQL (dev usa SQLite por padrão)      |
| Documentação API | drf-spectacular 0.28.0 (Swagger / ReDoc)    |
| Auditoria        | django-simple-history 3.10.1                |
| CORS             | django-cors-headers 4.9.0                   |
| Deploy           | Gunicorn (Linux) / Waitress (Windows)       |
| Assets estáticos | WhiteNoise 6.11.0                           |

---

## Estrutura do Projeto

O projeto é organizado por **domínios de negócio** — cada domínio é um pacote Python com inicial maiúscula, contendo um ou mais apps Django em minúsculo.

```
novo_cortex/
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
├── Identidade/                 # Domínio: identidade base do usuário
│   └── identidade/             # App Django
│       ├── models.py           # Usuario, Contato, Endereco, Matricula
│       ├── business.py
│       ├── rules.py
│       ├── helpers.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── Organizacional/             # Domínio: setores, funções, vínculos (em construção)
├── PessoasInstitucionais/      # Domínio: servidores, terceirizados (planejado)
├── Academico/                  # Domínio: alunos, cursos (planejado)
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
- PostgreSQL (opcional em desenvolvimento — SQLite é usado por padrão)

### Instalação

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd novo_cortex

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

# Banco de dados (deixe vazio para usar SQLite em dev)
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

---

## Endpoints da API

### Documentação interativa

| URL                    | Descrição                  |
| ---------------------- | -------------------------- |
| `/api/schema/swagger/` | Swagger UI                 |
| `/api/schema/redoc/`   | ReDoc                      |
| `/api/schema/`         | Schema OpenAPI (JSON/YAML) |

### Autenticação

| Método | URL                        | Descrição                      |
| ------ | -------------------------- | ------------------------------ |
| POST   | `/auth/token_jwt/`         | Login — obtém access + refresh |
| POST   | `/auth/token_jwt/refresh/` | Renova o access token          |
| POST   | `/auth/token_jwt/verify/`  | Verifica validade do token     |

### Identidade — Usuários

| Método | URL                                                    | Descrição                   |
| ------ | ------------------------------------------------------ | --------------------------- |
| GET    | `/identidade/usuarios/`                                | Listar usuários             |
| POST   | `/identidade/usuarios/`                                | Criar usuário               |
| GET    | `/identidade/usuarios/<pk>/`                           | Detalhar usuário            |
| PATCH  | `/identidade/usuarios/<pk>/`                           | Atualizar usuário           |
| POST   | `/identidade/usuarios/<pk>/desativar/`                 | Desativar usuário           |
| POST   | `/identidade/usuarios/<pk>/reativar/`                  | Reativar usuário            |
| GET    | `/identidade/usuarios/<pk>/contatos/`                  | Listar contatos             |
| POST   | `/identidade/usuarios/<pk>/contatos/`                  | Adicionar contato           |
| GET    | `/identidade/usuarios/<pk>/endereco/`                  | Obter endereço              |
| PUT    | `/identidade/usuarios/<pk>/endereco/`                  | Criar ou atualizar endereço |
| GET    | `/identidade/usuarios/<pk>/matriculas/`                | Listar matrículas           |
| POST   | `/identidade/usuarios/<pk>/matriculas/`                | Adicionar matrícula         |
| POST   | `/identidade/usuarios/<pk>/matriculas/<pk>/desativar/` | Desativar matrícula         |

---

## Autenticação

O sistema usa **JWT Bearer Tokens** com SimpleJWT:

- **Access token:** válido por 30 minutos
- **Refresh token:** válido por 7 dias
- **Header:** `Authorization: Bearer <token>`

O login é feito por **CPF**. O backend `EmailOrCpfBackend` suporta login por CPF ou e-mail.

```bash
# Exemplo de login
curl -X POST /auth/token_jwt/ \
  -H "Content-Type: application/json" \
  -d '{"username": "12345678901", "password": "SuaSenha@123"}'
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

- `Usuario` — entidade central, login por CPF
- `Contato` — e-mails e telefone
- `Endereco` — endereço residencial
- `Matricula` — carteirinha/matrícula institucional

### Organizacional _(em construção)_

Estrutura organizacional da instituição.

- `Setor` — setor dentro de um campus
- `Atividade` — atividade dentro de um setor
- `Funcao` — função exercida em uma atividade
- `UsuarioSetor` — vínculo entre usuário e setor (com papel de responsável/monitor)

### PessoasInstitucionais _(planejado)_

Perfis institucionais dos usuários.

- `Servidor` — servidor público (jornada 20h, 40h, DE)
- `Cargo` — posição formal do servidor
- `Terceirizado` — funcionário de empresa terceirizada
- `Empresa` — empresa ou instituição parceira

### Academico _(planejado)_

Perfil e vínculos acadêmicos.

- `Aluno` — aluno matriculado
- `Estagiario` — estagiário com vínculo em empresa
- `Curso` — curso ao qual o aluno pertence
