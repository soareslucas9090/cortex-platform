# Revisão Geral do AppCore — Resumo Executivo

## Objetivo

Este documento registra o resumo executivo da revisão inicial do `AppCore` e da base do projeto, com foco em verificar se a fundação atual está preparada para sustentar os domínios do Cortex.

A análise considera especialmente:

- autenticação e modelagem do usuário;
- arquitetura em camadas;
- views base;
- exceções e permissões;
- managers e comportamento de consulta;
- aderência da base ao domínio do Cortex.

---

## Diagnóstico geral

O `AppCore` atual é uma base **boa e promissora**, com decisões arquiteturais consistentes e vários componentes já bem encaminhados para sustentar o Cortex.

Os principais pontos positivos identificados foram:

- arquitetura em camadas explícita;
- mixins para `business`, `helpers`, `rules` e `state`;
- views base padronizadas;
- exceções customizadas;
- permissões reutilizáveis;
- paginação customizada;
- separação conceitual entre `AppCore`, `Auth` e `Cortex`.

Ao mesmo tempo, a revisão identificou que a base ainda precisa de alguns ajustes importantes antes do início efetivo dos apps de domínio.

---

## Conclusão principal

A conclusão da revisão é:

- a fundação do projeto pode ser mantida;
- mas alguns pontos precisam ser resolvidos antes de iniciar a implementação dos domínios centrais.

Os dois ajustes mais importantes identificados foram:

1. **resolver definitivamente a autenticação do usuário**
   - com suporte a login por email ou CPF;
   - alinhando `AUTH_USER_MODEL`, serializer de login, documentação e comportamento do `Auth`.

2. **remover o filtro automático por `ativo=True` do `BaseManager`**
   - deixando o comportamento do ORM previsível;
   - e deslocando o conceito de “ativos” para helpers e consultas explícitas.

---

## Decisões consolidadas nesta revisão

### 1. Estratégia de login

Foi consolidada a direção de permitir login usando:

- email
- ou CPF

A recomendação é usar um campo de entrada genérico no login, como `login`, com resolução do identificador via serializer/backend customizado.

---

### 2. Política de ativos

Foi consolidada a decisão de:

- remover a lógica implícita de `ativo=True` do `BaseManager.filter()`;
- tratar consultas por ativos em helpers e consultas explícitas do domínio.

---

## Resultado esperado após os ajustes

Após essas correções, a base deverá ficar mais adequada para:

- receber o domínio `identidade`;
- sustentar o `Usuario` real do sistema;
- permitir criação dos apps `organizacional`, `pessoas_institucionais` e `academico`;
- manter maior previsibilidade arquitetural;
- reduzir risco de retrabalho em autenticação e modelagem.

---

## Próximos passos previstos

A sequência prevista após esta revisão é:

1. definir o design exato da autenticação por email/CPF;
2. elaborar o plano de alteração arquivo por arquivo;
3. aplicar os ajustes de fundação no `AppCore`, `Auth` e `Cortex`;
4. só então iniciar a implementação dos apps de domínio.

---

## Resumo executivo

O `AppCore` está suficientemente bom para ser mantido como base do Cortex, mas não deve ser usado sem uma pequena rodada prévia de refatorações estruturais.

As duas prioridades imediatas são:

- autenticação híbrida por email/CPF;
- remoção do filtro implícito de ativos no manager base.
