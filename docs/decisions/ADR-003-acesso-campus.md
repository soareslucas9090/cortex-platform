# ADR-003 — Bounded context AcessoCampus (portaria / autorizações de circulação EM)

- **Status:** Proposto (aceito para implementação futura)
- **Data:** 2026-10-08

> **Escopo desta ADR:** decisão arquitetural e fronteiras do produto. O módulo **AcessoCampus** está **PLANEJADO** — ainda **não** consta em `PROJECT_APPS` nem possui código Django neste repositório.

## Contexto

No fluxo manual atual, alunos de **Ensino Médio (EM)** solicitam à coordenação/direção autorização para entrar fora do horário, sair antes do término, ausentar-se integralmente ou em períodos/recorrências. A portaria consulta listas ou comunicados aprovados e registra o que ocorreu na prática (comparecimento, divergência, impedimento). Esse processo mistura papel acadêmico (elegibilidade por curso e matrícula), decisão gerencial (aprovação única) e operação de guarita (fila do dia e registro físico).

O Cortex já possui domínios consolidados que **não** cobrem esse fluxo de forma coesa:

- **Academico** modela aluno, curso e `AlunoCurso`, mas não autorizações de circulação na portaria.
- **Infraestrutura** trata empréstimo de recursos e `Autorizacao` por sala/recurso — semântica distinta de “sair do campus” ou “entrar tarde”.
- **Transporte** trata ônibus (`EntradaSemTicket` é embarque, não portaria).
- **Identidade / Organizacional** fornecem `Usuario`, `Funcao` e `SetorVinculo`, sem produto de acesso campus.

Há risco de acoplamento acidental se o fluxo for embutido em Academico ou reutilizar tabelas de autorização de Infraestrutura. Menores de idade e responsável legal existem no mundo real, mas **não** entram no MVP documentado aqui (ver exclusões).

Pré-requisito acadêmico explícito: elegibilidade usa `Curso.nivel_ensino` (`IntegerChoices` `NivelEnsino`: `ENSINO_MEDIO=1`, `TECNICO=2`, `SUPERIOR=3`, `POS_GRADUACAO=4`). **É proibido** inferir ensino médio pelo nome do curso.

Timezone operacional: `America/Fortaleza`.

Frontend **MeuIF** (incluindo telas de aluno, gestão e portaria para este produto) reside em **outro repositório**; este repositório entrega **somente a API** REST.

---

## Decisão

Criar um **bounded context próprio**, módulo agregador **`AcessoCampus/`**, prefixo HTTP **`/cortex/acesso-campus/`**, `app_name` do agregador **`acesso_campus`**, chave de permissões no payload **`acesso_campus`**.

Apps internos (cada um com model principal), **sem rotas HTTP** no app `permissoes`:

| App | Model principal |
|-----|-----------------|
| `solicitacoes/` | `SolicitacaoAcesso` |
| `programacoes/` | `ProgramacaoAcesso` |
| `eventos/` | `EventoAcesso` |
| `registros/` | `RegistroAcesso` |
| `permissoes/` | `PermissaoFuncaoAcessoCampus`, `PermissaoUsuarioAcessoCampus` |

**Consumir, não duplicar:** `Aluno`, `AlunoCurso`, `Usuario`, `Funcao`, `SetorVinculo`. **Não** criar entidade `Campus`. **Não** duplicar aluno, matrícula, curso ou perfil de vigilante.

**Autorização = solicitação aprovada.** Não haverá model `Autorizacao` separado; `StatusSolicitacaoAcesso.APROVADA` materializa `EventoAcesso` congelados.

### Programação vs evento

- **`ProgramacaoAcesso`:** intenção editável enquanto a solicitação está `PENDENTE` (`TipoProgramacaoAcesso`: pontual, período, recorrente, saída com retorno, etc.).
- **`EventoAcesso`:** ocorrência operacional **materializada atomicamente na aprovação**, com `exige_confirmacao` **congelado** por evento. Após aprovação, eventos **não** são reescritos silenciosamente; cancelamento futuro marca `cancelado_em` em eventos sem registro.

### Confirmação derivada

`SituacaoConfirmacao` (**PENDENTE**, **NAO_EXIGIDA**, **RECEBIDA**) **não** é persistida. Deriva de `exige_confirmacao` (congelado no evento) e da existência de `RegistroAcesso` (0..1 por evento, `OneToOne`). Objeto **`confirmacao`** sempre presente em respostas de detalhe de solicitação/evento.

### Permissões de módulo

Capacidades booleanas (OR entre função e usuário, padrão Infraestrutura/Transporte):

| Capacidade | Papel típico |
|------------|--------------|
| `solicitar` | Aluno EM elegível — escopo **apenas** próprias solicitações |
| `analisar_solicitacoes` | Coordenação/direção — aprovação **única**, sem cadeia |
| `operar_portaria` | Vigilante/guarita — fila e registro |
| `visualizar_historico` | Consulta ampliada de histórico |

