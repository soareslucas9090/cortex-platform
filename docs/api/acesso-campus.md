# API — AcessoCampus (contrato planejado)

> **Status:** corte da **gestão** existe em `/cortex/acesso-campus/` (`acesso_campus`): `GET tipos/`, `GET tipos/{pk}/`, `GET alunos/`, `GET turmas/`, `POST autorizacoes/`, `GET solicitacoes/`, `GET solicitacoes/{pk}/`, `POST solicitacoes/{pk}/aceitar/`, `POST solicitacoes/{pk}/recusar/`. `tipo` nas autorizações é o id do catálogo (`TipoAutorizacaoAcesso`); Entrada no campus e Saída do campus são tipos-base; cadastro de tipo só no Django Admin. Os cinco papéis, quando são o responsável pelo setor, e o L3 alcançam qualquer Ensino Médio. O responsável pelo setor do curso alcança só esse curso. A listagem traz pedido do aluno e autorização da gestão. Criar ou aceitar recusa data passada e segunda autorização aceita do mesmo aluno, dia e tipo. O corte do **aluno** também existe: `GET/POST minhas-solicitacoes/` (lista própria — pedidos dele e autorizações da gestão para ele — com `status`, `tipo` (id do catálogo), `busca` e `ordenacao` = `data_liberacao`, `data_solicitacao`, `tipo`, `motivo`, `avaliado_por`, prefixo `-` inverte; padrão `-data_solicitacao`), `GET minhas-solicitacoes/{pk}/` e `GET solicitacoes/{pk}/anexo/` (comprovante via proxy autenticado: dono ou gestão com escopo). O POST exige `solicitar` (automático para aluno elegível de Ensino Médio) e recebe `aluno_curso`, `tipo` (só os tipos-base), `data_acesso`, `hora_solicitada`, `motivo` (≤ 100), `justificativa` (≤ 500) e `anexo` obrigatório (PDF/JPG/PNG ≤ 5 MB, `multipart/form-data`). Entrada para o próprio dia só até 07:00 (America/Fortaleza); recusa data passada, horário já passado no dia e pedido para dia e tipo em que o aluno já tem autorização aceita (pendentes não bloqueiam). O aluno não cancela pedido neste corte. O contrato abaixo, com programações, eventos e portaria, continua **planejado**.

Autenticação: JWT/sessão padrão Cortex (401 se ausente). Permissões de módulo na chave **`acesso_campus`** do payload compilado. **L3** acessa todos os recursos.

### Catálogo de tipos (implementado)

| Método | Path | name | Permissão |
|--------|------|------|-----------|
| GET | `tipos/` | `tipo-autorizacao-list` | Autenticado (catálogo de referência) |
| GET | `tipos/{pk}/` | `tipo-autorizacao-detail` | Autenticado (catálogo de referência) |

Filtros da lista: `ativo`, `nome`, `paginacao`. Sem POST/PATCH/desativar na API — cadastro só no Django Admin. `POST autorizacoes/` recebe `tipo` como **id** do catálogo (somente tipos ativos). Entrada no campus e Saída do campus são tipos-base (`eh_base`); não podem ser desativados.

Exceções: `ValidationException`, `BusinessRuleException` → **400**; `AuthorizationException` → **403**; `NotFoundException` → **404**.

---

## Matriz endpoint × capacidade

| Endpoint | Método | name | Capacidade mínima |
|----------|--------|------|-------------------|
| `solicitacoes/` | GET, POST | `solicitacao-list` | `solicitar` (escopo próprio) ou L3 |
| `solicitacoes/{pk}/` | GET | `solicitacao-detail` | `solicitar` (próprio) ou L3 |
| `solicitacoes/{pk}/cancelar/` | POST | `solicitacao-cancelar` | `solicitar` (próprio, PENDENTE) ou L3 |
| `analise/solicitacoes/` | GET | `analise-solicitacao-list` | `analisar_solicitacoes` ou L3 |
| `analise/solicitacoes/{pk}/` | GET | `analise-solicitacao-detail` | `analisar_solicitacoes` ou L3 |
| `analise/solicitacoes/{pk}/aprovar/` | POST | `analise-solicitacao-aprovar` | `analisar_solicitacoes` ou L3 |
| `analise/solicitacoes/{pk}/rejeitar/` | POST | `analise-solicitacao-rejeitar` | `analisar_solicitacoes` ou L3 |
| `analise/solicitacoes/{pk}/cancelar/` | POST | `analise-solicitacao-cancelar` | `analisar_solicitacoes` ou L3 (só APROVADA) |
| `portaria/eventos/` | GET | `evento-acesso-list` | `operar_portaria` ou L3 |
| `portaria/eventos/responsaveis-elegiveis/` | GET | `evento-acesso-responsaveis` | `operar_portaria` ou L3 |
| `portaria/eventos/{grupo_portaria_id}/` | GET | `evento-acesso-detail` | `operar_portaria` ou L3 |
| `portaria/eventos/{grupo_portaria_id}/alunos/` | GET | `evento-acesso-alunos` | `operar_portaria` ou L3 |
| `portaria/eventos/{grupo_portaria_id}/registrar/` | POST | `evento-acesso-registrar` | `operar_portaria` ou L3 |
| `historico/` | GET | `historico-list` | `visualizar_historico` ou `analisar_solicitacoes` ou L3 |
| `historico/{pk}/` | GET | `historico-detail` | idem |

