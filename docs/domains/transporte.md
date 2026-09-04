# Diretrizes do Domínio: Transporte

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Transporte** do projeto Cortex (MeuIF-Transporte).

## Visão Geral do Domínio

O domínio `Transporte` gerencia o transporte universitário. A entrega atual cobre
percursos, rotas, o perfil e a visão operacional do motorista (RF013), execuções
datadas, reserva de tickets, fila de espera, conferência de embarque, entrada sem
ticket, ausências, strikes e justificativas.

### Modelos e Relacionamentos

- **Percurso**: trajeto nomeado do ônibus (`apelido` + `descricao`). Campo `ativo` no lugar de exclusão física.
- **Rota**: agendamento do ônibus em um percurso (`horario_saida`, `dia_semana`, `quantidade_vagas`). N:1 com `Percurso` (um percurso pode ter várias rotas em dias/horários diferentes). Cada rota exige exatamente um percurso, como no diagrama de classes.
- **Motorista**: perfil associado 1:1 a `Usuario`. O campo `usuario` também é a
  chave primária do perfil e usa `PROTECT`, impedindo a exclusão física do usuário
  enquanto o vínculo existir. O campo `ativo` controla a disponibilidade do perfil.
- **ExecucaoRota**: ocorrência datada de uma rota. Congela `data_hora_saida` e
  `quantidade_vagas`. `chamada_tickets_concluida` e os timestamps
  `monitoramento_iniciado_em`, `chamada_concluida_em` e `embarcado_em` registram
  o andamento da conferência. `finalizada_em` fica para o fim da viagem
  (`EMBARCADO` → `INICIADA` → `FINALIZADA`).
- **Ticket**: solicitação de um aluno em uma execução; representa reserva, posição
  em fila, cancelamento, embarque, ausência ou não contemplado na espera (`NAO_CONTEMPLADO`).
- **EntradaSemTicket**: embarque manual por CPF nas vagas restantes após a chamada.
  Quem está `EM_ESPERA` e for informado no lote tem o ticket promovido para
  `EMBARCADO`. Quem não for informado permanece `EM_ESPERA` até o finalizar,
  quando vira `NAO_CONTEMPLADO`.
- **Strike**: falta vinculada unicamente a um ticket marcado como ausente.
- **Justificativa**: solicitação de revisão de bloqueio, cobrindo todos os strikes ativos do aluno.
- **Bloqueio**: estado do aluno (`is_bloqueado`, `faltas`, `quantidade_bloqueios`)
  sincronizado a partir dos strikes ativos; `faltas` são as ausências ativas no
  ciclo corrente e `quantidade_bloqueios` é o histórico de vezes em que o aluno
  entrou em bloqueio.

Não é possível desativar um percurso que ainda tenha rotas ativas. Não é possível vincular ou reativar rota em percurso inativo.

### Estrutura de Apps

```text
Transporte/
├── __init__.py
├── urls.py
├── percursos/       # App Django do model Percurso
├── rotas/           # App Django do model Rota
├── motoristas/      # App Django do perfil Motorista
├── execucoes_rotas/ # App Django do model ExecucaoRota
├── tickets/         # App Django do model Ticket e fila de espera
├── entradas_sem_ticket/
├── permissoes/
├── strikes/         # App Django do model Strike
├── justificativas/  # App Django do model Justificativa
└── bloqueios/       # Consulta de alunos bloqueados e envio de justificativa
```

## Regras Específicas do Domínio

### 1. Campos de Percurso

- `apelido`: identificador curto exibido na tela (ex.: "Rota R.SÃ"). Único, comparação case-insensitive.
- `descricao`: texto do trajeto (ex.: "IFPI – Posto R.Sã – FM – …").
- `ativo`: desativar/reativar no lugar de DELETE HTTP.

### 2. Campos de Rota

