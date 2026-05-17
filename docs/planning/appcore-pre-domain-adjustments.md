# AppCore — Ajustes necessários antes de iniciar os apps de domínio

## Objetivo

Este documento registra os ajustes que devem ser feitos na base do projeto antes do início da implementação dos apps de domínio do Cortex.

Esses ajustes são considerados importantes para reduzir retrabalho e garantir coerência entre a fundação técnica e a modelagem do sistema.

---

## 1. Resolver definitivamente a autenticação do usuário

### Problema atual

A base atual ainda está num estado intermediário em relação à autenticação:

- a configuração de `AUTH_USER_MODEL` ainda está provisória;
- a documentação do login ainda oscila entre email e CPF;
- o thin app `Auth` ainda não está plenamente alinhado ao modelo real do Cortex.

### Ajuste necessário

Definir de forma explícita:

- qual será o model concreto de usuário do projeto;
- qual será o valor final de `AUTH_USER_MODEL`;
- como o login aceitará email e CPF;
- como o serializer do login funcionará;
- como a documentação Swagger refletirá isso.

### Direção recomendada

- `Usuario` concreto no domínio `identidade`;
- `AUTH_USER_MODEL` apontando para esse model;
- login com identificador genérico;
- autenticação por email ou CPF.

---

## 2. Remover o filtro automático de `ativo=True` do `BaseManager`

### Problema atual

O `BaseManager` altera o comportamento padrão do ORM ao incluir `ativo=True` automaticamente em chamadas a `filter()`.

### Risco

Esse comportamento:

- é implícito;
- dificulta previsibilidade;
- pode esconder registros em contextos administrativos;
- aumenta o risco de bugs sutis.

### Ajuste necessário

Remover essa lógica do manager base e deixar o ORM se comportar de forma padrão.

### Direção recomendada

Passar a tratar “ativos” em:

- helpers;
- consultas explícitas;
- regras de negócio do domínio.

---

## 3. Revisar o thin app `Auth`

### Problema atual

O app `Auth` ainda carrega traços de uma configuração genérica demais para a realidade do Cortex.

### Ajuste necessário

- alinhar serializers de login;
- alinhar documentação do Swagger;
- remover ambiguidade entre email e CPF;
- garantir aderência ao model real de usuário.

---

## 4. Revisar mensagens e exceções que expõem detalhes técnicos

### Problema atual

Existem pontos da base que ainda propagam mensagens excessivamente técnicas em exceções.

### Exemplo típico

Falhas de utilitário com interpolação direta do erro interno.

### Ajuste necessário

Padronizar:

- logging interno;
- mensagem genérica para camadas superiores;
- aderência às diretrizes de segurança já documentadas.

---

## 5. Revisar coerência das convenções da base

### Ajuste necessário

Antes de crescer os apps do domínio, vale alinhar:

- aspas simples;
- textos em português;
- mensagens consistentes;
- pequenos detalhes de naming e estilo.

### Motivo

Isso evita espalhar inconsistências para os novos módulos do sistema.

---

## 6. Rever o placeholder atual de `AUTH_USER_MODEL`

### Problema atual

A configuração atual ainda aponta para um model que não representa a modelagem definitiva do Cortex.

### Ajuste necessário

Substituir a configuração provisória por uma estratégia real, consistente com o domínio `identidade`.

---

## Resumo executivo

Antes de começar os apps `identidade`, `organizacional`, `pessoas_institucionais` e `academico`, a base deve passar por uma rodada curta de ajustes estruturais.

As prioridades são:

1. autenticação do usuário;
2. remoção do filtro mágico do manager base;
3. alinhamento do `Auth` com o Cortex;
4. limpeza de mensagens, exceções e convenções.
