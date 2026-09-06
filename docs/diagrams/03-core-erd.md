# Core ERD do Cortex

## Objetivo

Este documento consolida a leitura textual do DER principal do Cortex, ajustando a modelagem inicial às decisões mais recentes do domínio.

Ele serve como referência para:

- criação dos models Django;
- organização dos apps por domínio;
- definição de relacionamentos;
- alinhamento entre negócio e implementação.

Este documento não substitui o diagrama visual, mas funciona como sua tradução arquitetural e semântica para o projeto.

---

## Escopo atual

O núcleo inicial do domínio do Cortex está organizado nestes contextos principais:

- `Identidade`
- `Organizacional`
- `PessoasInstitucionais`
- `Academico`
- `Transporte`

O DER textual abaixo descreve as entidades centrais e seus relacionamentos.

---

## Convenções deste documento

- Nomes de entidades estão em **PascalCase**
- Nomes de atributos estão em **snake_case**
- O texto descreve **conceito de domínio**, não necessariamente a implementação final exata no Django
- Quando houver dúvida entre solução relacional e solução de negócio, prevalece a solução orientada ao domínio

---

# 1. Domínio Identidade

## 1.1 Usuario

### Descrição

Entidade central de identidade do sistema.

Todo perfil institucional ou acadêmico parte de um `Usuario`.

### Atributos principais

- `id`
- `cpf`
- `nome`
- `foto`
- `deficiencia`
- `ativo`
- `password`
- `ultimo_login`
- `created_at`
- `updated_at`

### Observações

- O login do sistema será baseado em `cpf`
- `Usuario` é a base para perfis como `Servidor`, `Terceirizado` e `Aluno`
- Outros domínios não devem duplicar dados centrais de identificação

---

## 1.2 Contato

### Descrição

Representa meios de contato associados a um usuário.

### Atributos principais

- `id`
- `usuario`
- `email_academico`
- `email_pessoal`
- `telefone`
- `created_at`
- `updated_at`

### Relacionamento

- um `Usuario` pode possuir zero ou muitos `Contato`

### Observações

A cardinalidade final pode ser revista na implementação se fizer mais sentido consolidar isso em relação 1:1, mas no DER atual o entendimento é de multiplicidade.

---

## 1.3 Endereco

### Descrição

Representa o endereço associado ao usuário.

### Atributos principais

- `id`
- `usuario`
- `endereco`
- `bairro`
- `cep`
- `complemento`
- `numero`
- `cidade`
- `estado`
- `created_at`
- `updated_at`

### Relacionamento

- um `Usuario` pode possuir zero ou um `Endereco`

---

## 1.4 Matricula

### Descrição

Representa registros de matrícula associados ao usuário.

### Atributos principais

- `id`
- `usuario`
- `matricula`
- `situacao`
- `created_at`
- `updated_at`

### Relacionamento

- um `Usuario` pode possuir uma ou muitas `Matricula`

### Observações

Esse model funciona como identificador institucional/acadêmico vinculado à pessoa.

---

# 2. Domínio Organizacional

## 2.1 Setor

### Descrição

Unidade organizacional da instituição.

### Atributos principais

- `id`
- `nome`
- `sigla`
- `ativo`
- `created_at`
- `updated_at`

### Observações

- O setor representa uma estrutura organizacional real do campus/instituição
- Todo setor deve possuir um servidor responsável
- A responsabilidade do setor deve emergir de `SetorVinculo`, e não necessariamente de um campo direto em `Setor`

---

## 2.2 Funcao

### Descrição

Representa a função exercida por um usuário dentro de um setor.

### Atributos principais

- `papel_funcao`
- `descricao`
- `e_gratificada`
- `ativo`
- `created_at`
- `updated_at`

### Observações

- `Funcao` não é a mesma coisa que `Cargo`
- `Funcao` representa papel exercido em contexto organizacional
- `monitor` deve ser modelado como uma função
- a função pode indicar papéis como diretor, coordenador, chefe, monitor etc.

---

## 2.3 SetorVinculo

### Descrição

Representa o vínculo entre um usuário, um setor e uma função.

