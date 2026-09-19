# Diretrizes do Domínio: Infraestrutura

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Infraestrutura** do projeto Cortex.

## Visão Geral do Domínio

O módulo **Infraestrutura** substitui o Chameco legado (levantamento anteriormente chamado Sigec). Está **implementado e operacional** na v1: cadastro de blocos, salas, recursos, autorizações, empréstimos multi-item e importação assíncrona via Celery.

- **Foco v1:** operação do guarda (retirada, devolução, consulta, troca de titular).
- **Reservas:** fazem parte do domínio de negócio, mas **não existem** no código (sem app `reservas`); não implementar na v1.
- **Não criar** módulo ou pasta `Sigec`; o agregador canônico é `Infraestrutura/` na raiz do projeto (ADR-001).

Referências complementares (não substituem este arquivo para agentes):

- [Schema consolidado](../schema/infraestrutura.md)
- [ADR-002: Permissões Cortex por Nível](../decisions/ADR-002-permissoes-cortex-niveis.md)
- [Importação de Infraestrutura (schema)](../schema/importacao-infraestrutura.md)
- [Importação de Infraestrutura (OpenAPI)](../api/importacao-infraestrutura-openapi.md)

### Dependências de outros domínios

| Domínio | Uso |
| ------- | --- |
| **Identidade** | `Usuario` (solicitante, responsável, beneficiário, concedente); `usuario_coletivo` e pool coletivo; `permissoes_infraestrutura()` |
| **Organizacional** | `Setor`, `Funcao`, `SetorVinculo` (retirada automática de chave por `SalaSetor`; capacidades via `PermissaoFuncaoInfraestrutura`) |
| **PessoasInstitucionais** | Perfis `Servidor` e `Terceirizado` nas regras automáticas de retirada |
| **Acadêmico** | Perfil `Aluno` (retirada só com autorização ou `retirada_irrestrita`) |

### Modelos e Relacionamentos

- **Bloco** → **Sala** (1:N).
- **Sala** ↔ **Setor** via **SalaSetor** (M:N; unicidade `sala` + `setor`).
- **Recurso** (código de negócio único; tipos chave / mídia / material didático).
- **Emprestimo** + **ItemEmprestimo** (multi-item; devolução parcial; encerramento quando todos os itens têm `devolvido_em`).
- **Autorizacao** (beneficiário; alvo XOR `sala` ou `recurso`; vigência e revogação).
- **PermissaoFuncaoInfraestrutura** / **PermissaoUsuarioInfraestrutura** (capacidades do módulo; **sem HTTP** — admin Django e compilação em login).
- **ImportacaoLote** (carga assíncrona; status e progresso).

Usuários não são espelhados localmente: sempre FK para `Identidade.usuarios.Usuario`.

### Estrutura de Apps

```text
Infraestrutura/
├── __init__.py
├── urls.py
├── blocos/           # Bloco
├── salas/            # Sala, SalaSetor
├── recursos/         # Recurso (+ foto S3)
├── autorizacoes/     # Autorizacao
├── emprestimos/      # Emprestimo, ItemEmprestimo
├── permissoes/       # PermissaoFuncaoInfraestrutura, PermissaoUsuarioInfraestrutura (sem urls)
└── importacoes/      # ImportacaoLote + tasks Celery
```

---

## Prefixo HTTP

Todas as rotas públicas do módulo ficam sob:

**`/cortex/infraestrutura/`**

(montagem em `Cortex/urls.py` → `Infraestrutura.urls`).

---

## Permissões: L1–L3 × capacidades do módulo

Dois eixos **independentes** (ver ADR-002):

### Níveis Cortex (Identidade)

Condicionam **escopo de leitura** em empréstimos e o papel típico do usuário:

| Nível | Empréstimos (sem `operar`) |
| ----- | --------------------------- |
| **L1** | Lista e detalhe apenas empréstimos **ativos** em que o usuário é **solicitante** |
| **L2+** | Mesmo escopo restrito **até** receber capacidade `operar` |

Quem tem **`operar`** (ou `is_admin` / superuser) consulta empréstimos abertos e encerrados com filtros amplos.

