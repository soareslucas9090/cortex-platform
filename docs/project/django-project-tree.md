# Estrutura Atual do Projeto Django

## Objetivo

Este documento descreve a estrutura arquitetural atual do Cortex, refletindo a organização real do projeto após a descentralização dos domínios em apps menores.

A estrutura do projeto segue estes princípios:

- organização por domínio;
- módulos agregadores por contexto de negócio;
- apps internos finos;
- regra preferencial de um app para um model principal;
- arquitetura em camadas;
- views leves baseadas nas BasicViews do AppCore.

---

## Princípios estruturais

### 1. Domínio não é app

No Cortex, um domínio representa um contexto de negócio e pode agrupar múltiplos apps internos.

Exemplos:

- `Identidade/`
- `Organizacional/`

Esses diretórios são **módulos de domínio**, e não apps Django isolados.

---

### 2. Cada app corresponde, em regra, a um model principal

A regra preferencial do projeto é:

- um app Django para um model principal.

Exceções aceitas:

- tabelas de domínio;
- tabelas auxiliares;
- relações many-to-many sem lógica própria relevante;
- casos explicitamente aprovados.

---

### 3. Estrutura física orientada por domínio

O projeto é organizado em três níveis principais:

1. **infraestrutura/base**
2. **módulos de domínio**
3. **apps internos do domínio**

---

## Estrutura macro atual

