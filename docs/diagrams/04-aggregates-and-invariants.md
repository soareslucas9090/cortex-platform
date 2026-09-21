# Aggregates and Invariants do Cortex

## Objetivo

Este documento define os agregados do Cortex e suas invariantes principais.

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

## Visão geral dos agregados

Os agregados identificados no Cortex, alinhados aos seis contextos do ERD (documento 03), são:

| # | Agregado | Raiz | Contexto |
|---|----------|------|----------|
| 1 | `UsuarioAggregate` | `Usuario` | Identidade |
| 2 | `SetorAggregate` | `Setor` | Organizacional |
| 3 | `ServidorAggregate` | `Servidor` | PessoasInstitucionais |
| 4 | `TerceirizadoAggregate` | `Terceirizado` | PessoasInstitucionais |
| 5 | `AlunoAggregate` | `Aluno` | Academico |
| 6 | `CursoAggregate` | `Curso` | Academico |
| 7 | `RotaAggregate` | `Rota` | Transporte |
| 8 | `ExecucaoRotaAggregate` | `ExecucaoRota` | Transporte |
| 9 | `EspacoFisicoAggregate` | `Bloco` / `Sala` | Infraestrutura |
| 10 | `RecursoAggregate` | `Recurso` | Infraestrutura |
| 11 | `AutorizacaoAggregate` | `Autorizacao` | Infraestrutura |
| 12 | `EmprestimoAggregate` | `Emprestimo` | Infraestrutura |
| 13 | `PermissaoInfraestruturaAggregate` | (compilação) | Infraestrutura |
| 14 | `CalendarioTransporteAggregate` | `DiaCalendarioTransporte` | Transporte |

`ImportacaoLote` aparece em dois apps (`Identidade.usuarios` e `Infraestrutura.importacoes`) com a mesma invariante de lote único `EM_ANDAMENTO`; pode ser tratado como sub-agregado operacional de cada contexto, não como raiz transversal.

Objetos sem tabela própria (`RelatorioAlunos`, API `Transporte.bloqueios`) orbitam os agregados acima sem formar raiz separada.

---

# 1. UsuarioAggregate

## Aggregate Root

`Usuario`

## Entidades relacionadas

- `Usuario`
- `Contato`
- `Endereco`
- `ImportacaoLote` (app `Identidade.usuarios`)

## Responsabilidade

Representa a identidade central da pessoa no sistema, reunindo os dados cadastrais e relacionamentos básicos que orbitam o usuário.

## Motivo para ser agregado

As informações de identidade tendem a mudar em conjunto e dependem semanticamente do usuário como entidade central.

## Invariantes

1. Todo `Contato` deve pertencer a um `Usuario` (FK N:1).
2. Todo `Endereco` deve pertencer a um `Usuario` (`OneToOne`).
3. Quando informado, `cpf` deve ser único; o campo é opcional no model.
4. Quando informado, `email` deve ser único; o campo é opcional no model.
5. O login na API aceita e-mail, CPF ou matrícula ativa; `USERNAME_FIELD` permanece `cpf` para o admin Django.
6. `usuario_coletivo` só pode manter pools M2M (`empresas_coletivo`, `cargos_coletivo`, `funcoes_coletivo`, `setores_coletivo`) em contas marcadas como coletivas; conta coletiva não participa como solicitante/responsável de empréstimo.
7. No máximo um `ImportacaoLote` de usuários com status `EM_ANDAMENTO` (constraint `usuarios_importacao_lote_unico_em_andamento`).
8. Perfis institucionais e acadêmicos não devem duplicar dados centrais de identidade.

## Regras operacionais

- criação de usuário deve garantir unicidade de `cpf` e `email` quando informados;
- atualização de dados cadastrais deve ocorrer a partir do agregado de usuário;
- contatos e endereço devem ser manipulados preservando o vínculo com o usuário.

## Onde as regras devem morar

- validações: `Identidade/usuarios/rules.py`, `Identidade/contatos/business.py`, `Identidade/enderecos/` (model sem `rules.py` dedicado)
- orquestração: `Identidade/usuarios/business.py`; importação em lote conforme fluxo do app `usuarios`

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
9. Se `Funcao.exige_aluno` for verdadeiro, o usuário do vínculo deve ser `Aluno` ativo (`SetorVinculoRules.usuario_e_aluno_se_exigido`).
10. `Funcao.categoria` classifica o papel no catálogo; alterações seguem `Organizacional/funcoes/rules.py` (unicidade de `papel_funcao`, desativação sem vínculos).
11. Um mesmo usuário pode possuir múltiplos vínculos com setores distintos.
12. `Funcao` deve possuir o atributo `e_gratificada`.

