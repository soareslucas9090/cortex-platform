# Documentação Estrutural do Cortex

## Objetivo desta pasta

A pasta `docs/diagrams/` concentra os artefatos de documentação estrutural e conceitual do Cortex.

Ela registra decisões de modelagem, divisão de domínio, visão do sistema e regras centrais que descrevem o **backend implementado** e orientam evolução e programação agentic.

Esses documentos não substituem o código, mas servem como apoio para:

- entender o sistema em produção de desenvolvimento;
- alinhar decisões arquiteturais;
- reduzir retrabalho;
- manter consistência entre domínio, models e regras de negócio;
- facilitar evolução futura do projeto.

---

## Estrutura atual da documentação

### `00-readme.md`

Documento índice desta pasta, com visão geral dos artefatos.

### `01-product-and-system-overview.md`

Visão geral do produto e da estrutura do sistema (seis domínios de negócio, base técnica, rotas).

### `02-bounded-contexts.md`

Mapa canônico dos bounded contexts: apps, entidades, responsabilidades, dependências e exceções de roteamento.

### `03-core-erd.md`

Tradução textual e arquitetural do DER principal do sistema.

### `04-aggregates-and-invariants.md`

Define agregados e invariantes de domínio que orientam business e rules.

---

## Como ler estes documentos

A ordem recomendada de leitura é:

1. `00-readme.md`
2. `01-product-and-system-overview.md`
3. `02-bounded-contexts.md`
4. `03-core-erd.md`
5. `04-aggregates-and-invariants.md`

Essa sequência vai do mais geral para o mais específico.

Para regras operacionais por módulo, use `docs/domains/` (Identidade, Organizacional, Pessoas Institucionais, Acadêmico, Infraestrutura, Transporte). O schema de produto de Infraestrutura permanece em `docs/schema/infraestrutura.md`.

---

## Relação com outros artefatos do projeto

Além desta pasta, a documentação do projeto também se apoia em:

### `docs/decisions/`

Guarda ADRs e decisões arquiteturais formais.

Artefatos centrais:

- [ADR-001: Modularização por domínio](../decisions/ADR-001-modularizacao-por-dominio.md)
- [ADR-002: Permissões Cortex por nível (L1–L3)](../decisions/ADR-002-permissoes-cortex-niveis.md)

### `docs/project/`

Guarda artefatos operacionais, como:

- árvore do projeto;
- checklist de implementação;
- cenários de seed;
- guias de execução;
- [resumo da revisão do AppCore](../project/appcore-review-summary.md) (histórico da adequação da base técnica).

### `docs/planning/`

Marcos de implementação concluídos e follow-ups operacionais (`followup-*`).

---

## Princípios que orientam esta documentação

1. **Refletir o domínio e o código implementados**
   - diagramas e textos descrevem o estado atual; divergências devem ser corrigidas na documentação ou no código de forma explícita.

2. **Espelhar a linguagem do negócio**
   - seis módulos de domínio na raiz do repositório, roteados em `Cortex/urls.py`.

3. **Servir como apoio à arquitetura em camadas**
   - separação entre `models`, `business`, `rules`, `helpers`, `serializers` e `views`.

4. **Permanecer íntegra e alinhada ao código**
   - conjunto completo o suficiente para agentes e desenvolvedores navegarem o sistema sem adivinhar estrutura.

5. **Evitar ambiguidade**
   - cada artefato deve ter um propósito claro.

---

## Convenções gerais adotadas

### Organização por domínio

O Cortex é organizado por domínio, e não por agrupamentos puramente técnicos.

Domínios implementados:

1. `Identidade`
2. `Organizacional`
3. `PessoasInstitucionais`
4. `Academico`
5. `Infraestrutura`
6. `Transporte`

### Convenção de nomes

- **Domínio**: inicial maiúscula (módulo agregador PascalCase)
- **App Django**: minúsculo, dentro do módulo

Exemplos:

- Domínio: `Organizacional`
- app Django: `Organizacional/setores/`

### Arquitetura em camadas

Cada app de domínio tende a seguir a estrutura:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

### Views leves

As views devem permanecer leves e delegar a lógica para a camada de business.

### Rotas HTTP

Prefixo por domínio: `/cortex/<dominio>/` (com hífen em `pessoas-institucionais`). Autenticação em `/cortex/auth/`.

---

## Estado atual da documentação

Esta pasta descreve o sistema **já implementado**:

- seis bounded contexts com apps listados em `Cortex/settings.py` (`PROJECT_APPS`);
- `AppCore`, `Auth` e `Cortex` como base técnica em uso (`AUTH_USER_MODEL = usuarios.Usuario`);
- ERD textual, agregados e invariantes como referência complementar;
- decisões formalizadas em ADR-001 e ADR-002.

A revisão histórica da base `AppCore` está registrada em `docs/project/appcore-review-summary.md`; não é um passo pendente de implementação dos domínios.

---

## Manutenção contínua

O trabalho corrente é **manter documentação e código alinhados**. Follow-ups operacionais vivem em `docs/planning/followup-*`.

Atualize os documentos de `docs/diagrams/` sempre que houver:

- mudança relevante de domínio;
- mudança de nome de entidade importante;
- alteração de relação estrutural do ERD;
- revisão de agregados ou invariantes;
- nova convenção arquitetural relevante;
- inclusão ou remoção de app em `PROJECT_APPS` ou rota em `Cortex/urls.py`.

---

## Resumo

A pasta `docs/diagrams/` é o núcleo da documentação conceitual do Cortex.

Ela conecta entendimento de negócio, arquitetura e implementação prática do backend modular, com mapa detalhado em `02-bounded-contexts.md` e detalhamento operacional em `docs/domains/` e schemas correlatos.