**L3** (`EDITAR_TUDO`) recebe **todas** as capacidades automaticamente na compilação planejada. Vigilante típico: só `operar_portaria`. Gestão apta: `analisar_solicitacoes` (e em geral `visualizar_historico`). Hooks futuros: `UsuarioPermissions.permissoes_acesso_campus()` e `documentacao_acesso_campus()` em `Identidade/usuarios/`; mixins `PodeAnalisarAcessoCampusMixin`, `PodeOperarPortariaAcessoCampusMixin`, `PodeVisualizarHistoricoAcessoCampusMixin` em `AcessoCampus/permissoes/access.py`.

### Materialização (resumo)

Regras completas em `docs/domains/acesso-campus.md` e `docs/schema/acesso-campus.md`. Exemplos: `ENTRADA_TARDIA` → um `EventoAcesso` `ENTRADA`; `SAIDA_COM_RETORNO` → dois eventos no mesmo dia (`SAIDA` + `RETORNO`) ligados por `evento_relacionado` simétrico; `RECORRENTE` exige `data_fim` e `dias_semana` não vazio.

### Portaria e conta coletiva

Espelho Infraestrutura guarita: conta **`usuario_coletivo`** autentica a sessão; **`registrado_por`** em `RegistroAcesso` é sempre **`Usuario` pessoa física** (nunca `usuario_coletivo`).

---

## Alternativas consideradas e rejeitadas

| Alternativa | Motivo da rejeição |
|-------------|-------------------|
| App dentro de **Academico** | Mistura catálogo acadêmico com workflow operacional de portaria; viola coesão e ADR-001 |
| Reutilizar **Infraestrutura.autorizacoes** | Semântica sala/recurso/empréstimo; XOR sala/recurso não mapeia programações/eventos EM |
| Reutilizar **Transporte** / `EntradaSemTicket` | Domínio ônibus; não confundir bloqueio de transporte com circulação campus |
| Pasta **Sigec/** ou **APPs/** genérico | Contrário à ADR-001 e ADR-002 (módulo na raiz com PascalCase) |
| Entidade **Campus** | Implantação por instância; sem multi-campi na mesma base na v1 |
| Conta de **responsável legal** no MVP | Fluxo institucional/LGPD para menores exige validação separada; **fora** do MVP (documentado como exclusão explícita) |
| Model **Autorizacao** separado | Redundante: aprovação **é** a autorização |

---

## Dependências

| Contexto | Uso |
|----------|-----|
| **Academico** | `Aluno`, `AlunoCurso`, `Curso` (+ **`Curso.nivel_ensino`** — entrega AC.1 do milestone) |
| **Identidade** | `Usuario` (analista, cancelador, `registrado_por`) |
| **Organizacional** | `Funcao`, `SetorVinculo` (compilação OR de permissões) |
| **AppCore** | `BasicModel`, BasicViews, exceções, `PaginacaoCustomizada`, envelope de resposta |

**Não** depende de Transporte, Infraestrutura.autorizacoes nem Sigec.

---

## Implicações

### Estrutura e camadas

Por app interno: `models`, `choices`, `rules`, `helpers`, `business` (contrato `try/except` + `relancar_ou_erro_sistema`), `serializers` (**não** `ModelSerializer` de input), `views`, `urls`. **`state.py` não é necessário** — transições via `status` + `rules`, sem FSM estilo Transporte.

### API

Views **Basic\*** do AppCore; `@extend_schema` com bloco **`**Permissões:**`**; paginação `PaginacaoCustomizada`; filtros só **estreitam** após escopo de permissão. Erros: `ValidationException`, `BusinessRuleException`, `AuthorizationException`, `NotFoundException` → 400/401/403/404.

### Concorrência e integridade

Aprovação concorrente: `select_for_update` na `SolicitacaoAcesso`. Sobreposição de janelas data/hora bloqueada entre solicitações `PENDENTE` ou `APROVADA` do mesmo aluno (eventos não cancelados).

### Auditoria

`BasicModel` + `django-simple-history`; campos `*_por` / `*_em` em análise e cancelamento; snapshots textuais (`aluno_nome`, `curso_nome`, `matricula`) preenchidos na **criação** e **não** mutáveis na análise.

### Privacidade

Responsável legal **fora** do fluxo MVP. Go/no-go de produção para menores depende de validação institucional/LGPD documentada em `docs/project/implantacao-acesso-campus.md`.

---

## Artefatos relacionados

- `docs/domains/acesso-campus.md` — especificação funcional canônica
- `docs/schema/acesso-campus.md` — DER e dicionário planejados
- `docs/api/acesso-campus.md` — contrato HTTP planejado
- `docs/planning/milestone-acesso-campus.md` — backlog ordenado (AC.0–AC.12)
- `docs/project/implantacao-acesso-campus.md` — rollout e migrations
- `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- `docs/decisions/ADR-002-permissoes-cortex-niveis.md`
- `docs/diagrams/02-bounded-contexts.md` (seção 5.7 — AcessoCampus planejado)

---

## Resumo

Fica decidido **documentar e, em milestone futura, implementar** o bounded context **AcessoCampus** como módulo agregador dedicado, com solicitação → programação → eventos materializados na aprovação → registro na portaria, elegibilidade EM via `Curso.nivel_ensino`, permissões por capacidade OR função/usuário, e **sem** reutilizar autorizações de Infraestrutura nem Transporte.
