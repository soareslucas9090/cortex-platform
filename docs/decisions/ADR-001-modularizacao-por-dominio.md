# ADR-001 — Modularização por Domínio

- **Status:** Aceito
- **Data:** 2026-05-17

## Contexto

O Cortex será construído sobre uma base Django/DRF já existente, seguindo a arquitetura em camadas adotada no projeto:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

Embora o DER sirva como mapa inicial para os models, a estrutura do sistema não deve ser organizada apenas por afinidade técnica ou por tabelas isoladas do banco de dados. O objetivo é que a organização da aplicação reflita os **domínios de negócio** do sistema.

Durante a análise inicial do domínio, foram identificados quatro agrupamentos coesos:

- `Identidade`
- `Organizacional`
- `PessoasInstitucionais`
- `Academico`

Além disso, foram definidas regras importantes do domínio que impactam diretamente a modularização:

- um usuário pode estar vinculado a múltiplos setores;
- todo usuário vinculado a um setor deve possuir uma função;
- todo setor deve possuir um servidor responsável;
- a responsabilidade do setor é exercida dentro de um vínculo com função;
- `monitor` será representado como função, e não como atributo booleano;
- `Cargo` é exclusivo de `Servidor`;
- `Funcao` deverá possuir o atributo `e_gratificada`.

Com isso, tornou-se necessário formalizar a decisão de modularizar o sistema por domínio.

---

## Decisão

O Cortex será modularizado por **domínios de negócio**, e cada domínio será implementado como um **app Django próprio**, mantendo a convenção:

- **Domínio** com inicial maiúscula, para uso conceitual e documental;
- **app Django** com nome minúsculo, para uso no código e na estrutura do projeto.

Os domínios iniciais definidos são:

### 1. Identidade

App Django: `identidade`

Responsável por:

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

### 2. Organizacional

App Django: `organizacional`

Responsável por:

- `Setor`
- `Funcao`
- `SetorVinculo`

### 3. PessoasInstitucionais

App Django: `pessoas_institucionais`

Responsável por:

- `Servidor`
- `Cargo`
- `Terceirizado`
- `EmpresaInstituicao`

### 4. Academico

App Django: `academico`

Responsável por:

- `Aluno`
- `Curso`
- `AlunoCurso`

---

## Justificativa

A modularização por domínio foi escolhida porque:

1. **Reflete melhor o negócio**
   - O sistema passa a espelhar a linguagem do domínio, e não apenas a estrutura técnica do framework.

2. **Melhora coesão**
   - Entidades e regras que mudam juntas tendem a permanecer no mesmo módulo.

3. **Reduz acoplamento acidental**
   - Evita apps genéricos demais, como um único módulo de “cadastros” ou separações artificiais por tipo técnico.

4. **Facilita evolução incremental**
   - Permite iniciar por domínios essenciais e expandir o sistema sem desorganizar a base.

5. **Apoia a arquitetura em camadas já adotada**
   - Cada domínio poderá manter suas próprias classes de `business`, `rules`, `helpers` e `views`.

6. **Cria melhor base para documentação**
   - Os artefatos de domínio, DER, agregados e decisões arquiteturais ficam mais consistentes entre si.

---

## Implicações

### Estrutura de projeto

Cada domínio será representado por um app Django com estrutura semelhante a:

- `__init__.py`
- `apps.py`
- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

Arquivos opcionais:

- `choices.py`
- `state.py`

### Dependências entre domínios

A dependência principal entre os domínios será:

- `Identidade` como domínio base;
- `Organizacional` depende de `Identidade`;
- `PessoasInstitucionais` depende de `Identidade`;
- `Academico` depende de `Identidade`.

### Regras de fronteira

- O domínio `Organizacional` é responsável pela lógica de vínculo entre usuário, setor e função.
- A monitoria deve ser tratada em `Organizacional`, por meio de `Funcao` e `SetorVinculo`.
- `Cargo` permanece no domínio `PessoasInstitucionais`, por ser exclusivo de `Servidor`.
- O domínio `Academico` modela vínculo acadêmico, não a atuação organizacional do aluno.

---

## Consequências positivas

- Melhor alinhamento entre código e negócio.
- Maior clareza na criação de apps futuros.
- Facilidade para documentação, onboarding e manutenção.
- Menor risco de concentrar regras demais em um único módulo genérico.
- Melhor base para crescimento controlado do sistema.

---

## Consequências negativas / trade-offs

- Exige maior disciplina na definição de fronteiras entre domínios.
- Pode gerar dúvidas iniciais sobre onde colocar entidades transversais.
- Requer documentação mínima para evitar que a modularização perca consistência ao longo do tempo.

---

## Alternativas consideradas

### 1. Modularização por tipo técnico

Exemplo:

- app de usuários
- app de autenticação
- app de cadastros
- app de tabelas auxiliares

#### Motivo para não adotar

Essa abordagem tende a misturar conceitos de negócio diferentes apenas porque compartilham natureza técnica semelhante.

---

### 2. Um único app central para todo o domínio inicial

Exemplo:

- colocar todas as entidades do sistema em um único app

#### Motivo para não adotar

Embora simplifique o começo, essa abordagem dificulta evolução, aumenta acoplamento e reduz clareza arquitetural com o tempo.

---

### 3. Modularização excessivamente fragmentada por entidade

Exemplo:

- um app para `setor`
- um app para `funcao`
- um app para `cargo`
- um app para `curso`

#### Motivo para não adotar

Isso criaria excesso de fragmentação, dependências pequenas demais e perda de visão de contexto.

---

## Decisões derivadas

A partir desta ADR, ficam consolidadas as seguintes definições:

1. O sistema será organizado por domínio.
2. Domínios terão inicial maiúscula apenas em documentação/conceito.
3. Apps Django terão nomes minúsculos.
4. `SetorLotacao` será renomeado para `SetorVinculo`.
5. `monitor` será representado como `Funcao`.
6. `Funcao` terá o atributo `e_gratificada`.
7. Todo vínculo com setor exigirá uma função.
8. A responsabilidade de setor será modelada por vínculo, e não necessariamente por campo direto no model de setor.

---

## Ordem inicial de implementação

A ordem recomendada de construção dos domínios é:

1. `Identidade`
2. `Organizacional`
3. `PessoasInstitucionais`
4. `Academico`

Essa ordem foi escolhida porque:

- `Identidade` fornece a base comum;
- `Organizacional` modela uma parte central da operação;
- `PessoasInstitucionais` especializa perfis institucionais;
- `Academico` pode reutilizar a infraestrutura já consolidada.

---

## Artefatos relacionados

- `docs/diagrams/02-bounded-contexts.md`
- `docs/project/django-project-tree.md`
- `docs/diagrams/03-core-erd.md`
- `docs/diagrams/04-aggregates-and-invariants.md`

---

## Resumo

Fica decidido que o Cortex será modularizado por domínio de negócio, usando apps Django separados e coesos, de forma a refletir melhor a linguagem do negócio, reduzir acoplamento e sustentar o crescimento do sistema com clareza arquitetural.
