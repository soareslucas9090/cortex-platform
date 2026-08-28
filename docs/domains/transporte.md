# Diretrizes do Domínio: Transporte

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Transporte** do projeto Cortex (MeuIF-Transporte).

## Visão Geral do Domínio

O domínio `Transporte` gerencia o transporte universitário. A v1 expõe o cadastro de **percursos** (RF017), usado depois pelas rotas.

### Modelos e Relacionamentos

- **Percurso**: trajeto nomeado do ônibus (`apelido` + `descricao`). Campo `ativo` no lugar de exclusão física. Relação futura 1:1 com `Rota` (ainda não implementada).

### Estrutura de Apps

```text
Transporte/
├── __init__.py
├── urls.py
└── percursos/       # App Django do model Percurso
```

## Regras Específicas do Domínio

### 1. Campos de Percurso

- `apelido`: identificador curto exibido na tela (ex.: "Rota R.SÃ"). Único, comparação case-insensitive.
- `descricao`: texto do trajeto (ex.: "IFPI – Posto R.Sã – FM – …").
- `ativo`: desativar/reativar no lugar de DELETE HTTP.

### 2. Permissões (perfil TI)

Toda a API de percursos exige **L3** (`EDITAR_TUDO`: `is_staff`, `is_admin` ou superusuário). Não é catálogo aberto.

O payload `user.permissoes.transporte.gerenciar` é `true` apenas para L3, para o frontend exibir o menu Transporte somente ao perfil TI.

### 3. Endpoints

Base: `/cortex/transporte/percursos/`

- `GET` / `POST` na raiz
- `GET` / `PATCH` em `<pk>/`
- `POST` `<pk>/desativar/` e `<pk>/reativar/`
- Listagem: `?ativo=true|false`, `?busca=` (apelido ou descrição), paginação `?paginacao=`