### Capacidades Infraestrutura (`user.permissoes['infraestrutura']`)

Compiladas em `UsuarioPermissions.permissoes_infraestrutura()` — **união OR** entre:

1. Flags em `PermissaoFuncaoInfraestrutura` das **funções** dos vínculos ativos (`SetorVinculo` com setor e função ativos).
2. Flags em `PermissaoUsuarioInfraestrutura` (OneToOne com usuário), para exceções (ex.: guarita).

| Capacidade | Libera (views) |
| ---------- | ---------------- |
| `operar` | POST empréstimo, devolução, troca de titular; listagens `solicitantes-elegiveis` / `responsaveis-elegiveis` |
| `cadastrar` | CRUD blocos, salas, salas-setores, recursos, fotos; importação em lote |
| `autorizar` | Listar, conceder, revogar e reativar autorizações |
| `retirada_irrestrita` | Solicitante pode retirar **qualquer** recurso (regra de elegibilidade, não substitui `operar` na guarita) |

`is_admin` e `is_superuser` recebem **todas** as capacidades via `usuario_tem_acesso_total_infraestrutura()` (`Infraestrutura/permissoes/access.py`).

**Manutenção:** alterar regra de permissão exige atualizar `documentacao_infraestrutura()` em `Identidade/usuarios/documentacao.py` no mesmo PR (ADR-002).

Catálogos físicos (blocos, salas, recursos): **GET autenticado** (`IsAuthenticatedMixin`). Escrita exige mixin de capacidade correspondente.

---

## Regras de negócio essenciais

### Retirada automática vs `Autorizacao`

Ordem de elegibilidade do solicitante (`EmprestimoHelpers.solicitante_pode_retirar_recurso`):

1. Capacidade compilada **`retirada_irrestrita`**
2. **Servidor** ativo → qualquer tipo de recurso
3. Se recurso tipo **chave**:
   - **Terceirizado** ativo → chaves em geral
   - Vínculo ativo em **setor** ligado à sala via **SalaSetor** → chaves daquela sala
4. Caso contrário → **`Autorizacao` vigente** (por recurso ou por sala abrangendo o recurso)

Alunos e demais perfis caem no passo 4 salvo `retirada_irrestrita`.

Implementação de autorização vigente: `EmprestimoHelpers._usuario_tem_autorizacao_vigente` (considera revogação e datas).

### Autorizações

- Alvo **XOR**: exatamente um de `sala_id` ou `recurso_id` (`AutorizacaoRules.validar_alvo_xor`).
- **Permanente:** `data_fim` nula; **temporária:** `data_fim` ≥ `data_inicio`.
- Autorização por **sala** vale para todos os recursos da sala (avaliação em runtime).
- **Revogação:** preenche `revogado_em` e `revogador`; endpoint `POST .../revogar/`. Reativação só para revogadas (`POST .../reativar/`).
- Conceder/revogar/reativar exige capacidade **`autorizar`**.

### Empréstimos

- **Multi-item** em um único `Emprestimo`; cada `ItemEmprestimo` devolve separadamente.
- Constraint: no máximo **um item aberto** por recurso (`emprestimos_item_recurso_unico_aberto`).
- **Solicitante:** usuário ativo, não coletivo.
- **Responsável:** quem registra a entrega na retirada.
  - Conta **não coletiva:** responsável = usuário autenticado (não informar outro).
  - Conta **`usuario_coletivo`:** obrigatório `responsavel_id` do pool (`Identidade` + `GET .../emprestimos/responsaveis-elegiveis/`).
- Conta coletiva **não** pode ser solicitante nem responsável (`UsuarioRules` / `EmprestimoRules`).
- **Troca de titular:** devolve itens em aberto e abre novo empréstimo (sem vínculo entre registros).
- **Atraso UI:** empréstimo ativo há mais de 24 h (`HORAS_ALERTA_ATRASO`).

### Recursos

- Tipo **chave** exige `sala`; mídia e material didático: sala opcional.
- Desativação bloqueada se houver empréstimo aberto.
- Foto opcional; proxy `GET /recursos/{pk}/foto/` (AllowAny); upload via `cadastrar`.

### Importação assíncrona