Essa entidade é de negócio, e não apenas uma tabela associativa.

### Atributos principais

- `id`
- `usuario`
- `setor`
- `funcao`
- `responsavel`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Usuario` pode possuir muitos `SetorVinculo`
- um `Setor` pode possuir muitos `SetorVinculo`
- uma `Funcao` pode aparecer em muitos `SetorVinculo`

### Regras de domínio

- todo usuário vinculado a setor deve possuir uma função
- um usuário pode estar vinculado a múltiplos setores
- um setor deve possuir ao menos um vínculo com `responsavel=True`
- o responsável do setor deve ser um `Servidor`
- a responsabilidade sempre acontece dentro de um vínculo com função

### Observações

- `SetorVinculo` substitui o conceito anterior de `SetorLotacao`
- o atributo booleano `monitor` foi descartado
- monitoria passa a ser representada via `Funcao`

---

# 3. Domínio PessoasInstitucionais

## 3.1 Cargo

### Descrição

Representa o cargo formal do servidor na instituição.

### Atributos principais

- `id`
- `nome`
- `ativo`
- `created_at`
- `updated_at`

### Observações

- `Cargo` é exclusivo de `Servidor`
- exemplos: professor, técnico administrativo e cargos correlatos formais

---

## 3.2 Servidor

### Descrição

Perfil institucional de servidor vinculado a um `Usuario`.

### Atributos principais

- `usuario`
- `cargo`
- `categoria`
- `ativo`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Servidor` pertence a um único `Usuario`
- um `Servidor` possui um `Cargo`
- um `Cargo` pode estar associado a muitos `Servidor`

### Observações

- `Servidor` representa professor ou técnico-administrativo
- somente servidores podem assumir a responsabilidade principal de um setor

---

## 3.3 EmpresaInstituicao

### Descrição

Representa empresa ou instituição associada a terceirizados.

### Atributos principais

- `id`
- `nome`
- `cnpj`
- `ativo`
- `created_at`
- `updated_at`

### Observações

- por enquanto, este model será usado apenas para terceirizados

---

## 3.4 Terceirizado

### Descrição

Perfil institucional de terceirizado vinculado a um `Usuario`.

### Atributos principais

- `usuario`
- `empresa_instituicao`
- `ativo`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Terceirizado` pertence a um único `Usuario`
- uma `EmpresaInstituicao` pode possuir muitos `Terceirizado`

---

# 4. Domínio Academico

## 4.1 Aluno

### Descrição

Perfil acadêmico vinculado a um `Usuario`.

### Atributos principais

- `usuario`
- `ira`
- `ativo`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Aluno` pertence a um único `Usuario`

### Observações

- o comportamento de monitoria não deve ser modelado dentro de `Aluno`
- se um aluno atuar como monitor, isso deve ocorrer por `SetorVinculo` + `Funcao`

---

## 4.2 Curso

### Descrição

Representa um curso institucional.

### Atributos principais

- `id`
- `nome`
- `codigo_curso`
- `ativo`
- `created_at`
- `updated_at`

---

## 4.3 AlunoCurso

### Descrição

Representa o vínculo entre aluno e curso.

### Atributos principais

