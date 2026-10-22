# Diretrizes do Domínio: Notificacoes

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Notificacoes** do projeto Cortex.

## Visão Geral do Domínio

O módulo **Notificacoes** centraliza o disparo transversal de avisos para usuários: caixa de entrada in-app (canal `sistema`) e entrega assíncrona por e-mail na v1. Outros domínios invocam o dispatcher a partir de sua camada `business`; **não** há criação via HTTP para o frontend.

**Para emitir um aviso a partir de outro módulo, comece em [Como um business dispara uma notificação](#como-um-business-dispara-uma-notificação).**

- **Foco v1:** inbox REST, contador de não lidas, marcar como lida; e-mail via Celery + `enviar_email_simples`.
- **Canais futuros:** SMS e WhatsApp como adaptadores em `Envio` — ignorados até credenciais.
- **Sem** WebSocket/SSE, preferências de canal ou fila Celery dedicada na v1.
- Decisão arquitetural: [ADR-004](../decisions/ADR-004-sistema-de-notificacoes.md).

Referências complementares:

- [ADR-002: Permissões Cortex por Nível](../decisions/ADR-002-permissoes-cortex-niveis.md)
- [Configuração do Celery Beat](../project/configuracao-celery-beat.md) (workers existentes; notificações usam fila padrão)

### Dependências de outros domínios

| Domínio | Uso |
| ------- | --- |
| **Identidade** | `Usuario` como destinatário (`destinatario`); `Contato` para resolução de e-mail; hooks `permissoes_notificacoes()` e `documentacao_notificacoes()` |

Nenhum outro domínio de negócio é dependência obrigatória do núcleo de notificações. Emissores (Infraestrutura, Transporte, Acadêmico, etc.) dependem de **Notificacoes**, não o contrário.

### Estrutura de Apps

```text
Notificacoes/
├── __init__.py
├── urls.py                 # app_name = 'notificacoes'
└── notificacoes/           # Notificacao + Envio (exceção 1-app-2-models)
    ├── models.py
    ├── business.py         # disparar(...)
    ├── rules.py
    ├── helpers.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── tasks.py            # envio assíncrono de e-mail
    └── migrations/
```

---

## Prefixo HTTP

Todas as rotas públicas do módulo ficam sob:

**`/cortex/notificacoes/`**

(montagem em `Cortex/urls.py` → `Notificacoes.urls`).

**Não** expor POST de criação de notificação na API v1.

---

## Como um business dispara uma notificação

Único ponto de criação no código: `Notificacao().business.disparar(...)`.

Chame **somente** da camada `business` do módulo emissor, **dentro do `try` já existente** do método (o `disparar` também tem o próprio `try/except`). Não chame da view, do serializer, de `post_save` nem de signal.

### Import

Importe o **model** pelo caminho concreto (não instancie `NotificacaoBusiness()`):

```python
from Notificacoes.notificacoes.models import Notificacao
```

Prefira o import **dentro do método** que dispara, como já se faz com tasks Celery neste repositório — evita import circular entre domínios.

### Exemplo mínimo (inbox + e-mail)

O default de `canais` já é `['sistema', 'email']`. Basta destinatário, tipo, título e corpo:

```python
Notificacao().business.disparar(
    destinatario_id=usuario.id,
    tipo='infraestrutura.emprestimo.registrado',
    titulo='Empréstimo registrado',
    corpo='Seu empréstimo foi registrado na guarita.',
)
```

### Exemplo completo no `business` do emissor

```python
def registrar_emprestimo(self, solicitante, **dados):
    from Notificacoes.notificacoes.models import Notificacao

    try:
        emprestimo = Emprestimo.objects.create(solicitante=solicitante, **dados)
        Notificacao().business.disparar(
            destinatario_id=solicitante.id,
            tipo='infraestrutura.emprestimo.registrado',
            titulo='Empréstimo registrado',
            corpo=f'Seu empréstimo #{emprestimo.pk} foi registrado na guarita.',
            canais=['sistema', 'email'],
            contexto={
                'emprestimo_id': emprestimo.pk,
                'url': f'/infraestrutura/emprestimos/{emprestimo.pk}/',
            },
            chave_idempotencia=f'emprestimo:{emprestimo.pk}:registrado',
        )
        return emprestimo
    except Exception as e:
        self.relancar_ou_erro_sistema(
            e,
            'Não foi possível registrar o empréstimo.',
            logger,
        )
```

Vários destinatários: um `disparar` por `destinatario_id` (não há envio em lote na v1).

### Parâmetros

| Parâmetro | Obrigatório | Padrão | Descrição |
| --------- | ----------- | ------ | --------- |
| `destinatario_id` | sim | — | PK de `Usuario` (não passe a instância) |
| `tipo` | sim | — | Código estável do evento (ver convenção abaixo) |
| `titulo` | sim | — | Assunto curto (também vira subject do e-mail) |
| `corpo` | sim | — | Texto da inbox e corpo do e-mail |
| `canais` | não | `['sistema', 'email']` | Lista; valores válidos: `sistema`, `email`, `sms`, `whatsapp` |
| `contexto` | não | `{}` | JSON para o frontend (ids, deep link). Sem GenericForeignKey |
| `chave_idempotencia` | não | `None` | Evita duplicata para o mesmo destinatário + tipo |

Retorno: instância de `Notificacao` (a recém-criada ou a já existente, se a chave bater).

### Convenção de `tipo`

String estável, minúscula, com pontos: `<dominio>.<recurso>.<evento>`.

Exemplos: `infraestrutura.emprestimo.atraso`, `transporte.ticket.confirmado`, `identidade.usuario.conta_criada`.

O frontend e o filtro `?tipo=` da API usam esse código. **Não renomeie** depois de emitir em produção.

### `chave_idempotencia`

Quando preenchida, a unicidade é `(destinatario, tipo, chave_idempotencia)`:

- mesmo trio de novo → devolve a notificação já existente e **não** cria outro `Envio`;
- omita a chave se cada chamada for um aviso novo (lembrete que pode repetir).

Sugestão de valor: identifique o fato, não o texto (`emprestimo:42:atraso`, não o título).

### Canais

| Valor | Efeito na v1 |
| ----- | ------------ |
| `sistema` | Inbox. A linha `Notificacao` **sempre** é criada no disparo; este canal não gera `Envio` |
| `email` | Cria `Envio` `pendente` e enfileira a task **depois do commit**. Sem e-mail no usuário/`Contato` → `ignorado`; SMTP falha depois → `falhou`. A inbox **permanece** |
| `sms` / `whatsapp` | Cria `Envio` `ignorado` (`Canal ainda não configurado.`). Não enfileira task e não aborta os outros canais |

Só inbox, sem e-mail: `canais=['sistema']`.

### Transação e Celery

`disparar` grava na **transação corrente** do caller. A task `enviar_envio_task` só entra na fila no `transaction.on_commit`.

- Se o método de business der rollback, a notificação some e o e-mail **não** é enfileirado.
- Não chame `enviar_envio_task.delay` no módulo emissor.
- Não abra `transaction.atomic()` extra na view (já é da BasicView).
- Worker + Redis já usados pelo Cortex; **não** há fila nem variável de ambiente nova. Sem worker, a inbox existe e o `Envio` de e-mail fica `pendente` até o worker processar.
- Beat **não** dispara notificação.

SMTP usa `DEFAULT_FROM_EMAIL` / `EMAIL_HOST_*` já existentes. Sem SMTP configurado, a inbox continua; o e-mail tende a `falhou` após retries.

### Exceções (propagam para o caller)

| Situação | Exceção |
| -------- | ------- |
| `destinatario_id`, `tipo`, `titulo` ou `corpo` vazios; canal desconhecido | `ValidationException` |
| `destinatario_id` inexistente | `NotFoundException` |

Como o `disparar` está no `try` do emissor, essas exceções **abortam** a operação de negócio (o `relancar_ou_erro_sistema` do caller as relança). Falha **assíncrona** de SMTP **não** desfaz o que já commitou e **não** apaga a inbox.

### O que o emissor não deve fazer

- Chamar `disparar` na view, no serializer ou em signal/`post_save`.
- Instanciar `NotificacaoBusiness()` direto.
- Passar o objeto `Usuario` no lugar de `destinatario_id`.
- Criar `Envio` ou mandar e-mail com `enviar_email_simples` por fora deste fluxo.
- Expor POST de criação na API.

---

## Modelos

### `Notificacao` (inbox in-app)

| Campo | Tipo / notas |
| ----- | -------------- |
| `destinatario` | FK → `Identidade.usuarios.Usuario` (indexado) |
| `tipo` | CharField estável (ex.: `emprestimo.atraso`) — indexado; filtro da API |
| `titulo` | CharField — assunto curto |
| `corpo` | TextField — corpo em texto (e base do e-mail quando canal `email`) |
| `contexto` | JSONField, default `{}` — deep link, ids; **sem** GenericForeignKey |
| `lida_em` | DateTime, nullable — `null` = não lida |
| `chave_idempotencia` | CharField opcional; unicidade `(destinatario, tipo, chave_idempotencia)` quando preenchida |
| Campos de auditoria | Conforme `BasicModel` |

Constraint de negócio: toda linha visível na API pertence ao `destinatario` autenticado. Sem boolean `lida` separado — o estado deriva de `lida_em`.

### `Envio` (tentativa por canal externo)

| Campo | Tipo / notas |
| ----- | -------------- |
| `notificacao` | FK → `Notificacao` |
| `canal` | Choice: `email`, `sms`, `whatsapp` (extensível) |
| `status` | Choice — ver tabela abaixo |
| `destino` | CharField opcional — e-mail ou telefone efetivo usado na tentativa |
| `tentativas` | PositiveSmallInteger, default 0 |
| `ultimo_erro` | TextField opcional — mensagem resumida da falha |
| `enviado_em` | DateTime nullable — preenchido em sucesso |

Canal **`sistema`** não gera `Envio`: a própria `Notificacao` materializa a inbox.

#### Status de `Envio`

| Status | Significado |
| ------ | ----------- |
| `pendente` | Aguardando task Celery |
| `enviado` | Canal externo concluído com sucesso |
| `falhou` | Erro após esgotar retries da task |
| `ignorado` | Sem destino resolvido, ou canal ainda sem credencial (SMS/WhatsApp) |

Falha de e-mail **não** exclui `Notificacao`; apenas atualiza `Envio` e preserva a inbox.

---

## Resolução de e-mail (canal `email`)

Ordem em `Notificacao().helper.resolver_email_destinatario` (contatos 1:N):

1. `Usuario.email`, se preenchido
2. primeiro `Contato.email_academico` do usuário
3. primeiro `Contato.email_pessoal`

Se nenhum endereço: `Envio` em `ignorado`; a inbox permanece.

---

## Permissões

Dois eixos (ADR-002):

### Níveis Cortex L1–L3

**Não** ampliam escopo da inbox. L2/L3 **não** listam notificações de outros usuários via API.

### Payload `user.permissoes['notificacoes']`

Compilado em `UsuarioPermissions.permissoes_notificacoes()` — v1: `{'ler_proprias': True}` para qualquer usuário autenticado. Endpoints exigem autenticação e filtram `destinatario=request.user` no queryset (L2/L3 não ampliam).

**Manutenção:** alterar regra exige atualizar `documentacao_notificacoes()` em `Identidade/usuarios/documentacao.py` no mesmo PR.

Views: `IsAuthenticatedMixin`; escopo fixo no queryset (não usar `escopar_queryset_cortex` para ampliar leitura).

Operações administrativas: Django Admin (staff), fora do escopo da API MeuIF.

---

## Endpoints (v1)

Paths relativos ao prefixo `/cortex/notificacoes/`.

| Método | Path | Comportamento |
| ------ | ---- | ------------- |
| GET | `notificacoes/` | Lista paginada da inbox do usuário (filtros `lida`, `tipo` apenas estreitam; ordenação por data desc) |
| GET | `notificacoes/nao-lidas/contador/` | Contador inteiro de não lidas (`lida_em` nulo) |
| PATCH | `notificacoes/{id}/lida/` | Marca uma notificação como lida (`lida_em=now`) — somente se `destinatario=request.user` |
| PATCH | `notificacoes/marcar-todas-lidas/` | Marca todas as não lidas do destinatário |

Toda view deve declarar bloco **`**Permissões:**`** no `@extend_schema` (autenticado; apenas própria inbox).

---

## Camadas e arquivos de referência (implementação)

| Assunto | Onde implementar |
| ------- | ---------------- |
| Dispatcher | `Notificacoes/notificacoes/business.py` |
| Validação de canais | `Notificacoes/notificacoes/rules.py` |
| E-mail / resolução de endereço | `Notificacoes/notificacoes/helpers.py`, `tasks.py` |
| Escopo queryset | `Notificacoes/notificacoes/views.py` |

Fluxo padrão: **View → Business → Rules/Helpers**; `business.py` com try/except conforme [regras-do-projeto](../project/regras-do-projeto.md).

---

## O que NÃO fazer

- **Não** criar POST público de notificação para o frontend.
- **Não** disparar via `post_save` ou signals genéricos.
- **Não** colocar inbox em `Identidade.usuarios` ou utilitários soltos no AppCore.
- **Não** remover `Notificacao` quando e-mail falhar.
- **Não** implementar WebSocket/SSE ou preferências de canal na v1.
- **Não** acoplar esta entrega a eventos específicos de Infraestrutura/Transporte (wiring é marco posterior).
- **Não** usar L3 para ler inbox de terceiros via API.

---

## Fora de escopo (v1)

- Push em tempo real (WebSocket/SSE).
- Preferências por usuário (opt-in/opt-out por canal).
- Fila Celery dedicada `notificacoes`.
- SMS/WhatsApp operacionais (apenas contrato de `Envio` + stubs).
- Relatórios gerenciais de notificações enviadas (admin only se necessário).
