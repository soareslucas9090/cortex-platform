# Bounded Contexts / Domínios do Cortex

## Objetivo

Este documento define a divisão do Cortex por domínios de negócio, seus respectivos módulos agregadores, as responsabilidades de seus apps internos, entidades centrais, dependências e ordem de implementação.

A organização do sistema deve seguir **domínios como módulos agregadores com inicial maiúscula** e **apps internos em minúsculo**, mantendo a regra de que cada app corresponde a um model principal, garantindo coesão e acoplamento baixo.

Exemplos:
- Domínio/Módulo: `Organizacional`
- App interno: `Organizacional/setores/`

---

## Princípios adotados

1. O sistema deve ser organizado por **domínios de negócio** (módulos agregadores).
2. Cada módulo de domínio contém **apps internos específicos e finos**.
3. Em regra, cada app interno representa **um model principal** e suas entidades auxiliares.
4. A arquitetura de camadas é aplicada no nível de cada app interno:
   - `models.py`
   - `business.py`
   - `rules.py`
   - `helpers.py`
   - `serializers.py`
   - `views.py`
   - `urls.py`
5. Views devem permanecer leves, delegando toda lógica de negócio e queries para as camadas apropriadas.
6. O sistema deve priorizar clareza e consistência do domínio antes de otimizações prematuras.

---

## Visão geral dos domínios

O Cortex será inicialmente dividido nos seguintes domínios:

1. `Identidade`
2. `Organizacional`
3. `PessoasInstitucionais`
4. `Academico`

---

## 1. Domínio: Identidade

### Módulo Agregador
`Identidade/`

### Apps Django Internos e Entidades:
- `usuarios` -> Model principal: `Usuario` (autenticação e dados cadastrais básicos)
- `contatos` -> Model principal: `Contato` (meios de contato como e-mails e telefones)
- `enderecos` -> Model principal: `Endereco` (dados de residência)
- `matriculas` -> Model principal: `Matricula` (identificadores institucionais)

### Responsabilidade
Responsável pelo cadastro base da pessoa no sistema, concentrando os dados centrais de identificação e contato que são compartilhados por diferentes perfis institucionais.

### Observações de domínio
- `Usuario` (dentivo do app `usuarios`) é a entidade central sobre a qual orbitam os demais perfis.
- Outros domínios dependem de `Usuario`.
- Este domínio fornece a base de identidade para servidores, alunos e terceirizados.

### Dependências
- Não depende de outros domínios centrais do negócio.

---

## 2. Domínio: Organizacional

### Módulo Agregador
`Organizacional/`

### Apps Django Internos e Entidades:
- `setores` -> Model principal: `Setor` (unidade física/organizacional)
- `funcoes` -> Model principal: `Funcao` (papel formal do vínculo - ex: coordenador, monitor)
- `vinculos` -> Model principal: `SetorVinculo` (vínculo real do usuário com setor e função)

### Responsabilidade
Responsável pela estrutura organizacional da instituição e pelos vínculos dos usuários com setores e funções exercidas.

### Regras de domínio já definidas
- Um usuário pode estar vinculado a múltiplos setores.
- Todo usuário vinculado a um setor deve possuir uma função.
- Todo setor deve possuir um servidor responsável.
- O responsável pelo setor exerce uma função no próprio setor.
- A função `monitor` deve ser representada como registro em `Funcao`, e não como atributo booleano em `SetorVinculo`.
- `Funcao` deve possuir o atributo `e_gratificada`.

### Observações de modelagem
- `SetorVinculo` (no app `vinculos`) não é apenas uma tabela associativa; é uma entidade de negócio em camadas.
- A responsabilidade do setor deve emergir do vínculo (`responsavel=True` em `SetorVinculo`), e não de um campo direto em `Setor`.
- A regra de obrigatoriedade de responsável deve ser implementada na camada de negócio/regras.

### Dependências
- Depende de `Identidade` (referencia `Usuario`).

---

## 3. Domínio: PessoasInstitucionais

### Módulo Agregador
`PessoasInstitucionais/` (Planejado)

### Apps Django Internos e Entidades:
- `servidores` -> Model principal: `Servidor` (perfil docente ou técnico-administrativo)
- `cargos` -> Model principal: `Cargo` (posição formal do servidor)
- `terceirizados` -> Model principal: `Terceirizado` (prestador de serviço externo)
- `empresas_instituicoes` -> Model principal: `EmpresaInstituicao` (empresa parceira do terceirizado)

### Responsabilidade
Responsável pelos perfis institucionais formais vinculados ao usuário dentro da organização, incluindo vínculos funcionais e empresariais.

### Regras de domínio já definidas
- `Cargo` se aplica apenas a `Servidor`.
- `Servidor` representa professor ou técnico-administrativo.
- `EmpresaInstituicao` será usada, por ora, apenas para terceirizados.