Swagger: cada view com `@extend_schema` e bloco **`**Permissões:**`** (ADR-002).

---

## Objeto `confirmacao` (respostas de evento e solicitação detalhe)

Sempre presente:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `situacao_confirmacao` | string | `PENDENTE`, `NAO_EXIGIDA`, `RECEBIDA` (derivado) |
| `situacao_confirmacao_display` | string | Rótulo PT |
| `exige_confirmacao` | bool | Cópia congelada no evento; na solicitação, valor atual |
| `registro` | object \| null | Ver abaixo |

`registro` quando existir `RegistroAcesso`:

| Campo | Tipo |
|-------|------|
| `id` | int |
| `resultado` | int (`ResultadoRegistroAcesso`) |
| `resultado_display` | string |
| `registrado_em` | datetime ISO-8601 |
| `registrado_por` | `{ id, nome }` |
| `observacao` | string |

Regras derivadas: registro presente → `RECEBIDA`; sem registro e `exige_confirmacao` → `PENDENTE`; sem registro e não exige → `NAO_EXIGIDA`.

---

## Aluno — solicitações

### GET/POST `/cortex/acesso-campus/solicitacoes/`

- **name:** `solicitacao-list`
- **Permissões:** `solicitar` (lista apenas solicitações do aluno autenticado); L3 lista conforme escopo administrativo.

**GET — filtros:** `status` (int choice), `paginacao` (1–100).

**POST — body (exemplo compacto):**

```json
{
  "aluno_curso": 10,
  "justificativa": "Consulta médica.",
  "exige_confirmacao": true,
  "programacoes": [
    {
      "tipo": 1,
      "data_inicio": "2026-10-15",
      "data_fim": "2026-10-15",
      "hora_prevista": "09:30:00"
    }
  ]
}
```

**Resposta 201:** solicitação com `status=1` (PENDENTE), snapshots, programações aninhadas.

**Erros:** 400 elegibilidade/sobreposição/campos; 403 sem `solicitar`.

---

### GET `/cortex/acesso-campus/solicitacoes/{pk}/`

- **name:** `solicitacao-detail`
- **Permissões:** `solicitar` escopo próprio; L3.

**Resposta 200:** cabeçalho + programações + eventos (se já aprovada) cada um com `confirmacao`.

**Erros:** 404 fora do escopo.

---

### POST `/cortex/acesso-campus/solicitacoes/{pk}/cancelar/`

- **name:** `solicitacao-cancelar`
- **Permissões:** `solicitar` próprio; só `PENDENTE`.

**Body:** vazio ou `{}`.

**Resposta 200:** `status=4` (CANCELADA).

**Erros:** 400 se não PENDENTE.

---

## Gestão — análise

### GET `/cortex/acesso-campus/analise/solicitacoes/`

- **name:** `analise-solicitacao-list`
- **Permissões:** `analisar_solicitacoes` ou L3.

**Filtros:** `status` (default **1** PENDENTE), busca (nome/cpf/matrícula), `curso_id`, `data`, `paginacao`.

---

### GET `/cortex/acesso-campus/analise/solicitacoes/{pk}/`

- **name:** `analise-solicitacao-detail`

Detalhe completo para decisão (programações editáveis só refletidas enquanto PENDENTE no backend).

---

### POST `/cortex/acesso-campus/analise/solicitacoes/{pk}/aprovar/`

- **name:** `analise-solicitacao-aprovar`

**Body:**

```json
{
  "exige_confirmacao": false,
  "observacao_analise": "Autorizado."
}
```

**Resposta 200:** `status=2` (APROVADA), `eventos` materializados, `exige_confirmacao` congelado por evento.

**Erros:** 400 transição inválida; concorrência perdedora após lock.

---

### POST `/cortex/acesso-campus/analise/solicitacoes/{pk}/rejeitar/`

- **name:** `analise-solicitacao-rejeitar`

**Body:**

```json
{
  "observacao_analise": "Documentação insuficiente."
}
```

**Resposta 200:** `status=3` (REJEITADA).

---

### POST `/cortex/acesso-campus/analise/solicitacoes/{pk}/cancelar/`

- **name:** `analise-solicitacao-cancelar`

**Permissões:** gestão; solicitação deve estar **APROVADA**.

**Body:** `{ "observacao_analise": "..." }` (opcional conforme serializer).

