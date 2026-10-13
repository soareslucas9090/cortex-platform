# API — AcessoCampus (contrato planejado)

> **Status:** PLANEJADO — endpoints **não** existem no código. Prefixo base: **`/cortex/acesso-campus/`**. Namespace URL: **`acesso_campus`**. Envelope e paginação: padrão **AppCore** (`PaginacaoCustomizada`).

Autenticação: JWT/sessão padrão Cortex (401 se ausente). Permissões de módulo na chave **`acesso_campus`** do payload compilado. **L3** acessa todos os recursos.

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
| `portaria/eventos/` | GET | `portaria-evento-list` | `operar_portaria` ou L3 |
| `portaria/eventos/{pk}/` | GET | `portaria-evento-detail` | `operar_portaria` ou L3 |
| `portaria/eventos/{pk}/registrar/` | POST | `portaria-evento-registrar` | `operar_portaria` ou L3 |
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

- **name:** `portaria-evento-list`
- **Permissões:** `operar_portaria` ou L3.

**Filtros:** `data` (default **hoje** America/Fortaleza), busca, `tipo` (`TipoEventoAcesso`), `situacao_confirmacao`, `paginacao`.

**Escopo:** solicitação `APROVADA`, `cancelado_em` null, data no recorte. **Não** inclui fila de solicitações PENDENTES.

**Item lista (exemplo):**

```json
{
  "id": 501,
  "tipo": 1,
  "tipo_display": "Entrada",
  "data_hora_prevista": "2026-10-15T09:30:00-03:00",
  "aluno_nome": "Maria Silva",
  "matricula": "2026001",
  "confirmacao": {
    "situacao_confirmacao": "PENDENTE",
    "situacao_confirmacao_display": "Pendente",
    "exige_confirmacao": true,
    "registro": null
  }
}
```

---

### GET `/cortex/acesso-campus/portaria/eventos/{pk}/`

- **name:** `portaria-evento-detail`

Detalhe operacional + `confirmacao` + dados mínimos da solicitação.

---

### POST `/cortex/acesso-campus/portaria/eventos/{pk}/registrar/`

- **name:** `portaria-evento-registrar`

**Body:**

```json
{
  "resultado": 1,
  "observacao": "Entrada registrada."
}
```

`resultado`: 1=REALIZADO, 2=DIVERGENCIA, 3=NAO_COMPARECEU, 4=IMPEDIDO.

**Resposta 200:** evento com `confirmacao.situacao_confirmacao=RECEBIDA` e `registro` preenchido. Replay idempotente mesmo `resultado` → 200.

**Erros:** 400 evento inelegível, resultado inválido, ou **alteração** de resultado já gravado; 403 gestão sem `operar_portaria`.

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