- `percurso`: FK obrigatória (`PROTECT`) para `Percurso` ativo.
- `horario_saida`: horário de partida no formato `hh:mm` (também aceita `hh:mm:ss` na entrada).
- `dia_semana`: `segunda`, `terca`, `quarta`, `quinta`, `sexta`, `sabado`, `domingo`.
- `quantidade_vagas`: inteiro ≥ 1.
- Unicidade: par `percurso` + `dia_semana` + `horario_saida` (vale também para rotas inativas; o mesmo slot só volta com reativar).
- `ativo`: desativar/reativar no lugar de DELETE HTTP.
- Listagem ordena por dia da semana (segunda → domingo), depois horário e apelido do percurso.

### 3. Perfil e visão das rotas do dia pelo motorista (RF013)

- Todos os motoristas ativos visualizam todas as rotas ativas programadas para o dia atual.
- A data atual usa o timezone `America/Fortaleza` configurado no projeto.
- Rotas são ordenadas pelo horário de saída e, em caso de empate, pelo apelido do percurso.
- A consulta é somente de leitura e não cria nem altera registros.
- A resposta combina os dados de rota e percurso com a execução da data, quando ela existe:
  `execucao_id`, `status_execucao`, `status_execucao_display`, capacidade congelada
  da execução, `tickets_solicitados`, `vagas_ocupadas` e `vagas_disponiveis`.
- `tickets_solicitados` conta tickets `RESERVADO` e `EMBARCADO` e não inclui
  `EntradaSemTicket`.
- `vagas_ocupadas` e `vagas_disponiveis` usam a mesma regra da conferência: antes
  da chamada de tickets, ocupação = `RESERVADO` + `EMBARCADO`; depois da chamada,
  ocupação = `EMBARCADO` + `EntradaSemTicket`. `EM_ESPERA` não ocupa vaga.
- Quando ainda não existe execução para a rota na data, os campos da execução são
  nulos, `tickets_solicitados` e `vagas_ocupadas` são zero e a capacidade exibida
  vem da rota.

#### Estados do perfil Motorista

- **Ativo**: com a conta de usuário também ativa, recebe a capacidade
  `transporte.motorista` e pode consultar as rotas do dia.
- **Inativo**: não recebe a capacidade e não pode acessar a consulta, mesmo que a
  conta de usuário esteja ativa.
- Conta de usuário inativa sempre bloqueia o acesso, independentemente do estado do
  perfil Motorista.

#### Apresentação no frontend

A tela do motorista usa os dados reais da execução e dos tickets retornados pela
API. O status visual é derivado assim:

- sem execução: `RESERVAS NÃO INICIADAS`;
- execução `ABERTA`: `RESERVAS EM ABERTO`;
- demais estados da execução: `RESERVAS FINALIZADAS`.

O indicador `Tickets solicitados` exibe `tickets_solicitados / quantidade_vagas`.
A ocupação física do ônibus, após a conferência, deve usar `vagas_ocupadas` /
`quantidade_vagas`.
Nesta entrega a tela do motorista é só leitura: não inicia nem finaliza a
**viagem** (`EMBARCADO` → `INICIADA` → `FINALIZADA`; `finalizada_em`). Essa
API ainda não existe. O conferente opera só a **conferência** (monitoramento
`EM_EMBARQUE` e encerramento em `EMBARCADO` com `embarcado_em`), não a viagem.

### 4. Execuções de rotas

- Criadas manualmente por L3 para uma rota e uma data.
- A data deve corresponder ao dia da semana da rota.
- Unicidade por `rota` + `data_execucao`: rotas distintas do mesmo percurso e dia,
  em horários diferentes, podem ter execuções normalmente.
- Estados: `ABERTA`, `FECHADA`, `EM_EMBARQUE`, `EMBARCADO`, `INICIADA`,
  `FINALIZADA`, `CANCELADA`. Inteiros: `FINALIZADA = 4`, `CANCELADA = 5`,
  `EMBARCADO = 6`, `INICIADA = 7` (sem remapeamento de valores antigos).
- Reservas e entradas na fila exigem estado `ABERTA`.
- Para alunos, execuções disponíveis são exibidas somente de segunda a sexta,
  da meia-noite do próprio dia até exatamente 30 minutos antes da saída.