## Regras operacionais

- criação de vínculo com setor exige função obrigatória;
- definição do responsável do setor deve validar se o usuário é servidor;
- troca de responsável deve preservar a existência contínua de um responsável válido;
- remoção do único responsável de um setor não pode ser permitida sem substituição adequada;
- alunos monitores devem ser representados como usuários vinculados a setor com função correspondente.

## Onde as regras devem morar

- invariantes teóricas: `Organizacional/setores/rules.py` e `Organizacional/vinculos/rules.py`
- criação, troca e atualização de vínculos: `Organizacional/vinculos/business.py`

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
3. `Cargo` é obrigatório para `Servidor` e opcional para `Terceirizado`.
4. Um `Cargo` pode estar associado a múltiplos servidores e terceirizados.
5. Apenas servidores podem ocupar a responsabilidade principal de um setor.
6. Quando informada, `matricula` deve ser única no sistema (validação cruzada com `AlunoCurso` e `Terceirizado`).

## Regras operacionais

- criação de servidor exige usuário base existente;
- criação de servidor exige cargo válido;
- um usuário não deve ter múltiplos perfis redundantes de servidor;
- validações sobre elegibilidade de responsabilidade de setor podem consultar este agregado.

## Onde as regras devem morar

- regras específicas do perfil de servidor: `PessoasInstitucionais/servidores/rules.py`
- orquestração de criação/atualização: `PessoasInstitucionais/servidores/business.py`

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
4. `Cargo` em terceirizado é opcional; quando informado, deve estar ativo (`TerceirizadoRules.cargo_ativo`).
5. Quando informada, `matricula` deve ser única no sistema (validação cruzada com `AlunoCurso` e `Servidor`).

## Regras operacionais

- criação de terceirizado exige usuário base;
- criação de terceirizado exige empresa válida;
- regras futuras de escopo e permissões podem partir desse perfil.

## Onde as regras devem morar

- validações de vínculo terceirizado-empresa: `PessoasInstitucionais/terceirizados/rules.py`
- orquestração operacional: `PessoasInstitucionais/terceirizados/business.py`

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
6. `faltas`, `is_bloqueado` e `quantidade_bloqueios` são o estado de bloqueio do transporte no próprio `Aluno` (não há entidade `Bloqueio`); strikes e justificativas ressincronizam `faltas`/`is_bloqueado`.
7. Quando informada em `AlunoCurso`, `matricula` deve ser única no sistema (validação cruzada com `Servidor` e `Terceirizado`).

## Regras operacionais

- criação de aluno exige usuário base;
- vinculação do aluno a curso deve ocorrer por `AlunoCurso`;
- histórico acadêmico deve ser preservado via entidade de vínculo, evitando sobrecarga do model `Aluno`.

## Onde as regras devem morar

- validações acadêmicas: `Academico/alunos/rules.py`
- criação de vínculo aluno-curso: `Academico/alunos/business.py`

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

- regras do curso: `Academico/cursos/rules.py`
- operações de manutenção do curso: `Academico/cursos/business.py`

---

# 7. RotaAggregate

## Aggregate Root

`Rota`

## Entidades relacionadas

- `Rota`
- `Percurso` (agregado pai do trajeto; toda rota referencia exatamente um percurso)

## Dependências conceituais externas

- `Motorista`
- `Usuario`
- `ExecucaoRota`

## Responsabilidade

Representa a programação recorrente de um ônibus em determinado percurso, dia da
semana e horário. Também fornece a visão somente de leitura das rotas programadas
para a data local, enriquecida com a execução correspondente.

## Invariantes