- Model **`ImportacaoLote`**: no máximo **um** lote `EM_ANDAMENTO` por instância (constraint).
- Processamento em **`Infraestrutura/importacoes/tasks.py`** (Celery).
- Endpoints sob `importacao/` exigem **`cadastrar`**.
- Formato e colunas: [importacao-infraestrutura.md](../schema/importacao-infraestrutura.md) e [importacao-infraestrutura-openapi.md](../api/importacao-infraestrutura-openapi.md).

---

## Endpoints principais

Paths relativos ao prefixo `/cortex/infraestrutura/`.

### Blocos

| Método | Path |
| ------ | ---- |
| GET, POST | `blocos/` |
| GET, PATCH | `blocos/{pk}/` |
| POST | `blocos/{pk}/desativar/`, `blocos/{pk}/reativar/` |

### Salas e vínculos sala–setor

| Método | Path |
| ------ | ---- |
| GET, POST | `salas/` |
| GET, PATCH | `salas/{pk}/` |
| POST | `salas/{pk}/desativar/`, `salas/{pk}/reativar/` |
| GET, POST | `salas-setores/` |
| DELETE | `salas-setores/{pk}/` |

### Recursos

| Método | Path |
| ------ | ---- |
| GET, POST | `recursos/` |
| GET, PATCH | `recursos/{pk}/` |
| GET, POST, DELETE | `recursos/{pk}/foto/` |
| POST | `recursos/{pk}/desativar/`, `recursos/{pk}/reativar/` |

### Autorizações

| Método | Path |
| ------ | ---- |
| GET, POST | `autorizacoes/` |
| GET | `autorizacoes/{pk}/` |
| POST | `autorizacoes/{pk}/revogar/`, `autorizacoes/{pk}/reativar/` |

### Empréstimos

| Método | Path |
| ------ | ---- |
| GET | `emprestimos/solicitantes-elegiveis/` |
| GET | `emprestimos/responsaveis-elegiveis/` |
| GET, POST | `emprestimos/` |
| GET | `emprestimos/{pk}/` |
| POST | `emprestimos/{pk}/devolver/` |
| POST | `emprestimos/{pk}/trocar-titular/` |

### Importação

| Método | Path |
| ------ | ---- |
| GET | `importacao/modelo/` |
| POST | `importacao/pre-visualizar/` |
| POST | `importacao/` |
| GET | `importacao/status/` |
| POST | `importacao/cancelar/` |
| GET | `importacao/historico/` |

---

## Camadas e arquivos de referência

| Assunto | Onde ler |
| ------- | -------- |
| Elegibilidade retirada | `Infraestrutura/emprestimos/helpers.py`, `rules.py` |
| Autorização XOR / vigência | `Infraestrutura/autorizacoes/rules.py`, `helpers.py` |
| Capacidades OR | `Infraestrutura/permissoes/helpers.py`, `Identidade/usuarios/permissions.py` |
| Mixins HTTP | `Infraestrutura/permissoes/access.py` |
| Importação | `Infraestrutura/importacoes/business.py`, `tasks.py`, `views.py` |

Fluxo padrão do projeto: **View → Business → Rules/Helpers**; `business.py` com try/except conforme [regras-do-projeto](../project/regras-do-projeto.md).

---

## O que NÃO fazer

- **Não** criar app `Sigec`, módulo paralelo ou duplicar `Usuario` localmente.
- **Não** implementar **reservas** ou app `reservas` sem marco de produto explícito.
- **Não** colocar flags de Infraestrutura em `Organizacional.funcoes.Funcao`; usar `PermissaoFuncaoInfraestrutura`.
- **Não** expor HTTP em `Infraestrutura/permissoes/`; configurar via Admin ou fluxo administrativo acordado.
- **Não** inventar endpoints ou prefixos fora de `urls.py` existentes.
- **Não** usar L3 Cortex como substituto de `operar` / `cadastrar` / `autorizar` (são capacidades separadas, salvo admin/superuser).
- **Não** permitir conta coletiva como solicitante ou responsável de empréstimo.
- **Não** copiar DER/PDF legado como fonte de verdade; o código e este doc prevalecem.
