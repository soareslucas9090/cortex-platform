# Aggregates and Invariants do Cortex

## Objetivo

Este documento define os agregados iniciais do Cortex e suas invariantes principais.

Ele existe para complementar o ERD e responder a perguntas que o diagrama relacional, sozinho, não resolve bem:

- quais entidades devem ser tratadas como núcleo de consistência;
- quais regras precisam ser sempre verdadeiras;
- onde determinadas validações devem morar;
- quais operações podem atravessar mais de uma entidade;
- quais limites devem orientar a camada de business.

Este artefato deve ser usado como referência para implementação de:

- `business.py`
- `rules.py`
- decisões de criação e atualização de entidades
- validações de integridade de negócio

---

## Conceitos adotados

### Aggregate

Um agregado é um agrupamento de entidades e regras que devem ser tratadas como uma unidade de consistência do ponto de vista do domínio.

### Aggregate Root

É a entidade raiz do agregado, responsável por controlar o acesso consistente às demais entidades daquele agrupamento.

### Invariant

É uma regra que deve permanecer verdadeira sempre que o sistema estiver em estado consistente.

---

## Visão geral dos agregados iniciais

Os agregados iniciais identificados no Cortex são:

1. `UsuarioAggregate`
2. `SetorAggregate`
3. `ServidorAggregate`
4. `TerceirizadoAggregate`
5. `AlunoAggregate`
6. `CursoAggregate`

---

# 1. UsuarioAggregate

## Aggregate Root

`Usuario`

## Entidades relacionadas

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

## Responsabilidade

Representa a identidade central da pessoa no sistema, reunindo os dados cadastrais e relacionamentos básicos que orbitam o usuário.

## Motivo para ser agregado

As informações de identidade tendem a mudar em conjunto e dependem semanticamente do usuário como entidade central.

## Invariantes

1. Todo `Contato` deve pertencer a um `Usuario`.
2. Todo `Endereco` deve pertencer a um `Usuario`.
3. Toda `Matricula` deve pertencer a um `Usuario`.
4. O `cpf` do usuário deve ser único no sistema.
5. O login do sistema deve ser baseado no `cpf`.
6. Perfis institucionais e acadêmicos não devem duplicar dados centrais de identidade.

## Regras operacionais

- criação de usuário deve garantir unicidade de `cpf`;
- atualização de dados cadastrais deve ocorrer a partir do agregado de usuário;
- contatos, endereço e matrículas devem ser manipulados preservando o vínculo com o usuário.

## Onde as regras devem morar

- validações simples e teóricas: `identidade/rules.py`
- orquestração de criação/atualização: `identidade/business.py`

---

# 2. SetorAggregate

## Aggregate Root

`Setor`

## Entidades relacionadas

- `Setor`
- `SetorVinculo`
- `Funcao`

## Responsabilidade

Representa a unidade organizacional e os vínculos de usuários que exercem funções dentro dela.

## Motivo para ser agregado

As regras mais críticas do domínio organizacional giram em torno do setor, especialmente sua composição funcional, responsabilidade e vínculos.

## Invariantes

1. Todo `SetorVinculo` deve estar associado a um `Setor`.
2. Todo `SetorVinculo` deve estar associado a um `Usuario`.
3. Todo `SetorVinculo` deve possuir uma `Funcao`.
4. Todo setor deve possuir ao menos um vínculo marcado como responsável.
5. O vínculo responsável do setor deve apontar para um usuário que seja `Servidor`.
6. A responsabilidade do setor deve ser exercida dentro de um vínculo com função.
7. `monitor` não deve existir como atributo booleano em `SetorVinculo`.
8. A função de monitor deve ser representada por `Funcao`.
9. Um mesmo usuário pode possuir múltiplos vínculos com setores distintos.
10. `Funcao` deve possuir o atributo `e_gratificada`.

## Regras operacionais

- criação de vínculo com setor exige função obrigatória;
- definição do responsável do setor deve validar se o usuário é servidor;
- troca de responsável deve preservar a existência contínua de um responsável válido;
- remoção do único responsável de um setor não pode ser permitida sem substituição adequada;
- alunos monitores devem ser representados como usuários vinculados a setor com função correspondente.

## Onde as regras devem morar

- invariantes teóricas: `organizacional/rules.py`
- criação, troca e atualização de vínculos: `organizacional/business.py`

