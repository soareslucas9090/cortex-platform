# Plano da Milestone 0 — Fundação técnica

## Objetivo

A Milestone 0 existe para preparar a fundação técnica do Cortex antes da implementação dos apps de domínio.

Ela deve ajustar a base atual do projeto para que os próximos passos possam acontecer com menor risco de retrabalho, especialmente em torno de:

- autenticação;
- modelagem do usuário;
- comportamento do manager base;
- alinhamento do thin app `Auth`;
- consistência mínima do `AppCore`.

Esta milestone **não implementa os domínios do sistema**.  
Ela apenas prepara a base para que a Milestone 1 (`Identidade`) possa começar de forma correta.

---

## Resultado esperado ao final da milestone

Ao final da Milestone 0, a base do projeto deve estar pronta para:

1. suportar a estratégia de login por email ou CPF;
2. abandonar o filtro implícito de `ativo=True` no manager base;
3. alinhar o `Auth` ao comportamento real esperado do sistema;
4. receber o futuro model concreto `identidade.Usuario` sem ambiguidade estrutural.

---

## Escopo da milestone

## 1. Estratégia de autenticação

### O que deve ser resolvido

- contrato de autenticação com campo único `login`;
- suporte a email ou CPF como identificador;
- normalização adequada do CPF;
- alinhamento do serializer de login;
- alinhamento da documentação do login;
- preparação da configuração central do Django para backend customizado.

### Objetivo

Preparar a base para que o login do Cortex seja consistente, previsível e extensível.

---

## 2. Limpeza do manager base

### O que deve ser resolvido

- remoção do comportamento implícito que injeta `ativo=True` em `filter()`;
- restauração do comportamento padrão do ORM;
- formalização da decisão de que consultas por ativos devem ocorrer de forma explícita, especialmente em helpers.

### Objetivo

Eliminar um comportamento “mágico” que tende a gerar bugs sutis e dificultar previsibilidade.

---

## 3. Alinhamento do thin app `Auth`

### O que deve ser resolvido

- remover a ambiguidade entre login por email e login por CPF;
- ajustar serializers e documentação para `login + password`;
- deixar a camada de autenticação coerente com a estratégia do Cortex.

### Objetivo

Garantir que o `Auth` represente o contrato real do projeto, e não um modelo genérico indefinido.

---

## 4. Pequenos ajustes de coerência da base

### O que deve ser resolvido

- revisar utilitários que expõem erro técnico demais;
- aplicar pequenas limpezas de consistência em pontos já identificados;
- preparar a base para a próxima milestone sem ampliar desnecessariamente o escopo.

### Objetivo

Reduzir ruído técnico antes da entrada dos domínios reais.

---

## O que entra

Esta milestone pode incluir alterações em arquivos como:

- `Cortex/settings.py`
- `AppCore/basics/models/models.py`
- `AppCore/common/util/util.py`
- `Auth/auth/serializers.py`
- `Auth/auth/views.py`
- `AppCore/basics/auth/serializers.py`
- `AppCore/basics/auth/views.py`

Também pode incluir a criação de novos arquivos de fundação, como por exemplo:

- backend customizado de autenticação

---

## O que não entra

Esta milestone **não deve** incluir:

- criação do app `identidade`;
- criação do model concreto `Usuario`;
- implementação de `Contato`, `Endereco` ou `Matricula`;
- criação dos apps `organizacional`, `pessoas_institucionais` ou `academico`;
- endpoints de domínio;
- regras de domínio específicas;
- seeds;
- migrações estruturais dos domínios;
- qualquer ampliação de escopo para além da fundação técnica.

---

## Dependências

A Milestone 0 depende de decisões já consolidadas anteriormente:

- login por email ou CPF;
- remoção do filtro implícito de ativos do manager base;
- organização por domínio;
- futura existência de `identidade.Usuario` como usuário concreto do sistema;
- estratégia de implementação por milestones.

---

## Critérios de aceite

A Milestone 0 só deve ser considerada concluída quando:

### 1. Autenticação estiver tecnicamente bem definida

- o contrato do login estiver claro;
- a documentação refletir `login + password`;
- a base estiver preparada para autenticação por email ou CPF.

### 2. `BaseManager` estiver neutro

- `filter()` não deve mais injetar `ativo=True`.

### 3. `Auth` estiver coerente com a estratégia real

- sem ambiguidade entre email e CPF;
- sem contrato antigo contraditório.

### 4. A base estiver pronta para a Milestone 1

- sem bloqueios estruturais óbvios para o domínio `Identidade`.

---

## Riscos da milestone

## 1. Escopo excessivo

Se o pedido de implementação for amplo demais, o agente pode:

- começar a criar o domínio `Identidade` cedo demais;
- introduzir acoplamento com estruturas ainda não implementadas;
- extrapolar para regras de negócio fora da fundação.

## 2. Escopo insuficiente

Se o pedido for vago demais, o agente pode:

- alterar apenas documentação;
- não tocar nos pontos críticos;
- preservar ambiguidade técnica no login e no manager.

## 3. Acoplamento prematuro

Se o prompt não for bem controlado, o agente pode tentar resolver o model concreto de usuário dentro desta milestone, o que deve ser evitado.

---

## Arquivos impactados prioritariamente

Os arquivos mais importantes desta milestone são:

- `Cortex/settings.py`
- `AppCore/basics/models/models.py`
- `AppCore/common/util/util.py`
- `Auth/auth/serializers.py`
- `Auth/auth/views.py`

Arquivos adicionais podem ser tocados se necessário, mas a implementação deve permanecer restrita ao objetivo da milestone.

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- base de autenticação coerente com email/CPF;
- manager base sem filtro implícito;
- thin app `Auth` alinhado ao contrato do projeto;
- documentação de login coerente;
- fundação pronta para a implementação do domínio `Identidade`.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 0, o próximo passo deve ser:

- elaborar o plano da **Milestone 1 — Domínio Identidade**

Só então deve começar a implementação do usuário concreto e das entidades centrais do domínio.

---

## Resumo executivo

A Milestone 0 prepara a fundação técnica do Cortex antes da entrada dos domínios reais.

Ela existe para resolver os pontos estruturais mais sensíveis da base atual, especialmente:

- autenticação por email ou CPF;
- neutralidade do manager base;
- alinhamento do `Auth`;
- limpeza mínima do `AppCore`.

Seu sucesso depende de manter escopo controlado e evitar a tentação de já começar os domínios nesta etapa.
