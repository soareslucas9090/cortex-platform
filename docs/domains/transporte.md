# Diretrizes do Domínio: Transporte

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Transporte** do projeto Cortex (MeuIF-Transporte).

## Visão Geral do Domínio

O domínio `Transporte` gerencia o transporte universitário. A entrega atual cobre
**percursos** (RF017), **rotas** (RF016) e a primeira visão operacional do
**motorista** (RF013).

### Modelos e Relacionamentos

- **Percurso**: trajeto nomeado do ônibus (`apelido` + `descricao`). Campo `ativo` no lugar de exclusão física.
- **Rota**: agendamento do ônibus em um percurso (`horario_saida`, `dia_semana`, `quantidade_vagas`). N:1 com `Percurso` (um percurso pode ter várias rotas em dias/horários diferentes). Cada rota exige exatamente um percurso, como no diagrama de classes.
- **Motorista**: perfil associado 1:1 a `Usuario`. O campo `usuario` também é a
  chave primária do perfil e usa `PROTECT`, impedindo a exclusão física do usuário
  enquanto o vínculo existir. O campo `ativo` controla a disponibilidade do perfil.

Não é possível desativar um percurso que ainda tenha rotas ativas. Não é possível vincular ou reativar rota em percurso inativo.

### Estrutura de Apps

```text
Transporte/
├── __init__.py
├── urls.py
├── percursos/       # App Django do model Percurso
├── rotas/           # App Django do model Rota
└── motoristas/      # App Django do perfil Motorista
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

### 3. Visão das rotas do dia pelo motorista (RF013)

- Todos os motoristas ativos visualizam todas as rotas ativas programadas para o dia atual.
- A data atual usa o timezone `America/Fortaleza` configurado no projeto.
- Rotas são ordenadas pelo horário de saída e, em caso de empate, pelo apelido do percurso.
- A resposta contém somente dados já pertencentes à rota e ao percurso: data, horário,
  dia da semana, capacidade e descrição/apelido do percurso.
- A consulta é somente de leitura e não cria nem altera registros.
- Início/finalização de rota, reservas, status operacional e tickets ficam fora do
  escopo desta entrega.

#### Estados do perfil Motorista

- **Ativo**: com a conta de usuário também ativa, recebe a capacidade
  `transporte.motorista` e pode consultar as rotas do dia.
- **Inativo**: não recebe a capacidade e não pode acessar a consulta, mesmo que a
  conta de usuário esteja ativa.
- Conta de usuário inativa sempre bloqueia o acesso, independentemente do estado do
  perfil Motorista.

#### Apresentação temporária no frontend

Enquanto Reservas, Tickets e a operação do Conferente não estiverem integrados, o
frontend apresenta localmente os rótulos `RESERVAS FINALIZADAS`, `RESERVAS EM ABERTO`
e `RESERVAS NÃO INICIADAS`, além de `Tickets solicitados: — / capacidade`.

Esses valores são provisórios, não são persistidos e não fazem parte do serializer
nem do contrato OpenAPI desta entrega. O adapter temporário deve ser substituído
pelos dados reais quando esses módulos forem disponibilizados. A tela também não
oferece ação de iniciar ou finalizar rota, responsabilidade futura do Conferente.

### 4. Permissões

#### Gestão (perfil TI)

Toda a API de percursos e rotas exige **L3** (`EDITAR_TUDO`). Não é catálogo aberto: L1 e L2 recebem 403 em listagem, detalhe e escrita.

- **Views:** `IsAdminMixin` (`tem_acesso_elevado()`), o mesmo critério de L3: `is_staff`, `is_admin` ou superusuário.
- **Payload (login/me):** `user.permissoes.transporte.gerenciar` é `true` só para L3, para o frontend exibir os cadastros de Transporte apenas ao perfil TI.
- **Compilação:** `UsuarioPermissions.permissoes_transporte()`.
- **Documentação viva da API:** `GET /cortex/identidade/permissoes/documentacao/` (`documentacao_transporte()`). Toda mudança de regra deve atualizar esse método no mesmo PR.

Swagger de cada endpoint de percursos e rotas declara `**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.`

#### Visualização (motorista)

- `user.permissoes.transporte.motorista` é `true` somente para usuário e perfil Motorista ativos.
- L3/TI não recebe a capacidade operacional automaticamente.
- O endpoint de leitura usa o `IsAuthenticatedMixin` padrão do `AppCore`; a camada
  `Business` valida que o usuário possui perfil Motorista ativo.

### 5. Endpoints

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
