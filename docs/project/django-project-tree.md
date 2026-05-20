# Árvore Inicial do Projeto Django

## Objetivo

Este documento define a estrutura inicial sugerida para o projeto Cortex, considerando:

- modularização por domínio;
- arquitetura em camadas já adotada no projeto base;
- convenção de nomenclatura definida para domínios e apps;
- crescimento incremental do sistema.

Este artefato não representa uma estrutura imutável, mas sim a **árvore inicial recomendada** para organizar o desenvolvimento do sistema com clareza e coesão.

---

## Convenções adotadas

### Domínio vs app

- **Domínio**: nome conceitual com inicial maiúscula
- **App Django**: nome técnico em minúsculo

Exemplos:

- Domínio: `Organizacional`
- app Django: `organizacional`

### Estrutura física por domínio

Cada domínio deve possuir um **módulo de domínio** próprio, preparado para agrupar apps relacionados daquele contexto de negócio.

Dentro desse módulo, os apps Django ficam organizados com nomes técnicos em minúsculo.

Exemplo:

```text name=estrutura-dominio-exemplo.txt
Organizacional/
└── organizacional/
```

### Princípio arquitetural

As views devem permanecer leves, delegando a lógica para a camada de business, que por sua vez coordena rules, helpers e state quando necessário.

---

## Estrutura inicial recomendada

```text name=project-tree.txt
novo_cortex/
├── docs/
│   ├── decisions/
│   │   └── ADR-001-modularizacao-por-dominio.md
│   ├── diagrams/
│   │   └── 02-bounded-contexts.md
│   ├── planning/
│   └── project/
│       ├── django-project-tree.md
│       └── implementation-checklist.md
│
├── AppCore/
│   ├── __init__.py
│   ├── basics/
│   ├── common/
│   └── core/
│
├── Auth/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   └── urls.py
│
├── Cortex/
│   ├── __init__.py
│   ├── asgi.py
│   ├── rest_framework_settings.py
│   ├── settings.py
│   ├── spectacular_settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── Identidade/
│   ├── __init__.py
│   └── identidade/
│       ├── __init__.py
│       ├── apps.py
│       ├── business.py
│       ├── helpers.py
│       ├── models.py
│       ├── rules.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
│
├── Organizacional/
│   ├── __init__.py
│   └── organizacional/
│       ├── __init__.py
│       ├── apps.py
│       ├── business.py
│       ├── choices.py
│       ├── helpers.py
│       ├── models.py
│       ├── rules.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
│
├── PessoasInstitucionais/
│   ├── __init__.py
│   └── pessoas_institucionais/
│       ├── __init__.py
│       ├── apps.py
│       ├── business.py
│       ├── choices.py
│       ├── helpers.py
│       ├── models.py
│       ├── rules.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
│
├── Academico/
│   ├── __init__.py
│   └── academico/
│       ├── __init__.py
│       ├── apps.py
│       ├── business.py
│       ├── choices.py
│       ├── helpers.py
│       ├── models.py
│       ├── rules.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
│
├── manage.py
├── db.sqlite3
└── venv/
```

---

## Descrição dos blocos principais

### `docs/`

Diretório responsável pela documentação viva do projeto.

#### Subpastas

- `docs/decisions/`: ADRs e decisões arquiteturais
- `docs/diagrams/`: visão de domínio, ERD, agregados e outros artefatos conceituais
- `docs/planning/`: planos e artefatos operacionais temporários de implementação
- `docs/project/`: estrutura do projeto, checklist e guias práticos de execução

---

### `AppCore/`

Camada base reutilizável do projeto.

Responsável por:

- classes base;
- mixins;
- exceptions;
- permissões;
- views base;
- paginação;
- autenticação genérica;
- helpers e infraestrutura compartilhada.

Esse módulo deve permanecer genérico e reutilizável, evitando conter regras específicas do domínio do Cortex.

---

### `Auth/`

App fino de autenticação do projeto.

Responsável por:

- customização do login;
- serializers específicos do projeto;
- integração com os endpoints de autenticação da base;
- eventual especialização futura do fluxo de acesso.

Observação:
A autenticação não substitui o domínio `Identidade`; ela representa o fluxo de acesso ao sistema.

---

### `Cortex/`

Pacote principal de configuração do projeto Django.

Responsável por:

- settings;
- urls globais;
- ASGI/WSGI;
- configurações de DRF e documentação.

---

## Módulos de domínio

O projeto é organizado em **módulos de domínio**, e cada módulo pode abrigar um ou mais apps relacionados daquele contexto de negócio.

Mesmo quando houver apenas um app inicialmente, a estrutura deve ser preparada para crescimento futuro.

---

## `Identidade/`

Domínio: `Identidade`

### App atual

- `identidade`

### Responsabilidade

