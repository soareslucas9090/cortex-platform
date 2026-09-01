# Diretrizes do Domínio: Transporte

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Transporte** do projeto Cortex (MeuIF-Transporte).

## Visão Geral do Domínio

O domínio `Transporte` gerencia o transporte universitário. A entrega atual cobre
percursos, rotas, execuções datadas, reserva de tickets, fila de espera, embarque
por QR Code, ausências, strikes e justificativas.

### Modelos e Relacionamentos

- **Percurso**: trajeto nomeado do ônibus (`apelido` + `descricao`). Campo `ativo` no lugar de exclusão física.
- **Rota**: agendamento do ônibus em um percurso (`horario_saida`, `dia_semana`, `quantidade_vagas`). N:1 com `Percurso` (um percurso pode ter várias rotas em dias/horários diferentes). Cada rota exige exatamente um percurso, como no diagrama de classes.
- **ExecucaoRota**: ocorrência datada de uma rota. Congela `data_hora_saida` e
  `quantidade_vagas` para não ser alterada por edições futuras na rota.
- **Ticket**: solicitação de um aluno em uma execução; representa reserva, posição
  em fila, cancelamento, embarque ou ausência.
- **Strike**: falta vinculada unicamente a um ticket marcado como ausente.
- **Justificativa**: solicitação única de revisão de um strike.

Não é possível desativar um percurso que ainda tenha rotas ativas. Não é possível vincular ou reativar rota em percurso inativo.

### Estrutura de Apps

```text
Transporte/
├── __init__.py
├── urls.py
├── percursos/       # App Django do model Percurso
├── rotas/           # App Django do model Rota
├── execucoes_rotas/ # App Django do model ExecucaoRota
├── tickets/         # App Django do model Ticket e fila de espera
├── strikes/         # App Django do model Strike
└── justificativas/  # App Django do model Justificativa
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

### 3. Execuções de rotas

- Criadas manualmente por L3 para uma rota e uma data.
- A data deve corresponder ao dia da semana da rota.
- Unicidade por `rota` + `data_execucao`: rotas distintas do mesmo percurso e dia,
  em horários diferentes, podem ter execuções normalmente.
- Estados: `ABERTA`, `FECHADA`, `EM_EMBARQUE`, `FINALIZADA`, `CANCELADA`.
- Reservas e entradas na fila exigem estado `ABERTA`.
- Para alunos, execuções disponíveis são exibidas somente de segunda a sexta,
  da meia-noite do próprio dia até exatamente 30 minutos antes da saída.
- QR Code só é validado em `EM_EMBARQUE`.

### 4. Tickets, capacidade e cancelamento

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

### 5. Posição dos tickets e prioridade PcD

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

### 6. Ausências, strikes e justificativas

- L3 marca um ticket `RESERVADO` como `AUSENTE` durante o embarque ou após a
  finalização; a ação cria exatamente um strike.
- Strike `ATIVO` conta para o bloqueio; `JUSTIFICADO` deixa de contar.
- O aluno pode enviar imediatamente uma justificativa para qualquer strike ativo
  próprio, mesmo antes de atingir o bloqueio por três strikes.
- L3 aprova ou rejeita justificativas pendentes.
- Aprovar altera o strike para `JUSTIFICADO`; o aluno só é desbloqueado quando
  restarem menos de três strikes ativos.

### 7. QR Code

- O backend emite em `codigo_qr` um conteúdo opaco assinado, com UUID público do
  ticket e execução. CPF, deficiência e IDs internos não são embutidos.
- O frontend transforma esse conteúdo em imagem e pode incluí-lo no PDF.
- L3 envia o conteúdo lido a `POST /cortex/transporte/tickets/validar-qr/`.
- Assinatura, execução e status são validados no banco; ticket cancelado, em fila,
  ausente ou adulterado é rejeitado.
- A primeira leitura muda o ticket para `EMBARCADO`; leituras posteriores são
  idempotentes e retornam `ja_validado=true`.

### 8. Permissões

Percursos e rotas continuam restritos a **L3** (`EDITAR_TUDO`). Execuções abertas
podem ser consultadas por qualquer autenticado; L3 vê e administra todas.
O aluno vê e altera apenas os próprios tickets, strikes e justificativas.

- **Views:** `IsAdminMixin` (`tem_acesso_elevado()`), o mesmo critério de L3: `is_staff`, `is_admin` ou superusuário.
- **Payload (login/me):** `gerenciar` é `true` só para L3; `reservar` exige aluno
  ativo, matriculado e com menos de três strikes ativos.
- **Compilação:** `UsuarioPermissions.permissoes_transporte()`.
- **Documentação viva da API:** `GET /cortex/identidade/permissoes/documentacao/` (`documentacao_transporte()`). Toda mudança de regra deve atualizar esse método no mesmo PR.

Swagger de cada endpoint de percursos e rotas declara `**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.`

### 9. Endpoints

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
- `GET /cortex/transporte/justificativas/` e
  `GET /cortex/transporte/justificativas/<pk>/`
- `POST /cortex/transporte/strikes/<pk>/justificativas/`
- `POST /cortex/transporte/justificativas/<pk>/aprovar/`
- `POST /cortex/transporte/justificativas/<pk>/rejeitar/`
