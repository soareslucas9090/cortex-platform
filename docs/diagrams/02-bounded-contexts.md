# Bounded Contexts / Domínios do Cortex

## Objetivo

Este documento define a divisão do Cortex por domínios de negócio, seus respectivos apps Django, suas responsabilidades, entidades centrais, dependências e ordem sugerida de implementação.

A organização do sistema deve seguir **domínios com inicial maiúscula** e **apps Django em minúsculo**, mantendo coesão de negócio e evitando modularização orientada apenas por tipo técnico.

Exemplos:

- Domínio: `Organizacional`
- App Django: `organizacional`

---

## Princípios adotados

1. O sistema deve ser organizado por **domínio de negócio**.
2. Cada app Django representa um **contexto de negócio coeso**.
3. O DER serve como **mapa inicial dos models**, mas a divisão dos apps é orientada por regra de negócio e responsabilidade.
4. A arquitetura base do projeto continua em camadas:
   - `models.py`
   - `business.py`
   - `rules.py`
   - `helpers.py`
   - `serializers.py`
   - `views.py`
   - `urls.py`
5. Views devem permanecer leves, delegando para a camada de business.
6. O sistema deve priorizar clareza de domínio antes de otimizações prematuras.

---

## Visão geral dos domínios

O Cortex será inicialmente dividido nos seguintes domínios:

1. `Identidade`
2. `Organizacional`
3. `PessoasInstitucionais`
4. `Academico`

---

## 1. Domínio: Identidade

### App Django

`identidade`

### Responsabilidade

Responsável pelo cadastro base da pessoa no sistema, concentrando os dados centrais de identificação e contato que podem ser compartilhados por diferentes perfis institucionais.

### Entidades

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

### Descrição das entidades

- `Usuario`: entidade central de autenticação e identificação da pessoa no sistema.
- `Contato`: dados de contato associados ao usuário.
- `Endereco`: endereço associado ao usuário.
- `Matricula`: identificadores institucionais e/ou acadêmicos associados ao usuário.

### Observações de domínio

- `Usuario` é a entidade central sobre a qual orbitam os demais perfis.
- Outros domínios dependem de `Usuario`.
- Este domínio fornece a base de identidade para servidores, alunos e terceirizados.

### Dependências

- Não depende de outros domínios centrais do negócio.

---

## 2. Domínio: Organizacional

### App Django

`organizacional`

### Responsabilidade

Responsável pela estrutura organizacional da instituição e pelos vínculos dos usuários com setores e funções exercidas.

### Entidades

- `Setor`
- `Funcao`
- `SetorVinculo`

### Descrição das entidades

- `Setor`: unidade organizacional da instituição.
- `Funcao`: papel exercido pelo usuário em determinado setor.
- `SetorVinculo`: vínculo entre usuário, setor e função.

### Regras de domínio já definidas

- Um usuário pode estar vinculado a múltiplos setores.
- Todo usuário vinculado a um setor deve possuir uma função.
- Todo setor deve possuir um servidor responsável.
- O responsável pelo setor exerce uma função no próprio setor.
- A função `monitor` deve ser representada como registro em `Funcao`, e não como atributo booleano em `SetorVinculo`.
- `Funcao` deve possuir o atributo `e_gratificada`.

### Observações de modelagem

- `SetorVinculo` não é apenas uma tabela associativa; é uma entidade de negócio.
- A responsabilidade do setor deve emergir do vínculo, e não necessariamente de um campo direto em `Setor`.
- A regra de obrigatoriedade de responsável deve ser implementada na camada de negócio/regras.

### Dependências

- Depende de `Identidade`, pois `SetorVinculo` referencia `Usuario`.

---

## 3. Domínio: PessoasInstitucionais

### App Django

`pessoas_institucionais`

### Responsabilidade

Responsável pelos perfis institucionais formais vinculados ao usuário dentro da organização, incluindo vínculos funcionais e empresariais.

### Entidades

- `Servidor`
- `Cargo`
- `Terceirizado`
- `EmpresaInstituicao`

### Descrição das entidades

- `Servidor`: perfil institucional de servidor vinculado ao usuário.
- `Cargo`: cargo formal do servidor.
- `Terceirizado`: perfil institucional de terceirizado vinculado ao usuário.
- `EmpresaInstituicao`: empresa relacionada ao terceirizado.

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

### App Django

`academico`

### Responsabilidade

Responsável pelos perfis acadêmicos e pelos vínculos do aluno com os cursos.

### Entidades

- `Aluno`
- `Curso`
- `AlunoCurso`

### Descrição das entidades

- `Aluno`: perfil acadêmico vinculado ao usuário.
- `Curso`: curso institucional.
- `AlunoCurso`: vínculo entre aluno e curso.

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

## Estrutura inicial esperada por app

Cada app de domínio deve seguir a convenção arquitetural do projeto:

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

A organização inicial do Cortex será baseada em quatro domínios:

- `Identidade`
- `Organizacional`
- `PessoasInstitucionais`
- `Academico`

Essa divisão busca:

- refletir o negócio com mais fidelidade;
- evitar acoplamento técnico desnecessário;
- permitir crescimento controlado do sistema;
- manter clareza arquitetural desde o início.
