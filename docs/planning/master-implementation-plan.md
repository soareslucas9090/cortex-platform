# Plano Mestre de Implementação do Cortex

## Objetivo

Este documento define a estratégia principal de implementação do Cortex, organizando o desenvolvimento em milestones sequenciais e controladas.

Ele foi pensado para orientar um fluxo de trabalho em que:

- o planejamento acontece antes da implementação;
- cada etapa possui escopo claro;
- a base técnica é ajustada antes dos domínios;
- o uso de agentes de IA na implementação seja mais preciso, previsível e seguro.

Este plano mestre deve funcionar como referência para:

- decidir a ordem das implementações;
- planejar prompts;
- evitar retrabalho;
- controlar dependências entre milestones;
- manter alinhamento entre domínio, arquitetura e execução.

---

## Estratégia geral

A implementação do Cortex deve seguir uma abordagem **por milestones**, e cada milestone deve ser tratada em quatro momentos:

1. **Planejamento da milestone**
2. **Desenho técnico da milestone**
3. **Implementação da milestone**
4. **Revisão da milestone**

A ideia central é evitar pedidos amplos demais ao agente de implementação, reduzindo o risco de:

- extrapolação de escopo;
- decisões inventadas;
- acoplamento indevido;
- implementação fora de ordem.

---

## Decisões já assumidas neste plano

Este plano já considera como decisões consolidadas:

- organização do sistema por domínio;
- nomes conceituais de domínio com inicial maiúscula;
- nomes técnicos dos apps Django em minúsculo;
- documentação centralizada dentro de `docs/`;
- domínios iniciais:
  - `Identidade`
  - `Organizacional`
  - `PessoasInstitucionais`
  - `Academico`
- substituição de `SetorLotacao` por `SetorVinculo`;
- `Funcao` com atributo `e_gratificada`;
- monitor representado como função;
- autenticação por email ou CPF;
- remoção da lógica implícita de `ativo=True` do manager base;
- tratamento de “ativos” por helpers e consultas explícitas.

---

## Milestones do projeto

## Milestone 0 — Fundação técnica

### Objetivo

Ajustar a base técnica existente antes do início efetivo dos apps de domínio.

### Escopo principal

- revisar e ajustar autenticação;
- consolidar estratégia de login por email ou CPF;
- preparar estratégia final de `AUTH_USER_MODEL`;
- revisar e ajustar o thin app `Auth`;
- remover o filtro implícito de `ativo=True` do `BaseManager`;
- preparar a base para receber o domínio `Identidade`.

### Motivo

Sem essa milestone, existe alto risco de retrabalho em:

- autenticação;
- migrations;
- model concreto de usuário;
- integração entre `Auth`, `AppCore` e domínio real.

---

## Milestone 1 — Domínio Identidade

### Objetivo

Criar o núcleo do usuário real do sistema e os dados centrais de identidade.