Cadastro base da pessoa no sistema.

### Entidades esperadas

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

### Observações

Esse módulo deve ser criado primeiro, pois sustenta os demais domínios.

---

## `Organizacional/`

Domínio: `Organizacional`

### App atual

- `organizacional`

### Responsabilidade

Estrutura institucional e vínculo de usuários com setores.

### Entidades esperadas

- `Setor`
- `Funcao`
- `SetorVinculo`

### Observações

- `SetorVinculo` substitui `SetorLotacao`
- `Funcao` deve conter `e_gratificada`
- vínculo com setor sempre exige função
- monitoria deve ser modelada como função

---

## `PessoasInstitucionais/`

Domínio: `PessoasInstitucionais`

### App atual

- `pessoas_institucionais`

### Responsabilidade

Perfis institucionais formais vinculados ao usuário.

### Entidades esperadas

- `Servidor`
- `Cargo`
- `Terceirizado`
- `EmpresaInstituicao`

### Observações

- `Cargo` é exclusivo de `Servidor`
- `EmpresaInstituicao` será usada, neste momento, para terceirizados

---

## `Academico/`

Domínio: `Academico`

### App atual

- `academico`

### Responsabilidade

Perfis acadêmicos e vínculo com cursos.

### Entidades esperadas

- `Aluno`
- `Curso`
- `AlunoCurso`

### Observações

Monitoria não deve ser tratada como atributo isolado aqui, e sim pelo domínio `Organizacional`.

---

## Estrutura mínima por app

Cada app deve nascer, no mínimo, com os seguintes arquivos:

```text name=estrutura-minima-app.txt
app/
├── __init__.py
├── apps.py
├── business.py
├── helpers.py
├── models.py
├── rules.py
├── serializers.py
├── urls.py
└── views.py
```

Arquivos opcionais:

- `choices.py`
- `state.py`

---

## Sugestão de inclusão em `INSTALLED_APPS`

Quando os apps forem criados, a tendência é que entrem em `PROJECT_APPS` no `settings.py` com o caminho Python completo do app dentro do módulo de domínio.

Exemplo conceitual:

```python name=project_apps_example.py
PROJECT_APPS = [
    'Identidade.identidade',
    'Organizacional.organizacional',
    'PessoasInstitucionais.pessoas_institucionais',
    'Academico.academico',
]
```

---

## Sugestão de rotas globais

No `Cortex/urls.py`, a estrutura de inclusão deve seguir a ideia de separar as rotas por domínio.

Exemplo conceitual:

```python name=cortex_urls_example.py
urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
    path('auth/', include('Auth.urls')),

    path('identidade/', include('Identidade.identidade.urls')),
    path('organizacional/', include('Organizacional.organizacional.urls')),
    path('pessoas-institucionais/', include('PessoasInstitucionais.pessoas_institucionais.urls')),
    path('academico/', include('Academico.academico.urls')),
] + debug_toolbar_urls()
```

---

## Ordem recomendada de criação física dos módulos/apps

### 1. `Identidade/identidade`

Motivo:

- define `Usuario`, base para o restante do sistema

### 2. `Organizacional/organizacional`

Motivo:

- estrutura setores, funções e vínculos
- modela responsabilidade de setor e monitoria

### 3. `PessoasInstitucionais/pessoas_institucionais`

Motivo:

- especializa servidor e terceirizado
- introduz cargo e empresa

### 4. `Academico/academico`

Motivo:

- especializa aluno e curso
- pode aproveitar infraestrutura já consolidada

---

## Observações sobre crescimento futuro

Esta árvore inicial foi pensada para o estágio atual do sistema. Conforme o Cortex evoluir, será possível:

- adicionar novos apps dentro dos módulos de domínio já existentes;
- criar novos módulos de domínio quando necessário;
- introduzir `state.py` em domínios que demandem máquina de estados;
- extrair artefatos adicionais em `docs/` para detalhar agregados, fluxos e integrações.

A expansão do projeto deve preservar o princípio central desta árvore: **crescimento orientado por domínio, e não por conveniência técnica momentânea**.

---

## Próximos artefatos recomendados

Após este documento, recomenda-se manter e evoluir:

1. `docs/diagrams/03-core-erd.md`
2. `docs/diagrams/04-aggregates-and-invariants.md`
3. `docs/project/implementation-checklist.md`

---

## Resumo

A estrutura inicial do Cortex deve ser organizada em torno de módulos de domínio preparados para abrigar apps relacionados.

A recomendação inicial é usar:

- `Identidade/identidade`
- `Organizacional/organizacional`
- `PessoasInstitucionais/pessoas_institucionais`
- `Academico/academico`

Essa árvore aproveita a base reutilizável já existente, mantém a arquitetura em camadas e cria uma fundação clara para evolução incremental do sistema.