- Conferente e L3 iniciam o monitoramento (`EM_EMBARQUE`) somente pelo
  `iniciar` da conferência, depois de 30 minutos antes da saída
  (`now > data_hora_saida − 30 min`), em execução `ABERTA` ou `FECHADA`.
  Abrir/fechar/cancelar reservas **não** transita para `EM_EMBARQUE`.
  No instante exato do T-30 o aluno ainda pode solicitar ticket; o
  monitoramento ainda não inicia. Depois do horário de saída, no mesmo dia,
  ainda é possível iniciar. Replay de iniciar só enquanto `EM_EMBARQUE`.
  Depois de `EMBARCADO` (conferência encerrada) não se inicia de novo; o
  campo `pode_monitorar` no payload indica se o botão de iniciar deve
  aparecer. O mesmo vale para `INICIADA` e `FINALIZADA`.
- A listagem da conferência no dia inclui `ABERTA`, `FECHADA`, `EM_EMBARQUE`,
  `EMBARCADO`, `INICIADA` e `FINALIZADA` (consulta; `pode_monitorar` falso
  após o início do monitoramento ou depois da conferência). `CANCELADA` não
  aparece. `EM_EMBARQUE` serve para continuar o monitoramento. L3 obedece a
  mesma data (hoje) e o mesmo T-30. Se existir execução no sábado ou domingo,
  ela entra nessa lista; o aluno continua sem reservar no fim de semana.
- Abrir conferência por ID no mesmo dia: `CANCELADA` responde como não
  encontrada (404). `EMBARCADO`, `INICIADA` e `FINALIZADA` permanecem no
  escopo para consulta da execução e replay de finalizar (sem alterar
  timestamps). Iniciar monitoramento nessas execuções retorna 400.
  Chamada de tickets e entrada por CPF só existem em `EM_EMBARQUE`; depois
  de `EMBARCADO` a lista basta. Outro dia continua 404.
- Depois de `EM_EMBARQUE`, L3 **não** cancela a execução: só finaliza a
  conferência (vai para `EMBARCADO`) ou deixa o monitoramento seguir.
- O conferente grava `embarcado_em` ao encerrar a conferência e **não**
  preenche `finalizada_em` (reservado ao fim da viagem do motorista:
  `EMBARCADO` → `INICIADA` → `FINALIZADA`, fora desta entrega de API).

### 5. Tickets, capacidade e cancelamento

- Somente usuário e aluno ativos, com situação `MATRICULADO`, podem solicitar
  ticket (reserva ou fila) ou entrar por CPF.
- Três ou mais strikes ativos bloqueiam novas reservas, novas entradas em fila
  e entrada sem ticket.
- O terceiro strike não cancela tickets nem posições já existentes.
- Há no máximo um ticket não cancelado por aluno e execução (`NAO_CONTEMPLADO`
  também ocupa essa unicidade; só `CANCELADO` libera o par aluno+execução).
- Com vaga, a solicitação cria `RESERVADO`; sem vaga, a reserva falha e o aluno
  precisa entrar explicitamente na fila.
- Reserva, entrada na fila, cancelamento e saída da fila funcionam somente de
  segunda a sexta, entre a meia-noite do dia da execução e exatamente 30 minutos
  antes da saída. O instante exato do limite ainda é permitido; depois dele, todas
  essas ações são bloqueadas.
- Cancelar uma reserva promove o primeiro ticket da fila na mesma transação.
- A capacidade e a promoção usam bloqueio pessimista na execução para proteger a
  última vaga em requisições concorrentes.
- Na conferência, quem não entra em `ausentes` na chamada fica `EMBARCADO` sem QR
  (presença por omissão). O conferente é responsável pela lista; o conferente não
  valida QR. A primeira chamada que conclui grava o conjunto; um segundo envio só
  é aceito se repetir o mesmo conjunto. Finalizar a execução marca a espera que
  não embarcou por CPF como `NAO_CONTEMPLADO`. Quem entra no lote de CPF permanece
  `EMBARCADO`. O replay da chamada compara o conjunto gravado nela, não ausências
  marcadas depois pelo L3. O monitoramento pode iniciar depois do horário de
  saída no mesmo dia, desde que `now > T-30`.
