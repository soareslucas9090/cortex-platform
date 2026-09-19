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

O núcleo do domínio do Cortex está organizado nestes contextos principais:

- `Identidade`
- `Organizacional`
- `PessoasInstitucionais`
- `Academico`
- `Infraestrutura`
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
- `email` (único, opcional)
- `cpf` (único, opcional)
- `nome`
- `foto` (URL externa)
- `foto_secundaria` (chave S3, upload próprio)
- `deficiencia` (choices, opcional)
- `colaborador_externo`
- `usuario_coletivo`
- `empresas_coletivo`, `cargos_coletivo`, `funcoes_coletivo`, `setores_coletivo` (pools M2M do coletivo)
- `ativo`
- `password`
- `ultimo_login`
- `created_at`
- `updated_at`

### Observações

- Login na API aceita **e-mail**, **CPF** ou **matrícula** ativa (`EmailOrCpfBackend` + resolução de matrícula no helper de usuário)
- `USERNAME_FIELD` permanece `cpf` para o Django admin e fluxos internos que usam `ModelBackend`
- `usuario_coletivo` autentica a sessão (ex.: guarita); o responsável operacional é escolhido no pool — conta coletiva **não** pode ser solicitante nem responsável de empréstimo em Infraestrutura
- `Usuario` é a base para perfis como `Servidor`, `Terceirizado`, `Aluno` e `Motorista`
- Outros domínios não devem duplicar dados centrais de identificação
- `ImportacaoLote` (app `Identidade.usuarios`) registra importações em massa de usuários, com no máximo um lote `EM_ANDAMENTO` por vez

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

- `Contato` possui FK N:1 para `Usuario` (`related_name='contatos'`)
- um `Usuario` pode possuir zero ou muitos `Contato`

---

## 1.3 Endereco

### Descrição

Representa o endereço associado ao usuário.

### Atributos principais

- `id`
- `usuario`
- `logradouro`
- `bairro`
- `cep`
- `complemento`
- `numero`
- `cidade`
- `estado`
- `created_at`
- `updated_at`

### Relacionamento

- `Endereco` possui `OneToOneField` com `Usuario` (`related_name='endereco'`)
- um `Usuario` possui zero ou um `Endereco`

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
- `categoria`
- `descricao`
- `e_gratificada`
- `exige_aluno`
- `ativo`
- `created_at`
- `updated_at`

### Observações

- `Funcao` não é a mesma coisa que `Cargo`
- `Funcao` representa papel exercido em contexto organizacional
- `monitor` deve ser modelado como uma função
- `exige_aluno` restringe o vínculo a usuários com perfil `Aluno` ativo
- `categoria` classifica o papel no catálogo (choices em `CategoriaFuncao`)
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

- `Cargo` é obrigatório para `Servidor` e opcional para `Terceirizado` (FK nullable)
- exemplos: professor, técnico administrativo e cargos correlatos formais

---

## 3.2 Servidor

### Descrição

Perfil institucional de servidor vinculado a um `Usuario`.

### Atributos principais

- `usuario`
- `cargo`
- `matricula`
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
- `matricula` é opcional e funciona como identificador institucional para login e consultas

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
- `cargo` (opcional)
- `data_inicio`, `data_fim` (opcionais)
- `matricula`
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
- `situacao`
- `forma_ingresso`
- `ativo`
- `faltas` (strikes ativos no transporte)
- `is_bloqueado` (bloqueio por três ou mais faltas ativas)
- `quantidade_bloqueios` (histórico de bloqueios)
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
- `matricula`
- `ano_conclusao`
- `created_at`
- `updated_at`

### Relacionamentos

- um `Aluno` pode possuir muitos vínculos em `AlunoCurso`
- um `Curso` pode possuir muitos vínculos em `AlunoCurso`

### Observações

- Esse model permite preservar o histórico de vínculos acadêmicos sem sobrecarregar o model `Aluno`.
- `matricula` é opcional e funciona como identificador acadêmico para login e consultas

---

# 5. Relações centrais do núcleo

## Relações de identidade

- `Usuario` 1:N `Contato`
- `Usuario` 0..1:1 `Endereco`

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