1. Toda `Rota` deve estar associada a exatamente um `Percurso`.
2. A visão do motorista só contém rotas e percursos ativos.
3. A rota deve estar programada para o dia da semana correspondente à data local.
4. Todos os motoristas ativos visualizam o mesmo conjunto completo de rotas do dia.
5. Usuário ou perfil Motorista inativo não pode acessar a visão.
6. A consulta não cria nem altera registros.
7. A ordenação é por horário de saída e, em caso de empate, pelo apelido do percurso.
8. Cada usuário possui no máximo um perfil Motorista, pois o vínculo é `OneToOne`.
9. Um usuário vinculado a Motorista não pode ser excluído fisicamente (`PROTECT`).
10. Quando existe execução na data, status, capacidade e ocupação vêm dela; sem
    execução, os campos operacionais são nulos/zero e a capacidade vem da rota.
11. `tickets_solicitados` conta apenas tickets `RESERVADO` e `EMBARCADO`.
    `vagas_ocupadas` segue a regra da conferência: antes da chamada,
    `RESERVADO` + `EMBARCADO`; depois da chamada, `EMBARCADO` + `EntradaSemTicket`.
    `EM_ESPERA` e `CONTEMPLADO` não ocupam vaga (o walk-in da espera conta só na
    `EntradaSemTicket`).

## Onde as regras devem morar

- autorização do perfil Motorista e definição da data: `Transporte/rotas/business.py`;
- consultas e ordenação: `Transporte/rotas/helpers.py`;
- identificação do perfil ativo: `Transporte/motoristas/helpers.py`;
- contrato de resposta: `Transporte/rotas/serializers.py`.

---

# 8. ExecucaoRotaAggregate

### Aggregate Root

`ExecucaoRota`

### Entidades relacionadas

- `ExecucaoRota`
- `Ticket`
- `EntradaSemTicket`
- `Strike`
- `Justificativa`

### Invariantes

1. Uma rota possui no máximo uma execução por data; outras rotas e horários são permitidos.
2. Vagas e horário são congelados na execução.
3. Um aluno possui no máximo um ticket não cancelado por execução.
4. Reserva e promoção nunca podem ultrapassar a quantidade de vagas.
5. Reserva, fila, cancelamento e saída da fila só ocorrem em data operacional,
   entre 19h do dia anterior e o limite inclusivo de 30 minutos antes da saída.
6. Reservas ocupam a menor posição disponível. A fila e a promoção seguem FIFO,
   sem prioridade PcD; PcD aparece primeiro apenas na listagem do conferente.
7. Cancelamento de reserva e promoção acontecem na mesma transação. O primeiro da
   fila herda exatamente a posição cancelada; sem fila, a próxima reserva direta
   ocupa a menor posição livre. O cancelado conserva a posição só para auditoria.
8. Cada ticket ausente gera no máximo um strike.
9. Três strikes ativos bloqueiam novas reservas e entradas em fila;
    não cancelam tickets nem posições já existentes. Entrada sem ticket (walk-in)
    permanece permitida.
10. QR Code só embarca ticket reservado em execução no estado de embarque.
11. A aprovação da justificativa e a retirada do strike da contagem são atômicas.
12. O conferente inicia o monitoramento somente se `now > T-30` e somente pelo
    `iniciar` da conferência (abrir/fechar/cancelar não vai para `EM_EMBARQUE`);
    o aluno ainda solicita no instante igual a T-30. Depois de `EMBARCADO` o
    monitoramento não reinicia (replay de iniciar só em `EM_EMBARQUE`).
    A chamada é incremental (1ª e 2ª com POSTs por ticket e fechamento explícito);
    strikes de ausência na conferência só ao finalizar (`AUSENTE` remanescente).
    Vários conferentes podem marcar; a última escrita prevalece por ticket.
13. Ao finalizar a conferência (`EMBARCADO`), a espera que não entrou por CPF
    permanece `EM_ESPERA` — desfecho nessa execução. Grava-se `embarcado_em`,
    `conferencia_finalizada_por` e `entradas_cpf_concluidas`; `finalizada_em`
    fica para o fim da viagem (`INICIADA` → `FINALIZADA`). Replay não troca
    conferente nem timestamps. Finalizar sem CPF ainda aplica strikes pendentes.
14. Entrada sem ticket é um CPF por vez após `chamada_tickets_concluida`, sem
    bloqueio por lotação. `EM_ESPERA` → `CONTEMPLADO` + `EntradaSemTicket`;
    `AUSENTE` → `EMBARCADO` sem entrada nem strike imediato. Replay do mesmo CPF
    é 200. Fora da fase CPF, `validar` e registro retornam 400. Três strikes
    ativos não bloqueiam walk-in. Relatório: ausente que embarcou via CPF conta
    só como presente.
