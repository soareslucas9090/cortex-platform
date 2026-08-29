# ADR-002 — Permissões Cortex por Nível (L1–L3)

- **Status:** Aceito
- **Data:** 2026-07-10

## Contexto

O Cortex expõe permissões compiladas por módulo (`user.permissoes`) para o frontend e precisa aplicar regras coerentes nas views da API. O módulo `cortex` define três níveis hierárquicos derivados da identidade do usuário.

## Decisão

### Níveis Cortex

| Nível | Constante | Papel |
|-------|-----------|--------|
| 1 | `EDITAR_EU` | Empregado — lê/edita apenas recursos próprios |
| 2 | `LER_TUDO` | Gerente — leitura ampla; escrita apenas do próprio (onde aplicável) |
| 3 | `EDITAR_TUDO` | Master — leitura e escrita totais |

Derivação em `Identidade.usuarios.permissions.UsuarioPermissions.permissoes_cortex()`:

- `EDITAR_TUDO`: `is_staff`, `is_admin` ou `is_superuser`
- `LER_TUDO`: servidor ou terceirizado ativo
- `EDITAR_EU`: demais casos (ex.: aluno)

### Compilação e hooks

- `UserModelPermission.compilar_permissoes()` descobre métodos `permissoes_<modulo>()` e monta o dict.
- `Usuario` expõe `tem_acesso_elevado()` (L3) e `tem_leitura_ampla()` (L2+) para o AppCore sem acoplamento a Identidade.
- Helpers em `Identidade.usuarios.access`: `nivel_cortex`, `tem_nivel_cortex_minimo`, `escopar_queryset_cortex`.

### Mixins nas views

| Mixin | Uso |
|-------|-----|
| `IsAuthenticatedMixin` | Catálogos de referência (leitura para qualquer autenticado) |
| `IsOwnerOrAdminMixin` | Recursos com dono; escopo no `get_queryset` via `escopar_queryset_cortex` |
| `IsAdminMixin` | Escrita administrativa (L3 via `tem_acesso_elevado`) |

### Matriz de leitura (módulo cortex)

- **Catálogos** (setores, funções, cargos, cursos): autenticado → lista completa
- **Pessoas / vínculos pessoais**: L2+ → todos; L1 → só `request.user`
- **Empresas**: L2+ → todas; L1 → lista vazia

Query params **apenas estreitam** resultados após o escopo de permissão.

### Extensibilidade (ex.: Infraestrutura, Transporte)

Novos produtos adicionam `permissoes_<modulo>()` em `UsuarioPermissions` e apps Django dentro de um módulo de domínio na raiz (`Infraestrutura/`, `Transporte/`), nunca em pasta genérica `APPs/`. Subdomínios = apps internos do módulo (`Infraestrutura/recursos/`, `Transporte/percursos/`, etc.).

- **Infraestrutura:** capacidades booleanas (`operar`, `cadastrar`, `autorizar`, `retirada_irrestrita`), independentes de L1–L3.
- **Transporte:** capacidade `gerenciar` alinhada a L3 (`is_staff`, `is_admin` ou superusuário); toda a API de percursos e rotas usa `IsAdminMixin`.

### Documentação viva da API

- Endpoint: `GET /cortex/identidade/permissoes/documentacao/` (autenticado).
- Implementação: `PermissaoDocumentacao.compilar_documentacao()` em `Identidade.usuarios.documentacao`, espelhando `permissoes_*` com métodos `documentacao_<modulo>()`.
- **Regra de manutenção:** toda alteração de regra de permissão deve atualizar o `documentacao_<modulo>()` correspondente no mesmo PR/commit.

### Documentação de permissão em toda view (Swagger)

Toda view exposta na API **deve** declarar, na `description` do `@extend_schema`, um bloco **`**Permissões:**`** informando quem pode acessar o endpoint.

**Formato obrigatório:**

- Usar o vocabulário Cortex quando aplicável: **L1** (`EDITAR_EU`), **L2** (`LER_TUDO`), **L3** (`EDITAR_TUDO`).
- Endpoints públicos: `**Permissões:** Público (AllowAny — não requer autenticação).`
- Endpoints com leitura e escrita distintas: documentar ambos (ex.: leitura autenticada; escrita apenas L3).
- Endpoints com escopo por dono: indicar L2+ vs L1 (ex.: L2+ lista todos; L1 vê apenas o próprio).

**Exemplos:**

```
**Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).

**Permissões:** Autenticado. L2+ (LER_TUDO) lista todos; L1 (EDITAR_EU) vê apenas o próprio registro.

**Permissões:** L3 (EDITAR_TUDO) — administradores.

**Permissões:** Público (AllowAny — não requer autenticação).
```

**Regra de manutenção:** alterar mixin, escopo ou regra de acesso exige atualizar o bloco `**Permissões:**` da view no mesmo PR/commit.

## Consequências

- AppCore permanece genérico (duck-typing nos hooks do user).
- Documentação e testes cobrem escopo L1/L2/L3 por tipo de recurso.
- Swagger deve refletir permissões reais, não apenas “administradores”.
