# Diretrizes do Domínio: Transporte

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Transporte** do projeto Cortex (MeuIF-Transporte).

## Visão Geral do Domínio

O domínio `Transporte` gerencia o transporte universitário. A entrega atual cobre
percursos, rotas, o perfil e a visão operacional do motorista (RF013), execuções
datadas, reserva de tickets, fila de espera, embarque por QR Code, ausências,
strikes e justificativas.

### Modelos e Relacionamentos

- **Percurso**: trajeto nomeado do ônibus (`apelido` + `descricao`). Campo `ativo` no lugar de exclusão física.
- **Rota**: agendamento do ônibus em um percurso (`horario_saida`, `dia_semana`, `quantidade_vagas`). N:1 com `Percurso` (um percurso pode ter várias rotas em dias/horários diferentes). Cada rota exige exatamente um percurso, como no diagrama de classes.
- **Motorista**: perfil associado 1:1 a `Usuario`. O campo `usuario` também é a
  chave primária do perfil e usa `PROTECT`, impedindo a exclusão física do usuário
  enquanto o vínculo existir. O campo `ativo` controla a disponibilidade do perfil.
- **ExecucaoRota**: ocorrência datada de uma rota. Congela `data_hora_saida` e
  `quantidade_vagas` para não ser alterada por edições futuras na rota.
- **Ticket**: solicitação de um aluno em uma execução; representa reserva, posição
  em fila, cancelamento, embarque ou ausência.
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
  da execução e `tickets_solicitados`.
- `tickets_solicitados` conta tickets que ocupam vaga (`RESERVADO` e `EMBARCADO`),
  usando a mesma regra de ocupação da execução.
- Quando ainda não existe execução para a rota na data, os campos da execução são
  nulos, `tickets_solicitados` é zero e a capacidade exibida vem da rota.

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
A tela não oferece ação de iniciar ou finalizar rota, responsabilidade da operação
administrativa/conferência.

### 4. Execuções de rotas

- Criadas manualmente por L3 para uma rota e uma data.
- A data deve corresponder ao dia da semana da rota.
- Unicidade por `rota` + `data_execucao`: rotas distintas do mesmo percurso e dia,
  em horários diferentes, podem ter execuções normalmente.
- Estados: `ABERTA`, `FECHADA`, `EM_EMBARQUE`, `FINALIZADA`, `CANCELADA`.
- Reservas e entradas na fila exigem estado `ABERTA`.
- Para alunos, execuções disponíveis são exibidas somente de segunda a sexta,
  da meia-noite do próprio dia até exatamente 30 minutos antes da saída.
- QR Code só é validado em `EM_EMBARQUE`.

### 5. Tickets, capacidade e cancelamento

- Somente usuário e aluno ativos, com situação `MATRICULADO`, podem solicitar ticket.
- Três ou mais strikes ativos bloqueiam novas reservas e novas entradas em fila.
- O terceiro strike não cancela tickets nem posições já existentes.
- Há no máximo um ticket não cancelado por aluno e execução.
- Com vaga, a solicitação cria `RESERVADO`; sem vaga, a reserva falha e o aluno
  precisa entrar explicitamente na fila.
- Reserva, entrada na fila, cancelamento e saída da fila funcionam somente de
  segunda a sexta, entre a meia-noite do dia da execução e exatamente 30 minutos
  antes da saída. O instante exato do limite ainda é permitido; depois dele, todas
  essas ações são bloqueadas.
- Cancelar uma reserva promove o primeiro ticket da fila na mesma transação.
- A capacidade e a promoção usam bloqueio pessimista na execução para proteger a
  última vaga em requisições concorrentes.

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
O tipo de deficiência não é exposto nas respostas dos tickets.

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
  `is_bloqueado` e, quando aplicável, `quantidade_bloqueios` no aluno.
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
- Assinatura, execução e status são validados no banco; ticket cancelado, em fila,
  ausente ou adulterado é rejeitado.
- A primeira leitura muda o ticket para `EMBARCADO`; leituras posteriores são
  idempotentes e retornam `ja_validado=true`.

### 9. Permissões

Percursos e rotas continuam restritos a **L3** (`EDITAR_TUDO`). Execuções abertas
podem ser consultadas por qualquer autenticado; L3 vê e administra todas.
O aluno vê e altera apenas os próprios tickets, strikes e justificativas.

- **Views:** `IsAdminMixin` (`tem_acesso_elevado()`), o mesmo critério de L3: `is_staff`, `is_admin` ou superusuário.
- **Payload (login/me):** `gerenciar` é `true` só para L3; `motorista` exige conta
  de usuário e perfil Motorista ativos; `reservar` exige aluno ativo, matriculado
  e não bloqueado; `bloqueado`, `faltas` e `bloqueios` refletem o estado
  sincronizado do aluno (`bloqueios` = `quantidade_bloqueios`).
- **Compilação:** `UsuarioPermissions.permissoes_transporte()`.
- **Documentação viva da API:** `GET /cortex/identidade/permissoes/documentacao/` (`documentacao_transporte()`). Toda mudança de regra deve atualizar esse método no mesmo PR.

Swagger de cada endpoint de percursos e rotas declara `**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.`

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
- `POST` em `abrir-reservas/`, `fechar-reservas/`, `iniciar-embarque/`,
  `finalizar/` e `cancelar/`
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