### Observações de domínio
- Este domínio não substitui `Usuario`; ele especializa a identidade da pessoa.
- As regras de lotação e exercício em setor pertencem ao domínio `Organizacional`, mesmo quando relacionadas a servidores.

### Dependências
- Depende de `Identidade`.

---

## 4. Domínio: Academico

### Módulo Agregador
`Academico/` (Planejado)

### Apps Django Internos e Entidades:
- `alunos` -> Model principal: `Aluno` (perfil acadêmico da pessoa)
- `cursos` -> Model principal: `Curso` (curso de graduação/técnico)
- `aluno_cursos` -> Model principal: `AlunoCurso` (relação M:N entre alunos e cursos)

### Responsabilidade
Responsável pelos perfis acadêmicos e pelos vínculos do aluno com os cursos.

### Regras de domínio já definidas
- Alunos que atuarem como monitores devem possuir vínculo com setor.
- A monitoria deve ser tratada pelo domínio `Organizacional`, usando `SetorVinculo` + `Funcao`.

### Observações de domínio
- O comportamento organizacional do aluno monitor não deve ser modelado como exceção no domínio acadêmico.
- O domínio acadêmico representa o vínculo do aluno com a formação, não sua função organizacional.

### Dependências
- Depende de `Identidade`.
- Em situações de monitoria, se relaciona conceitualmente com `Organizacional`.

---

## Relações entre domínios

### Identidade

Domínio base do sistema.

### Organizacional

Depende de `Identidade`.

### PessoasInstitucionais

Depende de `Identidade`.

### Academico

Depende de `Identidade`.

### Relações conceituais cruzadas

- `Organizacional` pode operar sobre usuários que sejam servidores, terceirizados ou alunos.
- `Academico` e `PessoasInstitucionais` especializam a identidade do usuário.
- `Organizacional` modela o exercício funcional em setor, independentemente do perfil institucional da pessoa.

---

## Decisões importantes já consolidadas

### Convenção de nomenclatura

- **Domínios**: inicial maiúscula
- **Apps Django**: minúsculo

### Nome da entidade de vínculo com setor

- Nome adotado: `SetorVinculo`
- Nome descartado: `SetorLotacao`

### Representação de monitoria

- `monitor` não será atributo booleano em `SetorVinculo`
- `monitor` será uma `Funcao`

### Obrigatoriedade de função

- Todo vínculo com setor exige uma função

### Gratificação

- `Funcao` deverá possuir o atributo `e_gratificada`

### Cargo

- `Cargo` é exclusivo de `Servidor`

---

## Ordem sugerida de implementação

### 1. Identidade

Motivo:

- Fornece a entidade central `Usuario`
- Sustenta todos os demais domínios

### 2. Organizacional

Motivo:

- Estrutura setores, funções e vínculos
- Representa uma parte central do funcionamento institucional
- Permite modelar responsabilidades e monitoria desde cedo

### 3. PessoasInstitucionais

Motivo:

- Especializa o usuário em servidor e terceirizado
- Introduz cargo e empresa de terceirização

### 4. Academico

Motivo:

- Depende da identidade do usuário
- Pode reaproveitar a estrutura organizacional para monitoria

---

## Estrutura inicial esperada por app interno

Cada app interno do módulo de domínio deve seguir a convenção arquitetural de camadas do projeto:

- `__init__.py`
- `apps.py`
- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

Arquivos opcionais conforme necessidade:
- `choices.py`
- `state.py`

---

## Próximos artefatos recomendados

Após este documento, os próximos artefatos sugeridos são:

1. `diagrams/03-core-erd.md`
   - consolidar o DER ajustado aos nomes e regras atuais

2. `decisions/ADR-001-modularizacao-por-dominio.md`
   - registrar formalmente a decisão arquitetural de modularização por domínio

3. `project/django-project-tree.md`
   - definir a árvore inicial do projeto com os apps `identidade`, `organizacional`, `pessoas_institucionais` e `academico`

4. `diagrams/04-aggregates-and-invariants.md`
   - definir agregados e invariantes principais do domínio

---

## Resumo executivo

A organização inicial do Cortex será baseada em quatro domínios (Bounded Contexts) implementados como módulos agregadores contendo apps internos finos:

- `Identidade` (com sub-apps `usuarios`, `contatos`, `enderecos`, `matriculas`)
- `Organizacional` (com sub-apps `setores`, `funcoes`, `vinculos`)
- `PessoasInstitucionais` (com sub-apps planejados `servidores`, `cargos`, etc.)
- `Academico` (com sub-apps planejados `alunos`, `cursos`, etc.)

Essa divisão busca:
- refletir o negócio com mais fidelidade;
- evitar acoplamento técnico desnecessário através da regra de um app principal por model;
- permitir crescimento controlado do sistema mantendo views leves e lógica em camadas;
- manter clareza arquitetural desde o início.