## Relações de infraestrutura

- `Bloco` 1:N `Sala`
- `Sala` 1:N `SalaSetor` N:1 `Setor`
- `Sala` 0..N `Recurso` (obrigatório para tipo chave)
- `Usuario` 1:N `Emprestimo` (como `solicitante` e como `responsavel`)
- `Emprestimo` 1:N `ItemEmprestimo` N:1 `Recurso`
- `Usuario` 1:N `Autorizacao` (beneficiário, concedente, revogador)
- `Sala` ou `Recurso` 1:N `Autorizacao` (alvo XOR)
- `Funcao` 1:0..1 `PermissaoFuncaoInfraestrutura`
- `Usuario` 1:0..1 `PermissaoUsuarioInfraestrutura`

## Relações de transporte

- `Percurso` 1:N `Rota`
- `Rota` 1:N `ExecucaoRota`
- `DiaCalendarioTransporte` (data única) orienta geração automática de execuções
- `ExecucaoRota` 1:N `Ticket`
- `Aluno` 1:N `Ticket`
- `Ticket` 0..1:1 `Strike`
- `Aluno` 1:N `Justificativa`
- `Justificativa` N:M `Strike` (`strikes_cobertos`)
- `ExecucaoRota` 1:N `EntradaSemTicket`
- `Funcao` 1:0..1 `PermissaoFuncaoTransporte`
- `Usuario` 1:0..1 `PermissaoUsuarioTransporte`
- Bloqueio de transporte: estado em `Aluno` (`is_bloqueado`, `faltas`), sem entidade `Bloqueio` em `models.py`

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

## 6.7 Cargo no perfil institucional

- todo `Servidor` deve possuir `Cargo`
- `Terceirizado` pode possuir `Cargo` opcional (FK nullable)

---

# 7. Mapeamento dos models por app interno e domínio

## Módulo: `Identidade/`
- `Identidade.usuarios` -> Model: `Usuario`
- `Identidade.contatos` -> Model: `Contato`
- `Identidade.enderecos` -> Model: `Endereco`

## Módulo: `Organizacional/`
- `Organizacional.setores` -> Model: `Setor`
- `Organizacional.funcoes` -> Model: `Funcao`
- `Organizacional.vinculos` -> Model: `SetorVinculo`

## Módulo: `PessoasInstitucionais/`
- `PessoasInstitucionais.cargos` -> Model: `Cargo`
- `PessoasInstitucionais.servidores` -> Model: `Servidor`
- `PessoasInstitucionais.empresas_instituicoes` -> Model: `EmpresaInstituicao`
- `PessoasInstitucionais.terceirizados` -> Model: `Terceirizado`

## Módulo: `Academico/`
- `Academico.alunos` -> Model: `Aluno`
- `Academico.cursos` -> Model: `Curso`
- `Academico.aluno_cursos` -> Model: `AlunoCurso`

## Módulo: `Infraestrutura/`

- `Infraestrutura.blocos` -> Model: `Bloco`
- `Infraestrutura.salas` -> Models: `Sala`, `SalaSetor`
- `Infraestrutura.recursos` -> Model: `Recurso`
- `Infraestrutura.autorizacoes` -> Model: `Autorizacao`
- `Infraestrutura.emprestimos` -> Models: `Emprestimo`, `ItemEmprestimo`
- `Infraestrutura.permissoes` -> Models: `PermissaoFuncaoInfraestrutura`, `PermissaoUsuarioInfraestrutura`
- `Infraestrutura.importacoes` -> Model: `ImportacaoLote`

## Módulo: `Transporte/`

- `Transporte.percursos` -> Model: `Percurso`
- `Transporte.rotas` -> Model: `Rota`
- `Transporte.motoristas` -> Model: `Motorista`
- `Transporte.calendario_operacional` -> Model: `DiaCalendarioTransporte`
- `Transporte.execucoes_rotas` -> Model: `ExecucaoRota`
- `Transporte.tickets` -> Model: `Ticket`
- `Transporte.strikes` -> Model: `Strike`
- `Transporte.justificativas` -> Model: `Justificativa`
- `Transporte.entradas_sem_ticket` -> Model: `EntradaSemTicket`
- `Transporte.permissoes` -> Models: `PermissaoFuncaoTransporte`, `PermissaoUsuarioTransporte`
- `Transporte.relatorios` -> objeto de domínio `RelatorioAlunos` (sem tabela própria)
- `Transporte.bloqueios` -> API de leitura do estado de bloqueio em `Aluno` (sem `models.py`)

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