- Entrada por CPF revalida aluno ativo, matriculado, strikes, vaga, chamada
  concluída e execução em embarque. A consulta é `POST` em
  `entradas-sem-ticket/validar/` com `{ "cpf": "..." }` e não persiste (devolve
  dados do aluno para o card, inclusive `tem_deficiencia`). Depois do primeiro
  lote não vazio, `validar` devolve 400: o conjunto já foi concluído e a tela
  não mostra card que não dá para gravar. O `POST` em
  `entradas-sem-ticket/` recebe `{ "cpfs": [...] }`, revalida o lote e grava
  numa transação. Replay do mesmo conjunto devolve 200; conjunto diferente após
  o primeiro lote não vazio devolve 400. Lista vazia devolve 201 sem persistir e
  não conclui o lote. O lote é opcional: finalizar a execução sem enviá-lo
  marca a espera restante como `NAO_CONTEMPLADO`. Quem cancelou o próprio ticket
  pode usar este fluxo se houver vaga. Quem está `AUSENTE` nesta execução também pode: o ticket
  permanece `AUSENTE` e o strike não é desfeito. Quem está `EM_ESPERA` e entra
  no lote tem o ticket promovido para `EMBARCADO` (sem criar `EntradaSemTicket`).
  Três strikes ativos continuam impedindo a entrada (incluindo o strike desta
  ausência). `EM_ESPERA` não reserva vaga após a chamada.

### 6. Posição dos tickets e prioridade PcD

A posição é calculada dinamicamente e não é armazenada no ticket. Existem dois
grupos independentes: reservas confirmadas e fila de espera. A fila não é uma
entidade duplicada: corresponde aos tickets `EM_ESPERA`.

Ordem em cada grupo:

1. alunos cujo `Usuario.deficiencia` atual esteja preenchido;
2. demais alunos;
3. data/hora da reserva ou da entrada na fila dentro do respectivo grupo;
4. ID interno como desempate determinístico.

Para tickets de reserva (`RESERVADO`, `EMBARCADO` e `AUSENTE`), o total exibido é
a capacidade congelada da execução. Para `EM_ESPERA`, o total é a quantidade atual
de alunos aguardando. Alterar `Usuario.deficiencia` reposiciona dinamicamente os
tickets existentes nos dois grupos. A prioridade altera apenas a ordem exibida e
de atendimento: nunca remove uma reserva confirmada nem promove alguém sem vaga.
O tipo de deficiência não é exposto nas respostas dos tickets. Na listagem da
conferência (`GET .../conferencia/reservas/`) e no `validar` de CPF,
`aluno.tem_deficiencia` indica só se o cadastro tem deficiência preenchida, para
o selo no monitoramento.

O payload `posicao` informa `tipo` (`RESERVA` ou `ESPERA`), `atual` e `total`.
`posicao_fila` permanece como campo compatível e só contém valor para `EM_ESPERA`.

### 7. Ausências, strikes, bloqueios e justificativas

- Cada ausência registrada (ticket `AUSENTE`) gera exatamente um strike e incrementa
  `faltas` (strikes ativos no ciclo atual).
- Com 1 ou 2 faltas ativas o aluno **não** está bloqueado; na 3ª falta ativa
  (`is_bloqueado=true`) o aluno deixa de reservar tickets e entrar em fila.
- `quantidade_bloqueios` incrementa **somente** na transição para bloqueado
  (de `is_bloqueado=false` para `true`); novas faltas no mesmo ciclo (4ª, 5ª…)
  não incrementam o histórico. Após aprovação da justificativa, `faltas` zera e
  `quantidade_bloqueios` permanece.
