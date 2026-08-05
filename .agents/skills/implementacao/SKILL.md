---
name: implementacao
description: Guia alunos e agentes a implementar código no Cortex/DRF seguindo TODOS os padrões do projeto. Use quando o usuário pedir para implementar, criar endpoint, feature, model, business, rules, ou quando mencionar /implementacao. Suporta modo Plano e modo Agente.
disable-model-invocation: true
---

# Implementação — Novo Cortex

## Objetivo

Orquestrar a implementação de código no projeto **sem reinventar os guias**. Esta skill define **como trabalhar** (fluxo, perguntas, plano); os detalhes técnicos estão em `docs/`.

## Fontes obrigatórias (ler antes de implementar)

1. `docs/README.md` — mapa da documentação
2. `docs/project/regras-do-projeto.md` — arquitetura em camadas, views leves, proibições
3. `docs/project/guia-implementacao.md` — checklist de conformidade, AppCore, exemplos
4. `docs/domains/<dominio>.md` — regras do domínio afetado (identidade, organizacional, pessoas-institucionais, academico)

> **Regra de ouro:** se esta skill e `docs/` divergirem, **`docs/` vence**.

## Princípios para alunos leigos

- Use linguagem clara. Se usar termo técnico (ex.: serializer, endpoint), explique em uma frase.
- Explique brevemente o **porquê** de cada decisão arquitetural.
- **Não invente** requisitos críticos (permissões, regras de negócio, campos obrigatórios). Pergunte.
- Aceite prompts vagos; transforme em plano estruturado antes de codar.

---

## Fluxo obrigatório: Plano → Agente

### Modo PLANO (sempre primeiro)

Use quando: usuário pede planejar, está em Plan Mode, ou ainda não há plano aprovado.

1. Ler as fontes obrigatórias e explorar o código do app/domínio afetado.
2. Esclarecer dúvidas bloqueantes (ver seção Perguntas).
3. Produzir plano estruturado (template abaixo).
4. Pedir **aprovação explícita** do usuário antes de implementar.

### Modo AGENTE (só após plano aprovado)

Use quando: plano foi aprovado e o usuário pede implementar.

1. Implementar **somente** o que o plano aprovado descreve.
2. Se o pedido divergir do plano → parar, esclarecer, atualizar plano.
3. Seguir ordem de camadas (abaixo) e checklist do guia.

### Entrada direta no modo Agente

Se o usuário pedir implementação sem plano:

1. **Não pular o plano por padrão.**
2. Oferecer: "Posso montar o plano primeiro (recomendado) ou você confirma que quer implementar direto?"
3. Só implementar sem plano com confirmação explícita do usuário (ex.: "pode implementar direto, sem plano").

---

## Ordem de implementação

Sempre nesta sequência; cada camada depende da anterior:

```
Models → Rules → Helpers → Business → Serializers → Views → URLs → Testes
```

Resumo do que vai em cada camada (detalhes em `docs/project/guia-implementacao.md`):

| Camada | Responsabilidade |
|--------|------------------|
| **Models** | Estrutura de dados; herdar `BasicModel` / mixins do AppCore |
| **Rules** | Validações de negócio (`pode_*`, `validar_*`); português; sem persistência |
| **Helpers** | Queries e utilitários reutilizáveis |
| **Business** | Orquestração; `try/except` + `relancar_ou_erro_sistema` em todo método |
| **Serializers** | Entrada/saída da API |
| **Views** | Leves; herdar `Basic*APIView`; delegar ao Business via hooks `do_action_*` |
| **URLs** | `path()` com `name=`; `roteador_por_metodo` para múltiplos verbos |
| **Testes** | Essenciais ao criar/alterar views; atualizar se comportamento mudar |

---

## Perguntas ao usuário

### Quando perguntar

- Falta domínio, ator, permissão, campo obrigatório ou regra de negócio.
- Há ambiguidade que muda arquitetura (novo app vs. estender existente).
- O prompt é vago demais para implementar com segurança.

### Regras

- Máximo **3–5 perguntas por rodada**; priorize o que **bloqueia** o plano.
- Sempre ofereça opções **A/B/C/...** + **"Outro (descreva):"** no final.
- Agrupe perguntas relacionadas; não bombardear com 20 perguntas.

### Template de pergunta

```markdown
Para montar o plano com segurança, preciso esclarecer:

**1. [Tema da pergunta]**
- A) [opção clara]
- B) [opção clara]
- C) [opção clara]
- Outro (descreva):

**2. [Tema da pergunta]**
- A) ...
- B) ...
- Outro (descreva):
```

Mais exemplos em [perguntas.md](perguntas.md).

---

## Template de plano

Preencher e apresentar ao usuário para aprovação:

```markdown
# Plano de implementação: [título curto]

## Contexto
- **Pedido do usuário:** [resumo]
- **Domínio:** [identidade | organizacional | pessoas-institucionais | academico]
- **App(s) afetado(s):** [caminho no projeto]

## O que será feito
[1–3 frases em linguagem simples]

## Arquivos e camadas

| Arquivo | Ação | O que muda |
|---------|------|------------|
| models.py | criar/alterar | ... |
| rules.py | criar/alterar | ... |
| business.py | criar/alterar | ... |
| ... | ... | ... |

## Regras de negócio
- [regra 1]
- [regra 2]

## Permissões (Cortex L1/L2/L3)
- [quem pode fazer o quê]

## Riscos e pontos de atenção
- [ex.: migração, impacto em testes existentes]

## Testes previstos
- [cenário feliz]
- [cenário de erro / permissão negada]

## Fora do escopo (por ora)
- [o que NÃO será feito nesta entrega]

---
**Próximo passo:** Aprovar este plano para eu implementar, ou indicar ajustes.
```

---

## Durante a implementação (modo Agente)

1. Ler `docs/project/guia-implementacao.md` — aplicar **Checklist de Conformidade Obrigatório** em cada arquivo.
2. Consultar `docs/domains/<dominio>.md` para invariantes e vocabulário do domínio.
3. Views: **nunca** ORM, `transaction`, lógica de negócio — só delegação ao Business.
4. Business: **todo método** com `try/except` e `relancar_ou_erro_sistema`.
5. Rules: métodos em **português**; sem `.save()` / `.create()` / `.delete()`.
6. Ao terminar: resumir o que foi feito e indicar como testar.

---

## Prompts bons vs. ruins

### Bom (estruturado)
> "No domínio Organizacional, criar endpoint POST para vincular servidor a setor. Permissão L2. Validar que setor está ativo."

### Ruim (vago) — ainda assim aceitar
> "faz um endpoint de servidor"

**Resposta correta ao prompt vago:** explorar código, fazer 3–5 perguntas com opções, montar plano, pedir aprovação.

### Ruim (perigoso) — não inventar
> "cria a feature de matrícula com as regras que você achar melhor"

**Resposta correta:** perguntar regras de negócio, estados, permissões; apontar `docs/domains/academico.md`.

---

## Referências adicionais

- Checklist geral: `docs/project/implementation-checklist.md`
- Árvore do projeto: `docs/project/django-project-tree.md`
- Permissões: `docs/decisions/ADR-002-permissoes-cortex-niveis.md`
- Corrigir testes: `docs/project/guia-corrigir-testes.md`
- Exemplos de perguntas: [perguntas.md](perguntas.md)