# 9. Domínio Infraestrutura

Controle de espaços físicos, recursos, autorizações, empréstimos e devoluções. **Reservas** pertencem ao domínio, mas ficam fora da v1 (sem app `reservas` em `PROJECT_APPS`).

## 9.1 Bloco

Unidade física de agrupamento de salas.

- `nome`
- `ativo`

## 9.2 Sala e SalaSetor

`Sala` pertence a um `Bloco` (unicidade `bloco` + `nome`). `SalaSetor` associa `Sala` a `Setor` (unicidade `sala` + `setor`) e habilita retirada automática de **chaves** da sala para solicitantes com vínculo ativo no setor.

## 9.3 Recurso

Item emprestável com código de negócio único (`codigo`, distinto da PK).

- `tipo`: `chave`, `midia`, `material_didatico`
- `sala` (obrigatória para chave; opcional para demais tipos)
- `descricao`, `foto` (opcional), `em_avaria`, `ativo`
- estado derivado exibido: avaria → emprestado → reservado → disponível (`reservado` só quando reservas existirem)

## 9.4 Autorizacao

Concessão explícita de acesso a sala ou recurso.

- alvo **XOR**: exatamente um de `sala` ou `recurso`
- `beneficiario`, `concedente`
- `data_inicio`, `data_fim` (nula = permanente)
- `revogado_em`, `revogador`, `observacao`
- autorização por sala vale para todos os recursos da sala, inclusive cadastrados depois

## 9.5 Emprestimo e ItemEmprestimo

- `Emprestimo`: `solicitante`, `responsavel`, `retirada_em`, `observacao`; encerrado quando todos os itens têm `devolvido_em`
- `ItemEmprestimo`: `recurso`, `devolvido_em`; no máximo **um item aberto por recurso** (constraint parcial)
- devolução parcial permitida; troca de titular devolve e abre novo empréstimo sem vínculo entre registros
- empréstimos abertos há mais de 24h são sinalizados na UI (`atrasado`)

### Regras automáticas de retirada (complementam autorização)

- **Servidor** ativo: qualquer recurso
- **Terceirizado** ativo: qualquer **chave**; mídia/material didático exigem `Autorizacao` ou `retirada_irrestrita`
- solicitante com vínculo ativo em setor ligado à sala via `SalaSetor`: chaves da sala
- demais perfis (incluindo alunos): `Autorizacao` vigente ou `retirada_irrestrita`
- `usuario_coletivo` não é solicitante nem responsável; em conta coletiva o responsável vem do pool M2M

### Permissões do módulo (OR entre função e usuário)

Capacidades: `operar`, `cadastrar`, `autorizar`, `retirada_irrestrita` em `PermissaoFuncaoInfraestrutura` (1:1 com `Funcao`) e `PermissaoUsuarioInfraestrutura` (1:1 com `Usuario`), compiladas em `permissoes_infraestrutura()`.

## 9.6 ImportacaoLote (Infraestrutura)

Importação em massa de blocos/salas/recursos; no máximo um lote `EM_ANDAMENTO` por vez (constraint em `Infraestrutura.importacoes`).

---

# 10. Domínio Transporte

## 10.1 Percurso

Trajeto nomeado do ônibus universitário.

### Atributos principais

- `id`
- `apelido` (único, case-insensitive)
- `descricao`
- `ativo`

## 10.2 Rota

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

## 10.3 Motorista

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

## 10.4 DiaCalendarioTransporte

