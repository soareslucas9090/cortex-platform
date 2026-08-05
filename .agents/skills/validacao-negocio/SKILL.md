---
name: validacao-negocio
description: Valida regras de negócio e procura brechas (lacunas, inconsistências, casos extremos). Use quando o usuário pedir validar regras, achar buracos no negócio, revisar requisitos, ou /validacao-negocio.
disable-model-invocation: true
---

# Validação de Negócio — Novo Cortex

## Objetivo

Ajudar alunos a **entender, validar e encontrar brechas** em regras de negócio — antes ou depois da implementação. Cruza o que o usuário descreve com código existente e documentação de domínio.

## Fontes de referência

- `docs/domains/<dominio>.md` — vocabulário, invariantes, fluxos do domínio
- `docs/diagrams/04-aggregates-and-invariants.md` — invariantes do sistema
- Código: `rules.py`, `business.py`, `models.py`, `state.py` (quando existir)
- `docs/project/regras-do-projeto.md` — separação Rules vs Business

---

## Princípio central

**Conversar até entender.** Não saltar para conclusões nem assumir regras não ditas pelo usuário.

---

## Fase 1: Entender o negócio (conversa)

Extrair do usuário (perguntar o que faltar):

| Elemento | Pergunta guia |
|----------|---------------|
| **Atores** | Quem executa a ação? (aluno, servidor, gestor, sistema) |
| **Pré-condições** | O que precisa ser verdade antes? |
| **Ação** | O que acontece no fluxo feliz? |
| **Pós-condições** | O que muda no sistema depois? |
| **Invariantes** | O que **nunca** pode acontecer? |
| **Exceções** | Quais casos especiais são permitidos? |
| **Permissões** | Quem pode / quem não pode? (L1/L2/L3) |
| **Estados** | Quais estados existem? Quais transições são válidas? |
| **Fluxos infelizes** | O que acontece em erro, duplicidade, concorrência? |

Usar perguntas com opções A/B/C + **"Outro (descreva):"**. Máximo 3–5 por rodada.

Mais perguntas modelo: [perguntas.md](perguntas.md).

---

## Fase 2: Cruzar com implementação (se existir)

1. Identificar domínio e app(s) relacionados.
2. Ler `docs/domains/<dominio>.md`.
3. Ler `rules.py`, `business.py`, models e testes da feature.
4. Mapear: cada regra entendida → onde está (ou deveria estar) no código.

Se **não há código ainda**, validar só o modelo mental e apontar o que precisará ser implementado nas Rules e no Business.

---

## Fase 3: Procurar brechas

Verificar sistematicamente:

- **Lacunas:** cenário não coberto por regra nem código
- **Contradições:** regra A conflita com regra B ou com o código
- **Ambiguidade:** mais de uma interpretação possível
- **Permissões:** ação possível sem checagem de nível Cortex
- **Estados inválidos:** transição permitida que viola invariante
- **Edge cases:** listas vazias, duplicatas, registros inativos, datas limites, exclusão lógica vs física
- **Concorrência de negócio:** duas ações simultâneas geram estado inconsistente?
- **Exposição indevida:** dado sensível vazando em resposta da API

---

## Formato de saída (por regra)

```markdown
### Regra: [nome curto em linguagem de negócio]

| Campo | Valor |
|-------|-------|
| **Entendimento** | [como a regra foi interpretada] |
| **Status** | Satisfeita / Parcial / Violada / Não implementada / Ambígua |
| **Evidência** | [arquivo:linha ou "ausente no código"] |
| **Risco** | Baixo / Médio / Alto — [por quê] |
| **Pergunta ou recomendação** | [o que decidir ou implementar] |
```

### Status — definições

| Status | Significado |
|--------|-------------|
| **Satisfeita** | Regra clara e código/docs cobrem o cenário |
| **Parcial** | Cobre parte dos casos; faltam edge cases |
| **Violada** | Código permite o que a regra proíbe |
| **Não implementada** | Regra descrita mas sem código correspondente |
| **Ambígua** | Regra mal definida; precisa decisão do usuário |

---

## Template de relatório final

```markdown
# Validação de negócio: [feature ou fluxo]

## Resumo executivo
[2–3 frases para aluno leigo]

## Contexto entendido
- **Atores:** ...
- **Fluxo feliz:** ...
- **Invariantes:** ...

## Análise por regra
[usar formato por regra acima]

## Brechas encontradas (priorizadas)
1. **[Alta]** ...
2. **[Média]** ...

## Perguntas em aberto
[agrupadas, com opções A/B/C + Outro]

## Recomendações
- [o que implementar em Rules]
- [o que orquestrar em Business]
- [o que documentar em docs/domains/]
```

---

## Tom para alunos leigos

- Traduza "invariante" → "regra que nunca pode ser quebrada".
- Traduza "pré-condição" → "o que precisa estar certo antes".
- Use exemplos concretos do domínio (matrícula, vínculo, setor) em vez de abstrações.
- Quando achar brecha, explique **o que poderia dar errado na prática** (não só "falta validação").

---

## Diferença das outras skills

| Skill | Foco |
|-------|------|
| **implementacao** | Como codar seguindo padrões técnicos |
| **revisao-codigo** | Conformidade arquitetural do código |
| **validacao-negocio** | Correção e completude das **regras de negócio** |

Uma feature pode passar na revisão de código e ainda ter buracos de negócio — e vice-versa.

---

## O que NÃO fazer

- Não assumir regras não confirmadas pelo usuário.
- Não pular a fase de entendimento mesmo que o usuário tenha pressa.
- Não confundir validação de formato (serializer) com regra de negócio (rules).
- Não reescrever código inteiro — indicar **onde** e **o que** falta.