```text name=project-tree-current.txt
cortex-platform/
├── .github/
├── .vscode/
├── Academico/
├── AppCore/
├── Auth/
├── Cortex/
├── Identidade/
├── Infraestrutura/
├── Organizacional/
├── PessoasInstitucionais/
├── docs/
├── manage.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Blocos principais

### `AppCore/`

Camada base reutilizável do projeto.

Responsável por:

- classes base;
- BasicViews;
- mixins;
- autenticação base;
- exceptions;
- paginação;
- helpers e componentes compartilhados;
- armazenamento S3 e processamento de imagem em `AppCore/common/storage/`.

---

### `Auth/`

App fino responsável pelo fluxo de autenticação do projeto.

Ele não substitui o domínio de identidade.  
Seu papel é centralizar os endpoints e serializers de autenticação.

---

### `Cortex/`

Pacote principal de configuração do projeto Django.

Responsável por:

- settings;
- urls globais;
- configuração de DRF;
- configuração de documentação OpenAPI;
- ASGI/WSGI.

---

## Módulos de domínio atuais

### `Identidade/`

Domínio responsável pelos dados centrais de identidade do usuário.

#### Estrutura atual

```text name=identidade-module-tree.txt
Identidade/
├── __init__.py
├── urls.py
├── usuarios/
├── contatos/
├── enderecos/
└── matriculas/
```

#### Responsabilidades

- `usuarios/` → model principal `Usuario`
- `contatos/` → model principal `Contato`
- `enderecos/` → model principal `Endereco`
- `matriculas/` → model principal `Matricula`

---

### `Organizacional/`

Domínio responsável pela estrutura institucional e vínculos organizacionais.

#### Estrutura atual

```text name=organizacional-module-tree.txt
Organizacional/
├── __init__.py
├── urls.py
├── setores/
├── funcoes/
└── vinculos/
```

#### Responsabilidades

- `setores/` → model principal `Setor`
- `funcoes/` → model principal `Funcao`
- `vinculos/` → model principal `SetorVinculo`

---

## Estrutura esperada de um módulo de domínio

```text name=domain-module-pattern.txt
ModuloDominio/
├── __init__.py
├── urls.py
├── app_1/
├── app_2/
└── app_n/
```

### Regras

- o módulo de domínio agrega os apps internos;
- o `urls.py` do módulo é o ponto de entrada do domínio;
- o `Cortex/urls.py` inclui o módulo, não os apps internos diretamente.

---

## Estrutura esperada de um app interno

```text name=internal-app-pattern.txt
app_interno/
├── __init__.py
├── apps.py
├── models.py
├── business.py
├── rules.py
├── helpers.py
├── serializers.py
├── views.py
├── urls.py
├── tests.py
└── migrations/
```

Arquivos opcionais:

- `choices.py`
- `state.py`
- `selectors.py`, se um dia o projeto formalizar esse padrão
- outros arquivos auxiliares justificados

---

## Convenção de rotas

### `Cortex/urls.py`

Deve incluir apenas os módulos de domínio e apps estruturais globais.

Exemplo atual:

```python name=cortex-urls-pattern.py
urlpatterns = [
    path('cortex/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('cortex/admin/', admin.site.urls),
    path('cortex/auth/', include('Auth.urls')),
    path('cortex/identidade/', include('Identidade.urls')),
    path('cortex/organizacional/', include('Organizacional.urls')),
    path('cortex/pessoas-institucionais/', include('PessoasInstitucionais.urls')),
    path('cortex/academico/', include('Academico.urls')),
    path('cortex/infraestrutura/', include('Infraestrutura.urls')),
]
```

### `urls.py` do módulo de domínio

Deve agregar os apps internos do domínio.

Exemplo conceitual:

```python name=domain-urls-pattern.py
app_name = 'identidade'

urlpatterns = [
    path('usuarios/', include('Identidade.usuarios.urls')),
    path('contatos/', include('Identidade.contatos.urls')),
    path('enderecos/', include('Identidade.enderecos.urls')),
    path('matriculas/', include('Identidade.matriculas.urls')),
]
```

---

## Convenção de `INSTALLED_APPS`

O `settings.py` registra os apps internos, e não o módulo de domínio agregador.

Exemplo real atual:

```python name=project-apps-current.py
PROJECT_APPS = [
    'Identidade.usuarios',
    'Identidade.contatos',
    'Identidade.enderecos',
    'Identidade.matriculas',
    'Organizacional.setores',
    'Organizacional.funcoes',
    'Organizacional.vinculos',
    'PessoasInstitucionais.cargos',
    'PessoasInstitucionais.empresas_instituicoes',
    'PessoasInstitucionais.servidores',
    'PessoasInstitucionais.terceirizados',
    'Academico.cursos',
    'Academico.alunos',
    'Academico.aluno_cursos',
    'Infraestrutura.blocos',
    'Infraestrutura.salas',
    'Infraestrutura.recursos',
    'Infraestrutura.permissoes',
    'Infraestrutura.autorizacoes',
    'Infraestrutura.emprestimos',
]
```

Apps internos sem rotas HTTP próprias (suporte a regras e permissões) permanecem em `PROJECT_APPS`, mas não entram no `urls.py` agregador do domínio — exemplo: `Infraestrutura.permissoes`.

---

## Convenção de autenticação

O `AUTH_USER_MODEL` deve apontar para o app interno que contém o model real do usuário.

Exemplo atual:

```python name=auth-user-model-current.py
AUTH_USER_MODEL = 'usuarios.Usuario'
```

---

### `PessoasInstitucionais/`

Domínio responsável pelos perfis institucionais formais do usuário.

#### Estrutura atual

```text name=pessoas-institucionais-module-tree.txt
PessoasInstitucionais/
├── __init__.py
├── urls.py
├── cargos/
├── empresas_instituicoes/
├── servidores/
└── terceirizados/
```

#### Responsabilidades

- `cargos/` → model principal `Cargo`
- `empresas_instituicoes/` → model principal `EmpresaInstituicao`
- `servidores/` → model principal `Servidor`
- `terceirizados/` → model principal `Terceirizado`

---

### `Academico/`

Domínio responsável pelos perfis acadêmicos e vínculos com cursos.

#### Estrutura atual

```text name=academico-module-tree.txt
Academico/
├── __init__.py
├── urls.py
├── aluno_cursos/
├── alunos/
└── cursos/
```

#### Responsabilidades

- `alunos/` → model principal `Aluno`
- `cursos/` → model principal `Curso`
- `aluno_cursos/` → model principal `AlunoCurso`

---

### `Infraestrutura/`

Domínio responsável pelo cadastro de espaço físico, recursos, autorizações e empréstimos (substitui o fluxo legado do Chameco).

#### Estrutura atual

```text name=infraestrutura-module-tree.txt
Infraestrutura/
├── __init__.py
├── urls.py
├── blocos/
├── salas/
├── recursos/
├── permissoes/
├── autorizacoes/
└── emprestimos/
```

#### Responsabilidades

- `blocos/` → model principal `Bloco`
- `salas/` → models `Sala` e `SalaSetor`
- `recursos/` → model principal `Recurso`
- `permissoes/` → model `PermissaoFuncaoInfraestrutura` (capacidades por função; sem rotas HTTP)
- `autorizacoes/` → model principal `Autorizacao`
- `emprestimos/` → models de empréstimo multi-item

---

## Resumo

O Cortex atualmente adota:

- módulos de domínio como agregadores estruturais;
- apps internos finos;
- regra preferencial de um app por model principal;
- arquitetura em camadas;
- roteamento global por domínio;
- registro de apps no `settings.py` por app interno.

Essa estrutura substitui a visão anterior em que cada domínio era tratado como um único app principal.