- L3 marca um ticket `RESERVADO` como `AUSENTE` durante o embarque ou após a
  finalização; a ação cria exatamente um strike e sincroniza `faltas`,
  `is_bloqueado` e, quando aplicável, `quantidade_bloqueios` no aluno. O conferente
  faz o mesmo em lote ao finalizar a chamada (`ausentes`).
- Strike `ATIVO` conta para o bloqueio; `JUSTIFICADO` deixa de contar.
- O aluno bloqueado pode enviar **uma** justificativa cobrindo todos os strikes
  ativos (`POST /bloqueios/justificativas/`).
- L3 lista bloqueios, consulta o detalhe e aprova ou rejeita justificativas
  pendentes (`POST /justificativas/<pk>/aprovar/` ou `/rejeitar/`).
- Aprovar marca todos os strikes cobertos como `JUSTIFICADO` e ressincroniza o
  bloqueio do aluno.

#### Payload do detalhe (modal TI)

`GET /bloqueios/<aluno_pk>/` e `GET /justificativas/<pk>/` expõem, entre outros:

| Campo | Significado |
|-------|-------------|
| `ausencias` / `faltas` | Strikes ativos no ciclo atual |
| `bloqueios` | `quantidade_bloqueios` (histórico de bloqueios) |
| `deficiencia`, `ultimo_login` | Dados do `Usuario` vinculado |
| `justificativa_pendente.itens_ausencia[]` | Lista por ausência: `envio`, `data_ausencia`, `horario`, `justificativa` |
| `justificativa_pendente.strikes_cobertos` | Mantido para compatibilidade com clientes legados |

Cada item de `itens_ausencia` repete o texto único da justificativa e traz a data
e o horário da execução em que a ausência ocorreu.

### 8. QR Code

- O backend emite em `codigo_qr` um conteúdo opaco assinado, com UUID público do
  ticket e execução. CPF, deficiência e IDs internos não são embutidos.
- O frontend transforma esse conteúdo em imagem e pode incluí-lo no PDF.
- L3 envia o conteúdo lido a `POST /cortex/transporte/tickets/validar-qr/`.
  O conferente **não** valida QR.
- Assinatura, execução e status são validados no banco; ticket cancelado, em fila,
  ausente ou adulterado é rejeitado.
- A primeira leitura muda o ticket para `EMBARCADO`; leituras posteriores são
  idempotentes e retornam `ja_validado=true`.

### 9. Permissões

Percursos e rotas continuam restritos a **L3** (`gerenciar`). L2 (`LER_TUDO`) não
abre o módulo de Transporte. O aluno vê e altera apenas os próprios tickets,
strikes e justificativas.

- **Payload (login/me):** `gerenciar` é `true` só para L3; `motorista` exige conta
  de usuário e perfil Motorista ativos; `reservar` exige aluno ativo, matriculado
  e não bloqueado; `conferir` é `true` para L3 **ou** servidor/terceirizado ativo
  **e** (`PermissaoFuncaoTransporte.conferir` na função do vínculo ativo **ou**
  `PermissaoUsuarioTransporte.conferir`); `bloqueado`, `faltas` e `bloqueios`
  refletem o estado sincronizado do aluno (`bloqueios` = `quantidade_bloqueios`).
- **Conferente:** lista só execuções do **dia**; após iniciar a conferência, opera
  a chamada de tickets e a entrada por CPF **dessa** execução. Não acessa GET
  global de tickets.
- **Views de conferência:** `PodeConferirTransporteMixin`.
- **Views administrativas:** `IsAdminMixin` (`tem_acesso_elevado()`), o mesmo critério de L3.
- **Compilação:** `UsuarioPermissions.permissoes_transporte()`.
- **Documentação viva:** `documentacao_transporte()`. O dashboard futuro (RF012)
  reutiliza `conferir`; não há capacidade `ver_dashboard`.

Swagger das views de conferência declara capacidade `transporte.conferir` e o
escopo do dia, da chamada de tickets e da entrada por CPF da execução monitorada.

#### Visualização (motorista)

