# Documentação Estrutural do Cortex

## Objetivo desta pasta

A pasta `docs/diagrams/` concentra os artefatos de documentação estrutural e conceitual do Cortex.

Ela existe para registrar, de forma progressiva, as decisões de modelagem, divisão de domínio, visão do sistema e regras centrais que orientam a implementação do backend.

Esses documentos não substituem o código, mas servem como apoio para:

- entender o sistema antes da implementação;
- alinhar decisões arquiteturais;
- reduzir retrabalho;
- manter consistência entre domínio, models e regras de negócio;
- facilitar evolução futura do projeto.

---

## Estrutura atual da documentação

### `00-readme.md`

Documento índice desta pasta, com visão geral dos artefatos.

### `01-product-and-system-overview.md`

Visão geral do produto e da estrutura inicial do sistema.

### `02-bounded-contexts.md`

Define os domínios iniciais do Cortex, seus limites e responsabilidades.

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

---

## Relação com outros artefatos do projeto

Além desta pasta, a documentação do projeto também se apoia em:

### `docs/decisions/`

Guarda ADRs e decisões arquiteturais formais.

Artefato atual:

- `ADR-001-modularizacao-por-dominio.md`

### `docs/project/`

Guarda artefatos mais operacionais, como:

- árvore inicial do projeto;
- checklist de implementação;
- cenários de seed;
- guias de execução.

---

## Princípios que orientam esta documentação

1. **Documentar o suficiente para orientar a implementação**
   - sem transformar a documentação em peso desnecessário.

2. **Refletir o domínio real**
   - a documentação deve espelhar a linguagem do negócio.

3. **Servir como apoio à arquitetura em camadas**
   - especialmente para separar responsabilidades entre `models`, `business`, `rules`, `helpers`, `serializers` e `views`.

4. **Acompanhar mudanças importantes do sistema**
   - sempre que houver alteração relevante de domínio, modelagem ou convenção, os documentos devem ser revisados.

5. **Evitar ambiguidade**
   - cada artefato deve ter um propósito claro.

---

## Convenções gerais adotadas

### Organização por domínio

O Cortex será organizado por domínio, e não por agrupamentos puramente técnicos.

### Convenção de nomes

- **Domínio**: inicial maiúscula
- **App Django**: minúsculo

Exemplos:

- Domínio: `Organizacional`
- app Django: `organizacional`

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

---

## Estado atual da documentação

Neste estágio, a documentação já consolidou:

- a decisão de modularização por domínio;
- a árvore inicial do projeto;
- o ERD textual central;
- os agregados e invariantes principais;
- o checklist inicial de implementação;
- os cenários mínimos de seed e usuários de teste.

---

## Próximo passo previsto

O próximo passo planejado após estes artefatos é realizar uma **revisão geral do `AppCore`**, utilizando como base o repositório atual do projeto.

Essa revisão deverá verificar:

- aderência da base técnica ao domínio do Cortex;
- compatibilidade da arquitetura atual com os apps de domínio definidos;
- pontos de melhoria em autenticação, models base, mixins, permissões, views base e convenções;
- necessidade de ajustes antes do início efetivo da implementação dos domínios.

---

## Quando atualizar esta pasta

Atualize os documentos de `docs/diagrams/` sempre que houver:

- mudança relevante de domínio;
- mudança de nome de entidades importantes;
- alteração de relação estrutural do ERD;
- revisão de agregados ou invariantes;
- nova convenção arquitetural relevante.

---

## Resumo

A pasta `docs/diagrams/` é o núcleo da documentação conceitual do Cortex.

Ela deve continuar pequena, útil e diretamente conectada às decisões reais do projeto, servindo como ponte entre:

- entendimento de negócio;
- arquitetura;
- e implementação prática.