## Observações importantes

Embora `Funcao` seja um catálogo, ela participa diretamente da consistência do agregado porque o vínculo organizacional depende dela semanticamente.

---

# 3. ServidorAggregate

## Aggregate Root

`Servidor`

## Entidades relacionadas

- `Servidor`
- `Cargo`

## Dependência conceitual externa

- `Usuario`

## Responsabilidade

Representa o perfil institucional de servidor e sua relação com cargo formal na instituição.

## Motivo para ser agregado

As regras de servidor são específicas e não devem se misturar com identidade pura nem com terceirização.

## Invariantes

1. Todo `Servidor` deve estar associado a um único `Usuario`.
2. Todo `Servidor` deve possuir um `Cargo`.
3. `Cargo` é exclusivo de `Servidor`.
4. Um `Cargo` pode estar associado a múltiplos servidores.
5. Apenas servidores podem ocupar a responsabilidade principal de um setor.

## Regras operacionais

- criação de servidor exige usuário base existente;
- criação de servidor exige cargo válido;
- um usuário não deve ter múltiplos perfis redundantes de servidor;
- validações sobre elegibilidade de responsabilidade de setor podem consultar este agregado.

## Onde as regras devem morar

- regras específicas do perfil de servidor: `pessoas_institucionais/rules.py`
- orquestração de criação/atualização: `pessoas_institucionais/business.py`

---

# 4. TerceirizadoAggregate

## Aggregate Root

`Terceirizado`

## Entidades relacionadas

- `Terceirizado`
- `EmpresaInstituicao`

## Dependência conceitual externa

- `Usuario`

## Responsabilidade

Representa o perfil institucional de terceirizado vinculado a uma empresa/instituição.

## Invariantes

1. Todo `Terceirizado` deve estar associado a um único `Usuario`.
2. Todo `Terceirizado` deve estar associado a uma `EmpresaInstituicao`.
3. `EmpresaInstituicao`, no escopo atual, é utilizada apenas para terceirizados.
4. Terceirizados não possuem `Cargo`.

## Regras operacionais

- criação de terceirizado exige usuário base;
- criação de terceirizado exige empresa válida;
- regras futuras de escopo e permissões podem partir desse perfil.

## Onde as regras devem morar

- validações de vínculo terceirizado-empresa: `pessoas_institucionais/rules.py`
- orquestração operacional: `pessoas_institucionais/business.py`

---

# 5. AlunoAggregate

## Aggregate Root

`Aluno`

## Entidades relacionadas

- `Aluno`
- `AlunoCurso`

## Dependência conceitual externa

- `Usuario`
- `Curso`

## Responsabilidade

Representa o perfil acadêmico do usuário e seus vínculos com cursos.

## Invariantes

1. Todo `Aluno` deve estar associado a um único `Usuario`.
2. Todo `AlunoCurso` deve estar associado a um `Aluno`.
3. Todo `AlunoCurso` deve estar associado a um `Curso`.
4. A atuação de um aluno como monitor não deve ser modelada diretamente em `Aluno`.
5. A monitoria de aluno deve ser representada no domínio `Organizacional`, por meio de `SetorVinculo` + `Funcao`.

## Regras operacionais

- criação de aluno exige usuário base;
- vinculação do aluno a curso deve ocorrer por `AlunoCurso`;
- histórico acadêmico deve ser preservado via entidade de vínculo, evitando sobrecarga do model `Aluno`.

## Onde as regras devem morar

- validações acadêmicas: `academico/rules.py`
- criação de vínculo aluno-curso: `academico/business.py`

---

# 6. CursoAggregate

## Aggregate Root

`Curso`

## Entidades relacionadas

- `Curso`
- `AlunoCurso`

## Responsabilidade

Representa o curso e sua relação com os vínculos acadêmicos dos alunos.

## Invariantes

1. Todo `Curso` deve possuir identificação institucional coerente.
2. Um `Curso` pode participar de múltiplos vínculos em `AlunoCurso`.
3. O histórico de vínculos acadêmicos deve ser preservado via `AlunoCurso`.

## Regras operacionais

- criação de curso deve garantir integridade de identificação;
- atualizações de curso não devem quebrar vínculos acadêmicos existentes.

## Onde as regras devem morar

