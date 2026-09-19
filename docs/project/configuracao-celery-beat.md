# Configuração do Celery Beat

Este guia descreve como executar o Celery Beat do Cortex. O Beat é responsável por
disparar as tarefas periódicas configuradas no Django; o Celery Worker apenas
recebe e processa essas tarefas.

No domínio de Transporte, o Beat envia a tarefa
`Transporte.execucoes_rotas.tasks.gerar_execucoes_rotas_automaticas_task` a cada
cinco minutos. Essa tarefa cria as execuções das rotas do dia e, a partir das
19h, também do dia seguinte, de acordo com o dia da semana e com as exceções do
calendário operacional.

## Compose de produção (`docker/docker-compose-production.yml`)

O arquivo de produção define apenas os serviços **web** (Gunicorn) e **worker** (Celery), além de PostgreSQL e Redis. **Não há serviço `beat` no compose** — em produção o Celery Beat precisa ser executado em processo ou serviço separado (systemd, Kubernetes, PaaS etc.), com o mesmo código e variáveis do Worker. Este documento não altera o compose; apenas registra o fato.

## Arquitetura esperada

O ambiente de produção deve possuir, no mínimo, os seguintes processos:

| Processo | Responsabilidade | Contínuo |
| --- | --- | --- |
| Web | Executar a API Django/Gunicorn | Sim |
| Worker | Processar tarefas assíncronas | Sim |
| Beat | Disparar tarefas periódicas | Sim |
| PostgreSQL | Persistir os dados | Sim |
| Redis | Transportar as mensagens do Celery | Sim |

O Worker e o Beat devem apontar para o mesmo código, banco de dados e Redis da
aplicação Web.

> O Beat deve possuir apenas uma instância ativa. Duas instâncias podem enviar a
> mesma tarefa periódica simultaneamente.

## Pré-requisitos

Antes de configurar o Beat, confirme que:

- a aplicação Web e o Worker estão publicados e saudáveis;
- o PostgreSQL e o Redis estão disponíveis no mesmo ambiente;
- o Worker consegue se conectar ao Redis;
- as migrações do Django foram aplicadas;
- o processo do Beat usa a mesma versão do código implantada nos demais
  processos do backend.

## Variáveis de ambiente

O Beat precisa das mesmas variáveis de ambiente do Worker. Em especial, as
variáveis consumidas diretamente pelo Celery no Cortex são:

```env
CELERY_BROKER_URL=redis://<host>:<porta>/<db>
CELERY_RESULT_BACKEND=redis://<host>:<porta>/<db>
```

Também replique as variáveis Django e de banco já utilizadas pelo Worker,
especialmente:

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

Beat e Worker devem usar exatamente a mesma URL de broker e o mesmo banco de
dados. Em ambientes com múltiplos serviços, prefira variáveis de referência ou
secrets compartilhados em vez de copiar valores manualmente.

## Comando de inicialização

O Beat é um processo contínuo. Execute:

```bash
celery -A Cortex beat --loglevel=INFO
```

Não substitua o Beat por um cron externo que invoque tarefas manualmente. O
agendamento já está declarado em `Cortex/settings.py` por meio de
`CELERY_BEAT_SCHEDULE`; não é necessário cadastrar expressões de cron em outro
lugar.

Em Docker, systemd, Kubernetes ou plataformas PaaS, configure um serviço
dedicado apenas para esse comando. Não use o comando do Worker no mesmo
processo do Beat.

## Implantação

Implante o Beat com exatamente uma réplica ativa. O serviço não recebe
requisições HTTP e não precisa de domínio público.

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

## Validar a regra de geração

A ausência de novas execuções nem sempre representa erro. A tarefa somente cria
uma execução quando todas estas condições são atendidas:

- a data é operacional segundo o calendário de Transporte;
- a data é hoje ou, a partir das 19h, o dia seguinte;
- a rota está ativa;
- o percurso da rota está ativo;
- o dia da semana da rota corresponde à data processada;
- o horário atual ainda não passou de 30 minutos antes da saída;
- ainda não existe execução para a mesma rota e data.

Sem exceção ativa no calendário, segunda a sexta são dias operacionais e sábado
e domingo não são. Exceções letivas ou de reposição liberam a data; feriados,
pontos facultativos, suspensões, recessos e férias bloqueiam novas execuções.

## Diagnóstico de problemas

### O Beat não inicia

Confira os logs do deploy, o comando de inicialização, a versão do código e se
as dependências do projeto foram instaladas.

### Erro de conexão com o Redis

Confira se `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND` apontam para o Redis do
mesmo ambiente. Em ambientes com múltiplos serviços, não use `localhost` para
acessar o broker de outro container ou máquina.

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

Para interromper temporariamente os disparos automáticos, pare o processo do
Beat. Não é necessário parar o Worker, pois ele pode continuar processando
outras tarefas assíncronas do sistema.

Ao reativar o Beat, ele volta a reconciliar o dia corrente e, depois das 19h,
também o dia seguinte, a cada cinco minutos.
Rotas cujo limite de 30 minutos já passou não são criadas retroativamente.

## Referências

- [Celery — Periodic Tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [Celery Beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#beat-entries)