- `user.permissoes.transporte.motorista` é `true` somente para usuário e perfil Motorista ativos.
- L3/TI não recebe a capacidade operacional automaticamente.
- O endpoint de leitura usa o `IsAuthenticatedMixin` padrão do `AppCore`; a camada
  `Business` valida que o usuário possui perfil Motorista ativo.

### 10. Endpoints

Base percursos: `/cortex/transporte/percursos/`

- `GET` / `POST` na raiz
- `GET` / `PATCH` em `<pk>/`
- `POST` `<pk>/desativar/` e `<pk>/reativar/`
- Listagem: `?ativo=true|false`, `?busca=` (apelido ou descrição), paginação `?paginacao=`

Base rotas: `/cortex/transporte/rotas/`

- `GET` / `POST` na raiz
- `GET` / `PATCH` em `<pk>/`
- `POST` `<pk>/desativar/` e `<pk>/reativar/`
- Listagem: `?ativo=`, `?percurso_id=`, `?dia_semana=`, `?busca=` (apelido do percurso), `?paginacao=`

Base motorista: `/cortex/transporte/motorista/`

- `GET rotas-do-dia/` — lista completa, sem paginação, restrita a motoristas ativos

Base execuções: `/cortex/transporte/execucoes-rotas/`

- `GET` / `POST` na raiz
- `GET` em `<pk>/`
- `POST` em `abrir-reservas/`, `fechar-reservas/` e `cancelar/` (L3;
  cancelar só antes de `EM_EMBARQUE`)
- `GET` `execucoes-rotas/conferencia/`
- `POST` `execucoes-rotas/<pk>/conferencia/iniciar/` e `.../conferencia/finalizar/`
  (capacidade `conferir`)
- `GET` `execucoes-rotas/<pk>/conferencia/reservas/`
  (`aluno.tem_deficiencia`: selo PcD sem o tipo clínico)
- `POST` `execucoes-rotas/<pk>/conferencia/finalizar-chamada/`
- `POST` `execucoes-rotas/<pk>/conferencia/entradas-sem-ticket/validar/`
  (`cpf` no body; sem persistência; devolve o card; 400 se o lote já foi concluído)
- `POST` `execucoes-rotas/<pk>/conferencia/entradas-sem-ticket/`
  (`{ "cpfs": [...] }`; persiste o lote; replay do mesmo conjunto = 200; lote opcional)
- `POST` em `<pk>/reservar/` e `<pk>/fila-espera/entrar/`

Base tickets: `/cortex/transporte/tickets/`

- `GET` na raiz e em `<uuid>/`
- `POST` em `<uuid>/cancelar/`, `<uuid>/sair-fila/` e
  `<uuid>/marcar-ausente/`
- `POST` em `validar-qr/`

Bases auxiliares:

- `GET /cortex/transporte/strikes/`
- `GET /cortex/transporte/bloqueios/` — listagem paginada de alunos bloqueados
  - Query params: `busca` (nome ou CPF), `curso_id` (vínculo ativo), `tem_justificativa` (`true`|`false`), `paginacao`
  - Campos por item: `aluno_pk`, `nome`, `cpf`, `faltas` (compat.), `ausencias`,
    `bloqueios`, `is_bloqueado`, `tem_justificativa_pendente`, `curso_nome`,
    `data_bloqueio`
- `GET /cortex/transporte/bloqueios/<aluno_pk>/` — detalhe com `deficiencia`,
  `ultimo_login`, `ausencias`, `bloqueios` e `justificativa_pendente` (com
  `itens_ausencia` e `strikes_cobertos` para compatibilidade)
- `POST /cortex/transporte/bloqueios/justificativas/`
- `GET /cortex/transporte/justificativas/` e
  `GET /cortex/transporte/justificativas/<pk>/` (detalhe inclui `itens_ausencia`)
- `POST /cortex/transporte/justificativas/<pk>/aprovar/`
- `POST /cortex/transporte/justificativas/<pk>/rejeitar/`