**Efeito:** `CANCELADA`; eventos futuros sem registro → `cancelado_em` preenchido.

---

## Portaria — eventos

### GET `/cortex/acesso-campus/portaria/eventos/`

- **name:** `evento-acesso-list`
- **Permissões:** `operar_portaria` ou L3.

**Filtros:** `status` (múltiplo: `PENDENTE`, `CONCLUIDA`, `EXPIRADA`), `busca`,
`tipo_movimento` (`ENTRADA`, `SAIDA`), `tipo_beneficiario` (`INDIVIDUAL`, `TURMA`),
`data_autorizada`, `hora_inicio`, `hora_fim`, `ordenacao` e `paginacao`.

Filtros inválidos são ignorados. Quando `CONCLUIDA` e `EXPIRADA` são solicitadas juntas sem
ordenação explícita, a API usa data e hora autorizadas decrescentes, independentemente do status.

**Escopo:** somente solicitações aceitas materializadas como evento. **Não** inclui solicitações pendentes.
O GET deriva o status sem persistência; a task Celery grava `expirado_em` a cada minuto.

**Item lista (exemplo):**

```json
{
  "id": "7c067767-8c54-4a82-8b29-78fe444ddcf2",
  "tipo_beneficiario": "INDIVIDUAL",
  "beneficiario": {"id": 15, "tipo": "INDIVIDUAL", "nome": "Maria Silva"},
  "tipo_movimento": "ENTRADA",
  "autorizado_por": {"id": 4, "nome": "Coordenador"},
  "data_autorizada": "2026-10-15",
  "hora_autorizada": "09:30:00",
  "status": "PENDENTE",
  "progresso": {"total": 1, "liberados": 0, "pendentes": 1},
  "acoes": {"pode_registrar": true, "pode_conferir_turma": false}
}
```

---

### GET `/cortex/acesso-campus/portaria/eventos/{grupo_portaria_id}/`

- **name:** `evento-acesso-detail`

Detalhe operacional da autorização agrupada e dados mínimos da solicitação.

### GET `/cortex/acesso-campus/portaria/eventos/{grupo_portaria_id}/alunos/`

- **name:** `evento-acesso-alunos`

Lista os alunos congelados na autorização de turma para conferência parcial.

### GET `/cortex/acesso-campus/portaria/eventos/responsaveis-elegiveis/`

- **name:** `evento-acesso-responsaveis`

Lista o pool de vigilantes físicos da conta guarita. Aceita `busca`, `cpf` e `paginacao`.

---

### POST `/cortex/acesso-campus/portaria/eventos/{grupo_portaria_id}/registrar/`

- **name:** `evento-acesso-registrar`

**Body:**

```json
{
  "responsavel_liberacao_id": 42,
  "aluno_ids": [15, 18],
  "observacao": "Entrada registrada."
}
```

`responsavel_liberacao_id` é obrigatório para conta guarita. `aluno_ids` é obrigatório na
conferência de turma e omitido na autorização individual.

**Resposta 200:** objetos `autorizacao` e `registro`, incluindo quantos alunos foram confirmados
agora e quantos já estavam confirmados. Replay do mesmo registro é idempotente → 200.

**Erros:** 400 autorização expirada ou payload inválido; 403 sem `operar_portaria`; 404 grupo inexistente.

**Nota:** `registrado_por` vem do vigilante efetivo (conta coletiva usa pool — espelho Infraestrutura guarita); nunca persiste `usuario_coletivo` como `registrado_por`.

---

## Histórico

### GET `/cortex/acesso-campus/historico/`

- **name:** `historico-list`
- **Permissões:** `visualizar_historico` **ou** `analisar_solicitacoes` **ou** L3.

**Filtros:** `status`, `aluno_id`, `curso_id`, `data_inicio`, `data_fim`, busca, `paginacao`.

---

### GET `/cortex/acesso-campus/historico/{pk}/`

- **name:** `historico-detail`

Detalhe da **solicitação** com programações, todos os eventos, `confirmacao` e registros (visão auditável).

---

## Códigos HTTP resumidos

| Código | Uso |
|--------|-----|
| 200 | GET, ações idempotentes, cancelamentos |
| 201 | POST criação solicitação |
| 400 | Regra de negócio, validação, transição inválida, registro duplicado com resultado diferente |
| 401 | Não autenticado |
| 403 | Sem capacidade ou escopo |
| 404 | Recurso inexistente ou fora do escopo permitido |

---

## Integração frontend (MeuIF)

Outro repositório consome esta API; compilar capacidades via `GET /cortex/identidade/permissoes/` (chave `acesso_campus` após implementação dos hooks).

---

## Artefatos relacionados

- [Domínio](../domains/acesso-campus.md)
- [Schema](../schema/acesso-campus.md)
- [Milestone](../planning/milestone-acesso-campus.md)
