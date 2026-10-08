# Milestone — AcessoCampus (backlog ordenado)

> **Status:** PLANEJADO — **não** marcar etapas como histórico concluído até a implementação existir no código. O módulo **AcessoCampus** ainda **não** está em `PROJECT_APPS`.

Fontes canônicas para execução:

- [docs/domains/acesso-campus.md](../domains/acesso-campus.md)
- [docs/schema/acesso-campus.md](../schema/acesso-campus.md)
- [docs/api/acesso-campus.md](../api/acesso-campus.md)
- [docs/decisions/ADR-003-acesso-campus.md](../decisions/ADR-003-acesso-campus.md)
- [docs/project/regras-do-projeto.md](../project/regras-do-projeto.md), [guia-implementacao.md](../project/guia-implementacao.md)

---

## Objetivo

Entregar o bounded context **AcessoCampus/** com API REST em **`/cortex/acesso-campus/`**, fluxo solicitação → análise → eventos → portaria → histórico, elegibilidade EM via **`Curso.nivel_ensino`**, permissões **`acesso_campus`**, testes `APITestCase` e Swagger alinhado.

---

## Definição de pronto (DoD)

1. Apps registrados, migrations aplicáveis, `python manage.py check` OK.
2. Regras de elegibilidade, sobreposição, materialização e registro cobertas por testes listados abaixo.
3. Todas as views com `**Permissões:**` no `@extend_schema`.
4. Hooks `permissoes_acesso_campus()` e `documentacao_acesso_campus()` em Identidade.
5. **`schema.yaml` atualizado somente na etapa AC.12** (após API estável).
6. Documentação de domínio/schema/api consistente com o código entregue.

---

## Ordem de execução (AC.0 … AC.12)

### AC.0 — Documentação (esta milestone)

| | |
|--|--|
| **Pré-requisito** | ADR-001, ADR-002 lidos |
| **Entregáveis** | ADR-003, domains, schema, api, milestone, implantacao |
| **Critério de saída** | Time implementa sem reabrir vocabulário canônico |
| **Padrões** | PT-BR; marcar PLANEJADO |
| **Testes** | N/A |

---

### AC.1 — `Curso.nivel_ensino` (Academico)

| | |
|--|--|
| **Pré-requisito** | AC.0 |
| **Entregáveis** | Campo `nivel_ensino` (`NivelEnsino` int choices); migration; `rules` de validação; seeds existentes não quebram (default documentado ou data migration) |
| **Critério de saída** | API/admin curso expõe nível; testes Academico verdes |
| **Padrões** | IntegerChoices; não inferir EM por nome |
| **Testes** | Criação/edição curso com nível; seed smoke |

---

### AC.2 — Esqueleto AcessoCampus

| | |
|--|--|
| **Pré-requisito** | AC.1 |
| **Entregáveis** | Pasta `AcessoCampus/`, `urls.py` (`app_name = 'acesso_campus'`), include `Cortex/urls.py` → `path('cortex/acesso-campus/', ...)`; registro futuro em `PROJECT_APPS` (apps vazios ou stubs) |
| **Critério de saída** | Boot Django OK; rota responde 404 controlado até AC.6+ |
| **Padrões** | Espelhar `Infraestrutura/urls.py` |
| **Testes** | `manage.py check` |

---

### AC.3 — Models, choices, migrations

| | |
|--|--|
| **Pré-requisito** | AC.2 |
| **Entregáveis** | Apps `solicitacoes`, `programacoes`, `eventos`, `registros`, `permissoes` na ordem de dependência; models conforme [schema](../schema/acesso-campus.md); migrations |
| **Ordem migrations apps** | solicitacoes → programacoes → eventos → registros → permissoes |
| **Critério de saída** | `migrate` limpo em DB de dev |
| **Padrões** | BasicModel; PROTECT/CASCADE conforme schema |
| **Testes** | Factory mínima ou testes de model constraints |

---

### AC.4 — Rules, helpers, business

| | |
|--|--|
| **Pré-requisito** | AC.3 |
| **Entregáveis** | Camadas por app; materialização na aprovação; sobreposição; elegibilidade EM; cancelamento; registro idempotente; **try/except** integral em business |
| **Critério de saída** | Testes unitários de rules/business críticos verdes |
| **Padrões** | [regras-do-projeto.md](../project/regras-do-projeto.md) |
| **Testes** | Materialização por tipo; sobreposição; select_for_update (integração) |

---

### AC.5 — Permissões e hooks Identidade

| | |
|--|--|
| **Pré-requisito** | AC.3 (Funcao existe) |
| **Entregáveis** | `PermissaoFuncaoAcessoCampus`, `PermissaoUsuarioAcessoCampus`; `permissoes_acesso_campus()`; `documentacao_acesso_campus()`; mixins em `AcessoCampus/permissoes/access.py`; **sem urls** no app permissoes |
| **Critério de saída** | Payload `acesso_campus` correto; L3 todas flags |
| **Testes** | Compilação OR função/usuário |

---

### AC.6 — API aluno

| | |
|--|--|
| **Pré-requisito** | AC.4, AC.5 |
| **Entregáveis** | Views `solicitacao-list`, `detail`, `cancelar`; serializers input não-ModelSerializer; filtros `status`, `paginacao` |
| **Critério de saída** | Aluno EM cria/lista/cancela; superior 400 |
| **Testes** | APITestCase escopo próprio |

---

### AC.7 — API análise

| | |
|--|--|
| **Pré-requisito** | AC.6 |
| **Entregáveis** | `analise-solicitacao-*`, aprovar/rejeitar/cancelar aprovada |
| **Critério de saída** | Transições atômicas + eventos |
| **Testes** | Aprovar/rejeitar/cancelar; concorrência aprovação |

---

### AC.8 — API portaria + confirmação

| | |
|--|--|
| **Pré-requisito** | AC.7 |
| **Entregáveis** | `portaria-evento-*`, `registrar`; objeto `confirmacao`; filtros portaria |
| **Critério de saída** | Fila não mostra PENDENTE; quatro resultados; idempotência |
| **Testes** | confirmacao opcional vs obrigatória; conta coletiva não é registrado_por |

---

### AC.9 — API histórico

| | |
|--|--|
| **Pré-requisito** | AC.8 |
| **Entregáveis** | `historico-list`, `historico-detail` |
| **Critério de saída** | Gestão/histórico/L3 acessam conforme matriz |
| **Testes** | Vigilante sem historico 403; gestão com analisar ok |

---

### AC.10 — Testes APITestCase (pacote obrigatório)

Executar e manter verdes:

| Caso | Cobertura |
|------|-----------|
| Pontual entrada tardia | Materialização 1 ENTRADA |
| Pontual saída antecipada | 1 SAIDA |
| Período | N AUSENCIA dias civis |
| Recorrência | datas + dias_semana + data_fim |
| Saída com retorno | 2 eventos + relacionado |
| Ausência integral | 1 AUSENCIA |
| Aprovar / rejeitar / cancelar | Estados + cancelamento aprovada |
| confirmacao | exige true/false vs registro |
| Portaria | 4 resultados ResultadoRegistroAcesso |
| Aluno superior | não solicita (400) |
| L1 sem capacidade | 403 |
| Vigilante | não analisa (403 analise) |
| Gestão | não opera portaria sem operar_portaria |
| Conta coletiva | registrado_por pessoa física |
| Sobreposição | 400 |
| Concorrência aprovação | uma vitória, outra 400 |

---

### AC.11 — Swagger

| | |
|--|--|
| **Pré-requisito** | AC.6–AC.9 |
| **Entregáveis** | `@extend_schema` + `**Permissões:**` em todas as views AcessoCampus |
| **Critério de saída** | Revisão manual / drf-spectacular sem warnings críticos |

---

### AC.12 — schema.yaml

| | |
|--|--|
| **Pré-requisito** | AC.11, API estável |
| **Entregáveis** | Atualizar `schema.yaml` **somente após** endpoints existirem |
| **Critério de saída** | OpenAPI reflete paths `/cortex/acesso-campus/` |

---

## Cadastro inicial sugerido (pós AC.5)

| Perfil | Capacidades |
|--------|-------------|
| Função COORDENADOR / DIRETOR (EM) | `analisar_solicitacoes`, `visualizar_historico` |
| Vigilante / guarita | `operar_portaria` |
| L3 | todas (automático) |
| Aluno EM elegível | `solicitar` via regra de perfil + vínculo (compilação) |

Detalhes operacionais: [implantacao-acesso-campus.md](../project/implantacao-acesso-campus.md).

---

## O que não fazer nesta milestone

- Editar `schema.yaml` antes de AC.12.
- Implementar responsável legal.
- Acoplar Transporte ou Infraestrutura.autorizacoes.
- Marcar AC.1+ como concluído sem código merged.

---

## Artefatos relacionados

- [Implantação](../project/implantacao-acesso-campus.md)
- [ADR-003](../decisions/ADR-003-acesso-campus.md)