### Escopo principal

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`
- manager concreto
- business, rules e helpers do domínio
- serializers, views e urls básicas

### Motivo

`Identidade` sustenta todos os demais domínios.

---

## Milestone 2 — Domínio Organizacional

### Objetivo

Modelar a estrutura institucional e os vínculos funcionais com setores.

### Escopo principal

- `Setor`
- `Funcao`
- `SetorVinculo`
- regra de responsável
- regra de função obrigatória
- monitor como função

### Motivo

Esse domínio representa uma das áreas mais sensíveis e estruturantes do sistema.

---

## Milestone 3 — Domínio PessoasInstitucionais

### Objetivo

Modelar os perfis institucionais formais dos usuários.

### Escopo principal

- `Servidor`
- `Cargo`
- `Terceirizado`
- `EmpresaInstituicao`

### Motivo

Esse domínio depende de `Identidade` e interage com `Organizacional`, especialmente na regra de responsabilidade de setor.

---

## Milestone 4 — Domínio Academico

### Objetivo

Modelar perfis acadêmicos e vínculos com cursos.

### Escopo principal

- `Aluno`
- `Curso`
- `AlunoCurso`

### Motivo

Esse domínio depende de `Identidade` e se conecta ao `Organizacional` em casos como monitoria.

---

## Milestone 5 — Integrações e consolidação

### Objetivo

Revisar o sistema como um todo e consolidar as integrações entre domínios.

### Escopo principal

- ajustes de integração entre domínios;
- validação de regras cruzadas;
- revisão final de documentação;
- consolidação de massa inicial e cenários de uso;
- refinos estruturais e arquiteturais.

---

## Fluxo padrão por milestone

Cada milestone deve seguir o mesmo fluxo.

### Etapa A — Planejamento da milestone

Definir:

- escopo;
- exclusões;
- dependências;
- critérios de aceite;
- riscos.

### Etapa B — Desenho técnico

Definir:

- models;
- regras;
- contratos de API;
- arquivos impactados;
- estratégia de implementação.

### Etapa C — Implementação

Pedir ao agente apenas o escopo da milestone atual.

### Etapa D — Revisão

Verificar:

- aderência à arquitetura;
- aderência às decisões do domínio;
- ausência de extrapolações;
- qualidade geral da implementação.

---

## Regras de uso com agente de implementação

### 1. Nunca pedir o sistema inteiro de uma vez

A implementação deve ser feita sempre por milestone.

### 2. Nunca misturar planejamento com implementação no mesmo prompt

Planejamento e execução devem ocorrer separadamente.

### 3. Levar decisões estratégicas já fechadas para o prompt

O agente não deve decidir sozinho aspectos como:

- autenticação;
- modelagem central;
- semântica dos domínios;
- convenções principais.

### 4. Sempre explicitar o que não deve ser implementado

Isso ajuda a reduzir extrapolação de escopo.

### 5. Revisar a saída de cada milestone antes de iniciar a próxima

Erros estruturais devem ser corrigidos cedo.

---

## Critérios de avanço entre milestones

## Para sair da Milestone 0 e entrar na Milestone 1

Deve estar resolvido:

- design de autenticação;
- alinhamento do `Auth`;
- preparação da estratégia de `AUTH_USER_MODEL`;
- remoção do filtro implícito do manager base.

## Para sair da Milestone 1 e entrar na Milestone 2

Deve estar resolvido:

- usuário concreto funcional;
- identidade central estável;
- integração inicial de autenticação consistente.

## Para sair da Milestone 2 e entrar na Milestone 3

Deve estar resolvido:

- `Setor`, `Funcao` e `SetorVinculo` estáveis;
- regra de responsável clara e consistente.

## Para sair da Milestone 3 e entrar na Milestone 4

Deve estar resolvido:

- perfis institucionais estáveis;
- integração com `Usuario` funcional.

## Para sair da Milestone 4 e entrar na Milestone 5

Deve estar resolvido:

- vínculo acadêmico consistente;
- monitoria corretamente tratada no domínio `Organizacional`.

---

## Riscos que este plano busca evitar

- começar pelos apps errados;
- retrabalho em autenticação e modelagem do usuário;
- acoplamento precoce entre domínios;
- prompts amplos demais;
- inconsistência entre arquitetura documentada e código gerado;
- decisões estratégicas sendo improvisadas pelo agente.

---

## Ordem prática recomendada

A ordem prática recomendada a partir deste plano é:

1. detalhar a **Milestone 0**
2. criar o **prompt da Milestone 0**
3. executar a **Milestone 0**
4. revisar a **Milestone 0**
5. detalhar a **Milestone 1**
6. seguir adiante milestone por milestone

---

## Próximo passo sugerido

O próximo passo imediato, a partir deste documento, é elaborar:

- o plano da **Milestone 0 — Fundação técnica**

Esse plano deve detalhar:

- objetivo;
- escopo;
- o que entra e o que não entra;
- arquivos impactados;
- critérios de aceite;
- e posteriormente o prompt de implementação.

---

## Resumo executivo

O Cortex deve ser implementado em milestones progressivas:

1. fundação técnica
2. identidade
3. organizacional
4. pessoas institucionais
5. acadêmico
6. consolidação

Essa estratégia reduz retrabalho, melhora a qualidade dos prompts, aumenta a previsibilidade da implementação com agentes de IA e protege a coerência arquitetural do sistema.
