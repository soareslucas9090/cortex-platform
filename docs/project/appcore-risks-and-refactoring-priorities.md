# AppCore — Riscos arquiteturais e prioridades de refatoração

## Objetivo

Este documento consolida os principais riscos arquiteturais identificados na revisão inicial do `AppCore`, bem como a lista priorizada de refatorações recomendadas antes do início efetivo dos apps de domínio do Cortex.

---

# Riscos arquiteturais

## 1. Iniciar os domínios antes de consolidar o usuário real

### Risco

Começar a implementar os domínios do sistema sem definir corretamente:

- o model concreto de `Usuario`;
- o `AUTH_USER_MODEL`;
- o fluxo de autenticação;
- a documentação do login.

### Impacto

Isso pode causar:

- retrabalho em migrations;
- refatorações profundas na autenticação;
- desalinhamento entre `Auth`, `AppCore` e domínio `Identidade`.

---

## 2. Manter comportamento implícito no manager base

### Risco

Deixar o `BaseManager` interferir silenciosamente nas consultas com `ativo=True`.

### Impacto

Isso pode:

- dificultar debugging;
- esconder registros inativos;
- gerar comportamento inesperado em regras de negócio, admin e relatórios.

---

## 3. Manter o `Auth` num estado genérico demais

### Risco

Permitir que o app `Auth` continue num meio-termo entre base genérica e implementação concreta do Cortex.

### Impacto

Isso pode gerar:

- ambiguidade no login;
- documentação inconsistente;
- dificuldade de integração com o domínio real.

---

## 4. Espalhar regra de domínio em infraestrutura genérica

### Risco

Empurrar decisões específicas do Cortex para dentro de componentes excessivamente genéricos do `AppCore`.

### Impacto

Isso enfraquece:

- modularidade;
- reutilização da base;
- clareza de fronteira entre framework interno e domínio do sistema.

---

## 5. Fazer a documentação avançar mais rápido que a base técnica

### Risco

Ter documentação madura, mas fundação técnica ainda incompleta.

### Impacto

Isso aumenta a chance de:

- desalinhamento entre visão e implementação;
- criação precoce de código sobre base instável;
- retrabalho estrutural.

---

# Lista priorizada de refatorações no AppCore

## Prioridade 1 — fechar autenticação do Cortex

### Ajustes

- definir estratégia final de autenticação;
- suportar login por email ou CPF;
- alinhar serializer de login;
- alinhar documentação Swagger;
- alinhar `AUTH_USER_MODEL` ao model real do projeto.

### Resultado esperado

Fundação estável para o domínio `Identidade`.

---

## Prioridade 2 — remover inteligência implícita do `BaseManager`

### Ajustes

- retirar a lógica de `ativo=True` do `filter()`;
- deixar o manager base previsível;
- empurrar a semântica de ativos para helpers/consultas explícitas.

### Resultado esperado

Menor risco de bugs silenciosos e maior clareza nas consultas.

---

## Prioridade 3 — alinhar `Auth` ao projeto real

### Ajustes

- revisar `LoginInputSerializer`;
- revisar contratos de autenticação;
- revisar documentação do login;
- retirar referências ambíguas sobre email/CPF.

### Resultado esperado

Thin app de autenticação coerente com o Cortex.

---

## Prioridade 4 — revisar utilitários que expõem erro interno

### Ajustes

- revisar utilitários como envio de email;
- evitar vazamento de detalhes técnicos em exceções;
- adotar logging interno com mensagens seguras para o cliente.

### Resultado esperado

Maior aderência às diretrizes de segurança já definidas no projeto.

---

## Prioridade 5 — padronização geral de convenções

### Ajustes

- aspas simples;
- mensagens em português;
- naming;
- pequenas inconsistências de estilo.

### Resultado esperado

Base mais consistente para expansão.

---

## Prioridade 6 — limpeza técnica e simplificação

### Ajustes

- pequenos refinamentos de legibilidade;
- simplificações em tratamento de exceção;
- revisão de comentários/documentação genérica demais.

### Resultado esperado

Base mais limpa, sem necessidade de mudança estrutural ampla.

---

# Resumo executivo

Os maiores riscos atuais do AppCore estão concentrados em:

- autenticação ainda não consolidada;
- comportamento implícito demais no manager base;
- desalinhamento parcial do `Auth` com o Cortex real.

A prioridade máxima de refatoração deve ser:

1. autenticação email/CPF;
2. limpeza do `BaseManager`;
3. alinhamento do `Auth`;
4. depois ajustes menores de segurança, consistência e estilo.