Calendário operacional por data (`data` única): `descricao`, `tipo`, `ativo`. Tipos operacionais permitem geração de execuções em dias que não seriam úteis só pelo dia da semana (fins de semana/feriados configurados). A task `gerar_execucoes_rotas_automaticas_task` roda via Celery Beat a cada **5 minutos** e consulta o calendário ao materializar `ExecucaoRota`.

## 10.5 ExecucaoRota

Ocorrência de uma rota em uma data e horário congelados.

- `rota` (FK `PROTECT`)
- `data_execucao`
- `data_hora_saida`
- `quantidade_vagas`
- `status`
- unicidade de `rota` + `data_execucao`

Rotas distintas do mesmo percurso podem possuir execuções no mesmo dia quando
seus horários forem diferentes.

## 10.6 Ticket

Vínculo entre `Aluno` e `ExecucaoRota`, identificado externamente por UUID.

- estados: reservado, em espera, cancelado, embarcado, ausente e contemplado (`StatusTicket.CONTEMPLADO` — aluno em espera contemplado por entrada sem ticket);
- no máximo um ticket não cancelado por aluno e execução;
- `posicao_reserva` persiste a posição ocupada ou histórica; posições de reservas
  ativas são únicas por execução;
- tickets em espera formam a fila, sem entidades `Fila` ou `FilaEspera` separadas.

## 10.7 Strike, bloqueio e justificativa

- `Aluno` possui `faltas` (strikes ativos no ciclo), `is_bloqueado` (três ou mais
  faltas ativas) e `quantidade_bloqueios` (histórico de vezes em bloqueio);
- `Strike` possui relação 1:1 com o ticket ausente;
- `Justificativa` pertence ao aluno e cobre N strikes ativos via M2M `strikes_cobertos`;
- justificativa aprovada marca os strikes cobertos como `JUSTIFICADO` e ressincroniza
  `faltas` e `is_bloqueado`; `quantidade_bloqueios` não é zerada;
- o app `Transporte.bloqueios` expõe consulta do bloqueio; não há model `Bloqueio` separado.

## 10.8 EntradaSemTicket

Walk-in na execução após a chamada; vinculada a `ExecucaoRota` e ao aluno (ou CPF). Regras de lote de CPF e coexistência com tickets estão em `ExecucaoRotaAggregate` (documento 04).

## 10.9 Permissões de transporte

`PermissaoFuncaoTransporte` e `PermissaoUsuarioTransporte` (1:1 com `Funcao` e `Usuario`) concedem `conferir` e `visualizar_relatorio_alunos`, combinadas por OR na compilação de permissões do módulo.

---

# 11. Pontos que podem evoluir depois

Os itens abaixo permanecem abertos ou fora do escopo atual:

- perfil `Estagiario` (não implementado em `PROJECT_APPS`)
- datas de início/fim em `SetorVinculo` (não existem no model atual; terceirizado já possui `data_inicio`/`data_fim`)
- histórico explícito de função em setor
- regras adicionais para aluno monitor
- **reservas** de infraestrutura (bloqueios futuros de recurso/sala)
- notificações automáticas além da sinalização UI de empréstimo atrasado

---

# 12. Resumo executivo

O núcleo do Cortex parte de `Usuario` como centro da identidade, e organiza o restante do sistema em torno de:

- estrutura organizacional (`Setor`, `Funcao`, `SetorVinculo`)
- perfis institucionais (`Servidor`, `Terceirizado`, `Cargo`, `EmpresaInstituicao`)
- perfis acadêmicos (`Aluno`, `Curso`, `AlunoCurso`)
- infraestrutura física (`Bloco`, `Sala`, `Recurso`, `Emprestimo`, `Autorizacao`, permissões do módulo)
- transporte universitário (`Percurso`, `Rota`, `DiaCalendarioTransporte`, `Motorista`, `ExecucaoRota`, `Ticket`,
  `EntradaSemTicket`, `Strike`, `Justificativa`, permissões de transporte)

As decisões mais importantes consolidadas neste ERD textual são:

- modularização por domínio;
- separação entre cargo e função;
- substituição de `SetorLotacao` por `SetorVinculo`;
- função obrigatória em todo vínculo com setor;
- monitoria tratada como função;
- responsabilidade de setor modelada por vínculo.