- regras do curso: `academico/rules.py`
- operações de manutenção do curso: `academico/business.py`

---

# Invariantes transversais

As regras abaixo atravessam mais de um agregado e precisam ser tratadas com cuidado na camada de negócio.

## 1. Todo perfil parte de um usuário

Perfis como `Servidor`, `Terceirizado` e `Aluno` dependem da existência prévia de `Usuario`.

## 2. Responsável de setor deve ser servidor

Embora a regra afete diretamente `SetorAggregate`, ela depende da existência consistente de `ServidorAggregate`.

## 3. Aluno monitor depende de vínculo organizacional

A condição de monitor não nasce no agregado acadêmico, mas sim no organizacional.

## 4. Cargo e função não podem ser confundidos

- `Cargo` pertence ao contexto institucional do servidor
- `Funcao` pertence ao contexto organizacional do vínculo com setor

---

# Fronteiras recomendadas para a camada de business

## `identidade/business.py`

Deve orquestrar:

- criação de usuário;
- atualização cadastral;
- manutenção de contatos, endereço e matrículas.

## `organizacional/business.py`

Deve orquestrar:

- criação de setor;
- criação e atualização de vínculos;
- definição de responsável;
- validação de função obrigatória;
- operações relacionadas à monitoria como função.

## `pessoas_institucionais/business.py`

Deve orquestrar:

- criação de servidor;
- criação de terceirizado;
- associação de cargo;
- associação de empresa.

## `academico/business.py`

Deve orquestrar:

- criação de aluno;
- criação de curso;
- vínculo entre aluno e curso.

---

# Regras que não devem ir para as views

As seguintes validações não devem ser implementadas diretamente nas views:

- verificação de existência de responsável válido para setor;
- verificação de que responsável é servidor;
- validação de que vínculo com setor possui função;
- validação de exclusividade ou coerência de perfis;
- verificação de consistência entre aluno monitor e vínculo organizacional;
- verificação de unicidade semântica de `cpf`.

As views devem apenas:

- receber a requisição;
- validar o serializer;
- delegar à camada de business.

---

# Operações críticas que exigem atenção

## No domínio Organizacional

- criar vínculo de setor;
- alterar função de um vínculo;
- definir responsável;
- remover vínculo responsável;
- substituir responsável sem deixar setor inconsistente.

## No domínio PessoasInstitucionais

- criar servidor com cargo;
- criar terceirizado com empresa;
- validar se determinado usuário pode ocupar responsabilidade de setor.

## No domínio Academico

- criar vínculo aluno-curso;
- representar monitoria sem duplicar regra no agregado errado.

---

# Recomendações de implementação

## 1. Tratar agregados como fronteiras de consistência

Mesmo que o banco permita operações isoladas, a camada de business deve respeitar o agregado como unidade lógica.

## 2. Centralizar invariantes em rules + business

- `rules.py`: decide se algo pode
- `business.py`: executa e orquestra

## 3. Evitar duplicação de regra entre domínios

Se a monitoria pertence ao organizacional, ela não deve nascer como conceito paralelo no acadêmico.

## 4. Diferenciar invariantes fortes de conveniências de interface

Exemplo:

- “todo vínculo com setor precisa de função” = invariante forte
- “exibir nome do responsável na listagem” = conveniência de interface

---

# Possíveis refinamentos futuros

Este documento ainda pode evoluir com:

- definição de invariantes temporais;
- datas de início/fim em `SetorVinculo`;
- regras de troca de cargo;
- regras de coexistência de perfis no mesmo usuário;
- restrições mais detalhadas de matrícula e situação acadêmica;
- regras específicas para múltiplos vínculos simultâneos no mesmo setor.

---

# Resumo executivo

Os agregados iniciais do Cortex foram definidos em torno de:

- identidade da pessoa;
- estrutura organizacional;
- perfis institucionais;
- perfis acadêmicos.

A principal consequência prática desta definição é:

- regras de consistência devem ser pensadas por agregado;
- invariantes devem ser respeitadas fora das views;
- `Setor` e seus vínculos formam um dos núcleos mais sensíveis do sistema;
- `Cargo` e `Funcao` são conceitos distintos e pertencem a agregados/contextos diferentes;
- monitoria deve ser tratada no domínio organizacional, nunca como atalho em model acadêmico.