15. Depois de `EM_EMBARQUE` a execução não pode ser cancelada; só finaliza a conferência (`EMBARCADO`).
16. Conferência por ID no dia: `CANCELADA` não existe nesse escopo;
    `EMBARCADO`, `INICIADA` e `FINALIZADA` permanecem para consulta da execução
    e replay de finalizar, não de iniciar. Chamada de tickets e CPF só em `EM_EMBARQUE`.
    A lista do dia mostra esses estados e omite `CANCELADA`.

### Fronteira transacional

`ExecucaoRota` é bloqueada durante reserva e cancelamento com promoção. Tickets,
strikes e justificativas são bloqueados nas respectivas mudanças de estado.

### Relação com a visão do motorista

O status, a capacidade congelada e a ocupação desta execução alimentam a visão
diária do motorista. `tickets_solicitados` permanece `RESERVADO` + `EMBARCADO`;
depois da chamada, `vagas_ocupadas` soma `EMBARCADO` e `EntradaSemTicket`.
A consulta do motorista não inicia nem finaliza a viagem. Os POSTs de operação
do motorista fazem `EMBARCADO` → `INICIADA` → `FINALIZADA`, registrando início,
responsável e fim. O fim grava `finalizada_em` e `rota_finalizada_em` com o mesmo
horário. O conferente encerra só a conferência (`EMBARCADO` / `embarcado_em`).

Bloqueio para novas reservas/fila deriva de `Aluno.is_bloqueado` (três strikes ativos); `Transporte.bloqueios` apenas expõe esse estado — não é agregado separado.

### Onde as regras devem morar

- geração automática e calendário: `Transporte/execucoes_rotas/business.py`, `Transporte/calendario_operacional/rules.py`
- tickets, strikes, entradas sem ticket, justificativas: respectivos `rules.py` / `business.py` em `Transporte/tickets`, `strikes`, `entradas_sem_ticket`, `justificativas`, `execucoes_rotas`
- permissões: `Transporte/permissoes/rules.py` e compilação em helpers de acesso

---

# 9. EspacoFisicoAggregate

## Aggregate Root

`Bloco` (com `Sala` e `SalaSetor` no mesmo agrupamento operacional)

## Entidades relacionadas

- `Bloco`
- `Sala`
- `SalaSetor` (liga `Sala` a `Setor` do domínio organizacional)

## Invariantes

1. `Sala` pertence a um `Bloco` ativo para cadastro operacional; unicidade `bloco` + `nome`.
2. `SalaSetor` é único por par `sala` + `setor`.
3. Desativação de bloco/sala segue `Infraestrutura/blocos/rules.py` e `Infraestrutura/salas/rules.py` (sem vínculos/recursos que impeçam a operação).

## Onde as regras devem morar

- `Infraestrutura/blocos/rules.py`, `Infraestrutura/blocos/business.py`
- `Infraestrutura/salas/rules.py`, `Infraestrutura/salas/business.py`

---

# 10. RecursoAggregate

## Aggregate Root

`Recurso`

## Invariantes

1. `codigo` único na instância.
2. Tipo `chave` exige `sala` ativa; `midia` e `material_didatico` aceitam `sala` opcional (`RecursoRules.validar_sala_por_tipo`).
3. Recurso inativo ou `em_avaria` não pode ser emprestado.
4. Não desativar recurso com item de empréstimo aberto.
5. Estado derivado para UI: avaria → emprestado → reservado → disponível.

## Onde as regras devem morar

- `Infraestrutura/recursos/rules.py`, `Infraestrutura/recursos/business.py`

---

# 11. AutorizacaoAggregate

## Aggregate Root

`Autorizacao`

## Invariantes

1. Alvo XOR: exatamente um de `sala` ou `recurso` (`AutorizacaoRules.validar_alvo_xor`).
2. `data_fim` ≥ `data_inicio` quando informada; `data_fim` nula = permanente.
3. Concessão e revogação exigem capacidade `autorizar` no concedente/revogador.
4. Autorização por sala cobre todos os recursos da sala em runtime, inclusive futuros.
5. Elegibilidade de retirada consulta autorizações vigentes junto às regras automáticas de perfil (`Emprestimo` helper).

