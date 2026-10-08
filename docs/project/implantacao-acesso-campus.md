# Implantação — AcessoCampus

> **Status:** PLANEJADO — procedimento para quando o módulo **AcessoCampus** estiver implementado conforme [milestone](../planning/milestone-acesso-campus.md). **Não** afirmar presença em `PROJECT_APPS` antes do deploy real.

Este documento orienta migrations, cadastro de capacidades, rollout por perfil, validações, observabilidade, contingência e rollback **sem** apagar histórico.

---

## Pré-requisitos de release

1. Etapas **AC.1–AC.11** do milestone concluídas no ambiente alvo.
2. [ADR-003](../decisions/ADR-003-acesso-campus.md) aceita pelo time.
3. **Go/no-go LGPD** para menores: responsável legal **fora** do MVP — validação institucional registrada antes de abrir alunos EM em produção.
4. Frontend MeuIF (repositório separado) alinhado ao contrato [api/acesso-campus.md](../api/acesso-campus.md).

---

## Ordem de migrations

### 1. Academico (obrigatório primeiro)

- Migration adicionando **`Curso.nivel_ensino`** (`NivelEnsino`: `ENSINO_MEDIO=1`, `TECNICO=2`, `SUPERIOR=3`, `POS_GRADUACAO=4`).
- Garantir seeds/cursos existentes recebem valor coerente (migration de dados ou default temporário documentado).
- **Não** inferir ensino médio pelo nome do curso na carga.

### 2. AcessoCampus (ordem entre apps)

Aplicar na sequência (dependências FK):

1. `AcessoCampus.solicitacoes` — `SolicitacaoAcesso`
2. `AcessoCampus.programacoes` — `ProgramacaoAcesso`
3. `AcessoCampus.eventos` — `EventoAcesso`
4. `AcessoCampus.registros` — `RegistroAcesso`
5. `AcessoCampus.permissoes` — `PermissaoFuncaoAcessoCampus`, `PermissaoUsuarioAcessoCampus`

Registrar apps em `PROJECT_APPS` e include URL **`/cortex/acesso-campus/`** (`app_name` **`acesso_campus`**) na mesma janela de deploy que as migrations finais do módulo.

---

## Cadastro inicial de capacidades

Compilação na chave payload **`acesso_campus`** via `permissoes_acesso_campus()` (OR função + usuário). Capacidades:

| Flag | Uso |
|------|-----|
| `solicitar` | Aluno EM elegível |
| `analisar_solicitacoes` | Coordenação/direção EM |
| `operar_portaria` | Vigilante/guarita |
| `visualizar_historico` | Consulta ampliada |

### Sugestão institucional (v1)

| Origem | Configuração |
|--------|--------------|
| `PermissaoFuncaoAcessoCampus` em **COORDENADOR** / **DIRETOR** (funções EM) | `analisar_solicitacoes=true`, `visualizar_historico=true` |
| Perfil vigilante / função guarita | `operar_portaria=true` |
| `PermissaoUsuarioAcessoCampus` | Exceções pontuais (OR com função) |
| **L3** (`EDITAR_TUDO`) | **Todas** as capacidades automaticamente |

Aluno: **`solicitar`** derivado de elegibilidade (aluno ativo, `MATRICULADO`, `AlunoCurso.ativo`, `nivel_ensino=ENSINO_MEDIO`) — implementação na compilação conforme [domains/acesso-campus.md](../domains/acesso-campus.md).

Atualizar **`documentacao_acesso_campus()`** no mesmo commit que alterar regras (ADR-002).

Mixins de view: `PodeAnalisarAcessoCampusMixin`, `PodeOperarPortariaAcessoCampusMixin`, `PodeVisualizarHistoricoAcessoCampusMixin` em `AcessoCampus/permissoes/access.py`.

---

## Rollout por perfil

Ordem recomendada (feature flag ou menu MeuIF):

1. **Gestão** — analisar fila `PENDENTE` em homologação; validar materialização e timezone **America/Fortaleza**.
2. **Portaria** — fila `portaria/eventos/?data=`; testar conta **`usuario_coletivo`** + pool (espelho Infraestrutura guarita); `registrado_por` sempre pessoa física.
3. **Aluno EM (MeuIF)** — criar/cancelar solicitações; confirmar bloqueio para superior/técnico/pós.

Não misturar bloqueio de **Transporte** com este módulo na comunicação operacional.

---

## Validações pré-deploy

| Check | Como |
|-------|------|
| Migrations Academico + AcessoCampus | `migrate` em staging |
| Cursos EM com `nivel_ensino=1` | Query admin ou script |
| Permissões compiladas | `GET /cortex/identidade/permissoes/` amostra por persona |
| Swagger | Bloco `**Permissões:**` em todas as views |
| Testes AC.10 | CI verde |
| LGPD menores | Parecer institucional arquivado |

---

## Validações pós-deploy

| Check | Como |
|-------|------|
| Smoke aluno EM | POST `solicitacoes/` → PENDENTE |
| Smoke gestão | Aprovar → eventos materializados |
| Smoke portaria | GET fila hoje; POST registrar |
| Histórico | GET `historico/{pk}` com `confirmacao` |
| Idempotência registro | Replay 200 |
| Sobreposição | Segunda solicitação conflitante 400 |

---

## Observabilidade

- Logs estruturados em `business` via `relancar_ou_erro_sistema` (sem vazar `str(e)` ao cliente).
- Métricas sugeridas (futuro): contagem aprovações/dia, registros por `ResultadoRegistroAcesso`, latência fila portaria.
- Auditar via `django-simple-history` + campos `analisada_por`, `cancelada_por`, `registrado_por`.

---

## Contingência

Se a API **AcessoCampus** estiver indisponível:

- Manter **fluxo manual** institucional (papel/lista) até restauração.
- Portaria **não** deve depender de cache stale de eventos sem data explícita.
- Celery **não** é requisito do MVP documentado; fila é consulta síncrona por `data`.

---

## Rollback (produção)

**Objetivo:** desativar operação **sem** apagar histórico.

| Ação permitida | Ação proibida |
|----------------|---------------|
| Remover include de URLs ou feature flag MeuIF | `DROP TABLE` de solicitações/eventos/registros |
| Zerar flags em `PermissaoFuncaoAcessoCampus` / `PermissaoUsuarioAcessoCampus` | Deletar rows de auditoria |
| Reverter deploy de código (views) mantendo DB | Migration reversa destrutiva em produção |

Dados históricos permanecem para eventual reativação e obrigações LGPD/auditória.

---

## LGPD go/no-go

| Item | MVP |
|------|-----|
| Responsável legal no fluxo | **Excluído** — documentar exclusão explícita |
| Menores EM | Exige validação jurídica/pedagógica **antes** go-live amplo |
| Base legal / DPIA | Responsabilidade institucional; registrar decisão |
| Retenção | Alinhar política de histórico (`historico-*`) com DPO |

**No-go:** abrir produção para todos os EM sem parecer sobre menores e sem capacitação de gestão/portaria.

---

## Referências

- [Milestone AcessoCampus](../planning/milestone-acesso-campus.md)
- [Schema](../schema/acesso-campus.md)
- [Domínio](../domains/acesso-campus.md)
- [Infraestrutura — usuario_coletivo](../schema/infraestrutura.md) (padrão guarita)