- `id`
- `aluno`
- `curso`
- `ano_conclusao`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Aluno` pode possuir muitos vínculos em `AlunoCurso`
- um `Curso` pode possuir muitos vínculos em `AlunoCurso`

### Observações

Esse model permite preservar o histórico de vínculos acadêmicos sem sobrecarregar o model `Aluno`.

---

# 5. Relações centrais do núcleo

## Relações de identidade

- `Usuario` 1:N `Contato`
- `Usuario` 0..1:1 `Endereco`
- `Usuario` 1:N `Matricula`

## Relações organizacionais

- `Usuario` 1:N `SetorVinculo`
- `Setor` 1:N `SetorVinculo`
- `Funcao` 1:N `SetorVinculo`

## Relações institucionais

- `Usuario` 1:1 `Servidor`
- `Cargo` 1:N `Servidor`
- `Usuario` 1:1 `Terceirizado`
- `EmpresaInstituicao` 1:N `Terceirizado`

## Relações acadêmicas

- `Usuario` 1:1 `Aluno`
- `Aluno` 1:N `AlunoCurso`
- `Curso` 1:N `AlunoCurso`

## Relações de transporte

- `Percurso` 1:N `Rota`
- `Rota` 1:N `ExecucaoRota`
- `ExecucaoRota` 1:N `Ticket`
- `Aluno` 1:N `Ticket`
- `Ticket` 0..1:1 `Strike`
- `Aluno` 1:N `Justificativa`
- `Justificativa` N:M `Strike` (`strikes_cobertos`)

---

# 6. Regras semânticas importantes

## 6.1 Identidade central

Todo perfil do sistema deve partir de `Usuario`.

## 6.2 Cargo e função são conceitos diferentes

- `Cargo` = posição formal do servidor
- `Funcao` = papel exercido em contexto organizacional

## 6.3 Vínculo com setor exige função

Não pode existir `SetorVinculo` sem `Funcao`.

## 6.4 Um usuário pode possuir múltiplos vínculos organizacionais

Especialmente em casos como professores vinculados a múltiplos setores ou coordenações.

## 6.5 Todo setor precisa de responsável

Essa responsabilidade deve ser representada por um `SetorVinculo` cujo usuário seja um `Servidor`.

## 6.6 Monitoria é função, não flag

O conceito de monitor deve ser representado em `Funcao`, e não como atributo booleano em vínculo.

## 6.7 Cargo é exclusivo de servidor

Terceirizados não possuem `Cargo`.

---

# 7. Mapeamento dos models por app interno e domínio

## Módulo: `Identidade/`
- `Identidade.usuarios` -> Model: `Usuario`
- `Identidade.contatos` -> Model: `Contato`
- `Identidade.enderecos` -> Model: `Endereco`
- `Identidade.matriculas` -> Model: `Matricula`

## Módulo: `Organizacional/`
- `Organizacional.setores` -> Model: `Setor`
- `Organizacional.funcoes` -> Model: `Funcao`
- `Organizacional.vinculos` -> Model: `SetorVinculo`

## Módulo: `PessoasInstitucionais/` (Planejado)
- `PessoasInstitucionais.cargos` -> Model: `Cargo`
- `PessoasInstitucionais.servidores` -> Model: `Servidor`
- `PessoasInstitucionais.empresas_instituicoes` -> Model: `EmpresaInstituicao`
- `PessoasInstitucionais.terceirizados` -> Model: `Terceirizado`

## Módulo: `Academico/` (Planejado)
- `Academico.alunos` -> Model: `Aluno`
- `Academico.cursos` -> Model: `Curso`
- `Academico.aluno_cursos` -> Model: `AlunoCurso`

## Módulo: `Transporte/`

- `Transporte.percursos` -> Model: `Percurso`
- `Transporte.rotas` -> Model: `Rota`
- `Transporte.motoristas` -> Model: `Motorista`
- `Transporte.execucoes_rotas` -> Model: `ExecucaoRota`
- `Transporte.tickets` -> Model: `Ticket`
- `Transporte.strikes` -> Model: `Strike`
- `Transporte.justificativas` -> Model: `Justificativa`

---

# 8. Diretrizes para implementação no Django

## Herança e especialização

Perfis como `Servidor`, `Terceirizado` e `Aluno` devem especializar `Usuario` via relacionamento 1:1.

## Arquitetura em camadas por app interno

Cada **app interno** possui sua própria estrutura de camadas independente, e não o domínio agregador como um todo. Cada app interno deve conter, conforme a necessidade:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

## Regras de negócio

As regras semânticas do DER não devem ser jogadas diretamente nas views. Devem ser implementadas prioritariamente em:

- `rules.py`
- `business.py`

## Responsabilidade do setor

A garantia de que todo setor possui responsável deve ser tratada como regra de negócio, e não apenas como restrição superficial de interface.

---

# 9. Domínio Transporte

## 9.1 Percurso

Trajeto nomeado do ônibus universitário.

### Atributos principais

- `id`
- `apelido` (único, case-insensitive)
- `descricao`
- `ativo`

## 9.2 Rota

Agendamento de um ônibus em um percurso, em um dia e horário.

### Atributos principais

- `id`
- `percurso` (FK `PROTECT`, N:1)
- `horario_saida`
- `dia_semana`
- `quantidade_vagas` (≥ 1)
- `ativo`

### Relacionamentos

- Uma `Rota` pertence a exatamente um `Percurso`
- Um `Percurso` pode ter várias `Rota`

### Invariantes

- Não vincular nem reativar rota em percurso inativo
- Não desativar percurso com rotas ativas
- Unicidade de `percurso` + `dia_semana` + `horario_saida`

## 9.3 Motorista

Perfil operacional associado 1:1 a `Usuario`.

### Atributos principais

- `usuario` (`OneToOne`, PK, `on_delete=PROTECT`)
- `ativo`

### Relacionamentos

- `Usuario` 1 : 0..1 `Motorista`
- Cada `Motorista` pertence a exatamente um `Usuario`

### Restrições

- Um `Usuario` pode possuir no máximo um perfil `Motorista`
- A exclusão física do `Usuario` é protegida enquanto existir um `Motorista`
- O acesso operacional exige simultaneamente `Usuario.ativo` e `Motorista.ativo`

## 9.4 ExecucaoRota

Ocorrência de uma rota em uma data e horário congelados.

- `rota` (FK `PROTECT`)
- `data_execucao`
- `data_hora_saida`
- `quantidade_vagas`
- `status`
- unicidade de `rota` + `data_execucao`

Rotas distintas do mesmo percurso podem possuir execuções no mesmo dia quando
seus horários forem diferentes.

## 9.5 Ticket

Vínculo entre `Aluno` e `ExecucaoRota`, identificado externamente por UUID.

- estados: reservado, em espera, cancelado, embarcado e ausente;
- no máximo um ticket não cancelado por aluno e execução;
- tickets em espera formam a fila, sem entidades `Fila` ou `FilaEspera` separadas.

## 9.6 Strike, bloqueio e justificativa

- `Aluno` possui `faltas` (strikes ativos no ciclo), `is_bloqueado` (três ou mais
  faltas ativas) e `quantidade_bloqueios` (histórico de vezes em bloqueio);
- `Strike` possui relação 1:1 com o ticket ausente;
- `Justificativa` pertence ao aluno e cobre N strikes ativos via M2M `strikes_cobertos`;
- justificativa aprovada marca os strikes cobertos como `JUSTIFICADO` e ressincroniza
  `faltas` e `is_bloqueado`; `quantidade_bloqueios` não é zerada.

---

# 10. Pontos que podem evoluir depois

Os itens abaixo podem ser refinados em artefatos posteriores ou na modelagem detalhada:

- cardinalidade final de `Contato`
- necessidade de datas de início/fim em `SetorVinculo`
- necessidade de histórico explícito de função em setor
- detalhamento da categoria do servidor
- detalhamento da situação da matrícula
- regras adicionais para aluno monitor
- notificações, perfis de motorista e conferente; entrada sem ticket pertence a `ExecucaoRota`

---

# 11. Resumo executivo

O núcleo do Cortex parte de `Usuario` como centro da identidade, e organiza o restante do sistema em torno de:

- estrutura organizacional (`Setor`, `Funcao`, `SetorVinculo`)
- perfis institucionais (`Servidor`, `Terceirizado`, `Cargo`, `EmpresaInstituicao`)
- perfis acadêmicos (`Aluno`, `Curso`, `AlunoCurso`)
- transporte universitário (`Percurso`, `Rota`, `Motorista`, `ExecucaoRota`, `Ticket`,
  `EntradaSemTicket`, `Strike`, `Justificativa`)

As decisões mais importantes consolidadas neste ERD textual são:

- modularização por domínio;
- separação entre cargo e função;
- substituição de `SetorLotacao` por `SetorVinculo`;
- função obrigatória em todo vínculo com setor;
- monitoria tratada como função;
- responsabilidade de setor modelada por vínculo.