## Onde as regras devem morar

- `Infraestrutura/autorizacoes/rules.py`, `Infraestrutura/autorizacoes/business.py`

---

# 12. EmprestimoAggregate

## Aggregate Root

`Emprestimo`

## Entidades relacionadas

- `Emprestimo`
- `ItemEmprestimo`

## Invariantes

1. `solicitante` ativo, não coletivo; `responsavel` resolvido conforme conta (coletiva exige pool elegível).
2. Cada `ItemEmprestimo` referencia recurso disponível (ativo, sem avaria, sem outro item aberto no mesmo recurso).
3. Solicitante deve ser elegível por perfil, `SalaSetor`, `Autorizacao` ou `retirada_irrestrita` (`EmprestimoRules.validar_elegibilidade_solicitante_para_recurso`).
4. Devolução parcial permitida; empréstimo encerra quando todos os itens têm `devolvido_em`.
5. Troca de titular exige itens em aberto e reabre empréstimo sem vínculo com o anterior.

## Onde as regras devem morar

- `Infraestrutura/emprestimos/rules.py`, `Infraestrutura/emprestimos/business.py`
- elegibilidade e estado emprestado: `Infraestrutura/emprestimos/helpers.py`

---

# 13. PermissaoInfraestruturaAggregate

## Aggregate Root

Compilação lógica (sem entidade única): união **OR** de `PermissaoFuncaoInfraestrutura` (via vínculos ativos do usuário) e `PermissaoUsuarioInfraestrutura`.

## Invariantes

1. Cada `Funcao` e cada `Usuario` possuem no máximo um registro de permissão 1:1.
2. Capacidades `operar`, `cadastrar`, `autorizar`, `retirada_irrestrita` são independentes e cumulativas por OR entre fontes.
3. Operações de empréstimo exigem `operar`; cadastro estrutural exige `cadastrar`.

## Onde as regras devem morar

- `Infraestrutura/permissoes/rules.py`, `Infraestrutura/permissoes/access.py` (`permissoes_infraestrutura()`)
- importação em lote: `Infraestrutura/importacoes/rules.py`, constraint de lote único `EM_ANDAMENTO` no model

---

# 14. CalendarioTransporteAggregate

## Aggregate Root

`DiaCalendarioTransporte`

## Responsabilidade

Define exceções operacionais por data (`tipo`, `ativo`) usadas na geração automática de `ExecucaoRota`.

## Invariantes

1. `data` única no calendário.
2. `DiaCalendarioTransporteRules.permite_operacao_na_data` combina dia da semana com tipos operacionais do calendário.
3. Task Celery Beat `gerar_execucoes_rotas_automaticas_task` (agendamento `*/5` minutos em `Cortex/settings.py`) materializa execuções idempotentes para rotas elegíveis na data.

## Onde as regras devem morar

- `Transporte/calendario_operacional/rules.py`, `Transporte/calendario_operacional/business.py`
- geração: `Transporte/execucoes_rotas/business.py` (`gerar_execucoes_automaticas`), `Transporte/execucoes_rotas/tasks.py`

---

# Invariantes transversais

As regras abaixo atravessam mais de um agregado e precisam ser tratadas com cuidado na camada de negócio.

## 1. Todo perfil parte de um usuário

Perfis como `Servidor`, `Terceirizado`, `Aluno` e `Motorista` dependem da existência prévia de `Usuario`.

## 2. Responsável de setor deve ser servidor

Embora a regra afete diretamente `SetorAggregate`, ela depende da existência consistente de `ServidorAggregate`.

## 3. Aluno monitor depende de vínculo organizacional

A condição de monitor não nasce no agregado acadêmico, mas sim no organizacional.

## 4. Cargo e função não podem ser confundidos

- `Cargo` pertence ao contexto institucional do servidor
- `Funcao` pertence ao contexto organizacional do vínculo com setor

---

# Fronteiras recomendadas para a camada de business

## `Identidade/usuarios/business.py` (e respectivos apps)

Deve orquestrar:

- criação de usuário;
- atualização cadastral;
- manutenção de contatos (em `Identidade/contatos/business.py`) e endereços (em `Identidade/enderecos/business.py`).
- matrícula: `normalizar_matricula` em `AppCore/common/util/util.py`; busca, elegibilidade e unicidade global em `Usuario().helper` / `Usuario().rules`.

