---
name: revisao-codigo
description: Revisa código Cortex/DRF contra padrões do projeto. Use quando o usuário pedir revisão, code review, checar conformidade, ou /revisao-codigo.
disable-model-invocation: true
---

# Revisão de Código — Novo Cortex

## Objetivo

Revisar código Python do projeto verificando conformidade com os padrões arquiteturais. Esta skill **orquestra o processo**; os checklists detalhados estão em `docs/`.

## Fontes obrigatórias

1. `docs/project/regras-do-projeto.md` — regras gerais e proibições
2. `docs/project/guia-revisao-de-codigo.md` — checklists por tipo de arquivo
3. `docs/domains/<dominio>.md` — quando o código pertence a um domínio específico

---

## Processo de revisão

### 1. Entender o pedido

Identificar:
- **O quê** revisar (arquivo, diff, PR, app inteiro)
- **Por quê** (PR, dúvida do aluno, pré-merge, aprendizado)
- **Critérios extras** do usuário (segurança, performance, cobertura de testes)

Se faltar informação crítica → perguntar com opções A/B/C + **"Outro (descreva):"**.

**Escopo vago?** Inferir do código aberto ou do diff e **confirmar** com o usuário antes de concluir.

### 2. Coletar evidências (antes de opinar)

Não revisar "de memória". Ler:

- Arquivo(s) alvo indicado(s)
- Arquivos vizinhos da mesma feature: `business.py`, `rules.py`, `helpers.py`, `views.py`, `urls.py`, `serializers.py`, `tests/`
- Diff/git status, se disponível
- Doc do domínio em `docs/domains/`

### 3. Aplicar checklists

Executar os checklists de `docs/project/guia-revisao-de-codigo.md` conforme o tipo de arquivo detectado. Resumo rápido em [checklist.md](checklist.md).

Um arquivo pode exigir mais de um checklist (ex.: view + serializer no mesmo módulo).

### 4. Produzir relatório

Para cada achado:

| Campo | Conteúdo |
|-------|----------|
| **Problema** | O que está errado (linha/trecho) |
| **Por quê** | Qual padrão do projeto é violado |
| **Como corrigir** | Sugestão concreta com exemplo curto |
| **Severidade** | Crítico / Importante / Sugestão |

### 5. Encerrar

- Se sem problemas: confirmar conformidade e citar o que foi verificado.
- Se com problemas: priorizar **Crítico** primeiro; não reescrever o mundo inteiro — focar no escopo pedido.

---

## Severidades

| Nível | Quando usar | Exemplo |
|-------|-------------|---------|
| **Crítico** | Quebra padrão obrigatório, risco de bug ou segurança | ORM na view; business sem try/except |
| **Importante** | Viola convenção; funciona mas dificulta manutenção | Método `can_*` em rules; URL sem `name=` |
| **Sugestão** | Melhoria opcional, estilo, clareza | Comentário redundante; nome pouco descritivo |

---

## Perguntas quando falta contexto

### Escopo

**O que devo revisar?**
- A) Arquivo específico que vou indicar
- B) Diff / mudanças não commitadas
- C) Toda a feature (views + business + rules + testes)
- D) Apenas conformidade com views leves
- Outro (descreva):

### Profundidade

**Qual nível de detalhe?**
- A) Rápido — só problemas Críticos e Importantes
- B) Completo — incluir Sugestões e estilo
- C) Didático — explicar cada padrão como para iniciante
- Outro (descreva):

---

## Template de relatório

```markdown
# Revisão: [arquivo ou escopo]

**Escopo:** [o que foi revisado]
**Referências:** regras-do-projeto.md, guia-revisao-de-codigo.md[, domínio X]

## Resumo
[1–2 frases: conformidade geral, contagem por severidade]

## Achados

### 1. [Título curto] — Crítico
- **Onde:** `arquivo.py`, linha N
- **Problema:** ...
- **Padrão violado:** ... (ver docs/project/...)
- **Correção sugerida:**
  ```python
  # exemplo curto
  ```

### 2. [Título curto] — Importante
...

## Conformidades verificadas
- [ ] Views leves / Basic*APIView
- [ ] Business com try/except
- [ ] Rules em português
- [ ] URLs com name=
- [ ] ...

## Próximos passos
[O que o aluno deve corrigir primeiro]
```

---

## Tom para alunos leigos

- Explique o padrão em linguagem simples antes de citar o trecho errado.
- Um problema por item; exemplo de correção **curto** (não reescrever arquivo inteiro).
- Se o código estiver correto mas o aluno não entender o padrão, incluir link para a seção relevante em `docs/`.

---

## O que NÃO fazer

- Não revisar sem ler os arquivos.
- Não sugerir refatoração massiva fora do escopo.
- Não duplicar o guia inteiro na resposta — apontar para `docs/project/guia-revisao-de-codigo.md`.
- Não misturar revisão de negócio profunda — para isso, usar a skill `validacao-negocio`.
