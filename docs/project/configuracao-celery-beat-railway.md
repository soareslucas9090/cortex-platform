# Configuração do Celery Beat no Railway

Este guia descreve como executar o Celery Beat do Cortex no Railway. O Beat é
responsável por disparar as tarefas periódicas configuradas no Django; o Celery
Worker apenas recebe e processa essas tarefas.

No domínio de Transporte, o Beat envia a tarefa
`Transporte.execucoes_rotas.tasks.gerar_execucoes_rotas_automaticas_task` a cada
cinco minutos. Essa tarefa cria as execuções das rotas do dia de acordo com o
dia da semana e com as exceções do calendário operacional.

## Arquitetura esperada

O projeto do Railway deve possuir, no mínimo, os seguintes serviços:

| Serviço | Responsabilidade | Processo contínuo |
| --- | --- | --- |
| Web | Executar a API Django/Gunicorn | Sim |
| Worker | Processar tarefas assíncronas | Sim |
| Beat | Disparar tarefas periódicas | Sim |
| PostgreSQL | Persistir os dados | Sim |
| Redis | Transportar as mensagens do Celery | Sim |

O Worker e o Beat devem apontar para o mesmo código, banco de dados e Redis da
aplicação Web.

> O Beat deve possuir apenas uma réplica. Duas instâncias podem enviar a mesma
> tarefa periódica simultaneamente.

## Pré-requisitos

Antes de configurar o Beat, confirme que:

- a aplicação Web e o Worker estão publicados e saudáveis;
- o PostgreSQL e o Redis estão disponíveis no mesmo projeto/ambiente;
- o Worker consegue se conectar ao Redis;
- as migrações do Django foram aplicadas;
- o serviço usa a mesma branch ou o mesmo commit implantado nos demais
  processos do backend.

## 1. Criar o serviço

No painel do Railway:

1. Abra o projeto e o ambiente que executam o backend.
2. Clique em **New** e crie um serviço vazio ou conecte novamente o mesmo
   repositório GitHub usado pelo backend.
3. Nomeie o serviço como `celery-beat`.
4. Em **Source**, selecione o mesmo repositório e a mesma branch do serviço Web
   e do Worker.
5. Se houver configuração de **Root Directory**, **Build Command** ou caminho de
   Dockerfile no Worker, replique-a no Beat.

O serviço não recebe requisições HTTP, portanto não precisa de domínio público.

## 2. Configurar as variáveis

Em **Variables**, replique as variáveis do Worker. É importante que os dois
serviços usem as mesmas referências de PostgreSQL e Redis.

As variáveis consumidas diretamente pelo Celery no Cortex são:

```env
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

Substitua `Redis` pelo nome real do serviço Redis no projeto, caso seja
diferente. Também replique as variáveis Django e de banco já utilizadas pelo
Worker, especialmente:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DATABASE_ENGINE
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
DATABASE_HOST
DATABASE_PORT
```

Não copie valores manualmente quando puder usar variáveis de referência do
Railway. Assim, uma alteração no banco ou no Redis é compartilhada entre os
serviços.

## 3. Definir o comando de inicialização

Em **Settings > Deploy > Custom Start Command**, informe:

```bash
celery -A Cortex beat --loglevel=INFO
```

Esse é um processo contínuo. Não configure o serviço como um Railway Cron Job e
não use o comando do Worker nesse serviço.

A agenda já está declarada em `Cortex/settings.py` por meio de
`CELERY_BEAT_SCHEDULE`. Não é necessário cadastrar manualmente a expressão de
cron no painel do Railway.

## 4. Implantar

Revise as alterações pendentes no Railway e faça o deploy. Configure o serviço
com exatamente uma réplica.

Após a inicialização, os logs devem indicar que o Celery Beat iniciou e carregou
a agenda. A cada cinco minutos, deve aparecer no Beat uma mensagem semelhante a:

```text
Scheduler: Sending due task gerar-execucoes-rotas-pelo-calendario
```

No serviço Worker, deve aparecer o recebimento da tarefa:

```text
Task Transporte.execucoes_rotas.tasks.gerar_execucoes_rotas_automaticas_task received
```

Depois do processamento, o Worker deve registrar a conclusão da tarefa. A
mensagem informa a data, quantas execuções foram criadas, quantas já existiam,
quantas estavam fora do prazo e se o dia era operacional.

## 5. Validar a regra de geração

A ausência de novas execuções nem sempre representa erro. A tarefa somente cria
uma execução quando todas estas condições são atendidas:

- a data é operacional segundo o calendário de Transporte;
- a rota está ativa;
- o percurso da rota está ativo;
- o dia da semana da rota corresponde à data atual;
- o horário atual ainda não passou de 30 minutos antes da saída;
- ainda não existe execução para a mesma rota e data.

Sem exceção ativa no calendário, segunda a sexta são dias operacionais e sábado
e domingo não são. Exceções letivas ou de reposição liberam a data; feriados,
pontos facultativos, suspensões, recessos e férias bloqueiam novas execuções.

## Diagnóstico de problemas

### O Beat não inicia

Confira os logs do deploy, o comando de inicialização, a branch, o diretório
raiz e se as dependências do projeto foram instaladas.

### Erro de conexão com o Redis

Confira se `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND` referenciam o Redis do
mesmo ambiente. Dentro do Railway, não use `localhost` para acessar outro
serviço.

### O Beat envia, mas o Worker não recebe

Confirme que Beat e Worker usam a mesma URL de broker e que o Worker está
saudável. Também confirme que ambos foram implantados com a mesma versão do
código.

### O Worker informa tarefa não registrada

Faça um novo deploy do Worker com o mesmo commit usado pelo Beat. O projeto
carrega as tarefas automaticamente a partir dos apps Django instalados.

### A tarefa executa, mas não cria rotas

Consulte a mensagem de conclusão no Worker e valide o calendário, o dia da
semana, os estados da rota e do percurso e o limite de 30 minutos antes da
saída. Reexecuções são idempotentes e não criam duplicatas.

## Desativação e reversão

Para interromper temporariamente os disparos automáticos, pare o serviço
`celery-beat` no Railway. Não é necessário parar o Worker, pois ele pode
continuar processando outras tarefas assíncronas do sistema.

Ao reativar o Beat, ele volta a reconciliar o dia corrente a cada cinco minutos.
Rotas cujo limite de 30 minutos já passou não são criadas retroativamente.

## Referências

- [Serviços no Railway](https://docs.railway.com/services)
- [Comandos de build e inicialização](https://docs.railway.com/builds/build-and-start-commands)
- [Guia de Django no Railway](https://docs.railway.com/guides/django)