## `Organizacional/vinculos/business.py` e `Organizacional/setores/business.py`

Deve orquestrar:

- criação de setor (em `Organizacional/setores/business.py`);
- criação e atualização de vínculos (em `Organizacional/vinculos/business.py`);
- definição de responsável (em `Organizacional/vinculos/business.py`);
- validação de função obrigatória;
- operações relacionadas à monitoria como função.

## `PessoasInstitucionais/servidores/business.py` e `PessoasInstitucionais/terceirizados/business.py`

Deve orquestrar:

- criação de servidor (em `PessoasInstitucionais/servidores/business.py`);
- criação de terceirizado (em `PessoasInstitucionais/terceirizados/business.py`);
- associação de cargo (em `PessoasInstitucionais/servidores/business.py`);
- associação de empresa (em `PessoasInstitucionais/terceirizados/business.py`).

## `Academico/alunos/business.py` e `Academico/cursos/business.py`

Deve orquestrar:

- criação de aluno (em `Academico/alunos/business.py`);
- criação de curso (em `Academico/cursos/business.py`);
- vínculo entre aluno e curso.

## `Transporte/rotas/business.py` e apps operacionais de Transporte

Deve orquestrar:

- autorização e consulta das rotas do dia para motoristas ativos;
- associação da execução correspondente e cálculo da ocupação real;
- geração automática de execuções (calendário + Celery Beat);
- mudanças de estado das execuções;
- reserva, fila, cancelamento, embarque e ausência;
- strikes, justificativas e entradas sem ticket;
- permissões de conferência e relatório (`Transporte/permissoes/`).

## Apps de `Infraestrutura/`

Deve orquestrar:

- cadastro de blocos, salas, vínculos sala–setor e recursos;
- concessão/revogação de autorizações;
- retirada, devolução parcial e troca de titular de empréstimos;
- compilação de permissões do módulo;
- importação em lote de estrutura/recursos (`Infraestrutura/importacoes/business.py`).

---

# Regras que não devem ir para as views

As seguintes validações não devem ser implementadas diretamente nas views:

- verificação de existência de responsável válido para setor;
- verificação de que responsável é servidor;
- validação de que vínculo com setor possui função;
- validação de exclusividade ou coerência de perfis;
- verificação de consistência entre aluno monitor e vínculo organizacional;
- verificação de unicidade semântica de `cpf` e `email`;
- elegibilidade de retirada de recurso e XOR de autorização;
- resolução de responsável em conta coletiva.

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

## No domínio Transporte

- consultar rotas do dia sem criar efeitos colaterais;
- gerar execuções pelo calendário sem duplicar `rota` + `data_execucao`;
- reservar a última vaga sob concorrência;
- cancelar uma reserva e promover a fila na mesma transação;
- validar QR Code e registrar embarque de forma idempotente;
- registrar ausência, strike e decisão de justificativa de modo consistente;
- entrada sem ticket e lote de CPF após a chamada.

## No domínio Infraestrutura

- retirada com vários recursos e devolução parcial;
- impedir segundo empréstimo aberto no mesmo recurso;
- validar elegibilidade automática (servidor, terceirizado/chave, sala–setor);
- revogar autorização e trocar titular com transação consistente.

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
- restrições mais detalhadas de situação acadêmica;
- regras específicas para múltiplos vínculos simultâneos no mesmo setor;
- perfil `Estagiario` e reservas de infraestrutura (fora da v1).

---

# Resumo executivo

Os agregados do Cortex foram definidos em torno de seis contextos:

- identidade da pessoa;
- estrutura organizacional;
- perfis institucionais;
- perfis acadêmicos;
- infraestrutura física e empréstimos;
- transporte universitário e sua operação diária (incluindo calendário e geração automática de execuções).

A principal consequência prática desta definição é:

- regras de consistência devem ser pensadas por agregado;
- invariantes devem ser respeitadas fora das views;
- `Setor` e seus vínculos formam um dos núcleos mais sensíveis do sistema;
- `Cargo` e `Funcao` são conceitos distintos e pertencem a agregados/contextos diferentes;
- monitoria deve ser tratada no domínio organizacional, nunca como atalho em model acadêmico.
