# Diretrizes do Domínio: Notificacoes

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Notificacoes** do projeto Cortex.

## Visão Geral do Domínio

O módulo **Notificacoes** centraliza o disparo transversal de avisos para usuários: caixa de entrada in-app (canal `sistema`) e entrega assíncrona por e-mail na v1. Outros domínios invocam o dispatcher a partir de sua camada `business`; **não** há criação via HTTP para o frontend.

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

## Contrato `disparar`

Entrada via `NotificacaoBusiness.disparar` (instanciado como `Notificacao().business.disparar(...)` conforme padrão do projeto).

Parâmetros esperados (kwargs documentados — implementação valida em `rules.py`):

| Parâmetro | Obrigatório | Descrição |
| --------- | ----------- | --------- |
| `destinatario_id` | sim | PK de `Usuario` |
| `tipo` | sim | Código estável (ex.: `emprestimo.atraso`) |
| `titulo` | sim | Título da notificação |
| `corpo` | sim | Texto principal |
| `canais` | não | Default `['sistema', 'email']` |
| `contexto` | não | Dict serializável JSON |
| `chave_idempotencia` | não | Evita duplicata para o mesmo destinatário+tipo |

Exemplo ilustrativo (chamada a partir de outro `business.py`):

```python
Notificacao().business.disparar(
    destinatario_id=user.id,
    tipo='emprestimo.atraso',
    titulo='Empréstimo atrasado',
    corpo='O empréstimo #42 está atrasado há mais de 24 h.',
    canais=['sistema', 'email'],
    contexto={'url': '/emprestimos/42'},
    chave_idempotencia='emprestimo:42',
)
```

Fluxo:

1. Valida destinatário, tipo e canais.
2. Se `chave_idempotencia` já existir para o mesmo destinatário+tipo, devolve a `Notificacao` existente (não cria outra).
3. Cria `Notificacao` quando `sistema` ∈ `canais` (default inclui `sistema`).
4. Cria `Envio` por canal externo (`email`, `sms`, `whatsapp`).
5. `transaction.on_commit` enfileira `enviar_envio_task.delay(envio_id)` para cada `Envio` pendente.
6. Canais `sms`/`whatsapp` na v1 → `Envio` com status `ignorado`, **sem** abortar `sistema` nem e-mail.

---

## Resolução de e-mail (canal `email`)

Ordem ao montar destinatário SMTP:

1. `Usuario.email` (campo de login), se preenchido e válido para envio
2. `Contato.email_academico` (FK/usuário 1:1 conforme Identidade)
3. `Contato.email_pessoal`

Se nenhum endereço válido: `Envio` em `ignorado`; **inbox permanece** se canal `sistema` foi pedido.

Implementação de referência futura: helper em `Notificacoes/notificacoes/helpers.py`.

---

## Permissões

Dois eixos (ADR-002):

### Níveis Cortex L1–L3

**Não** ampliam escopo da inbox. L2/L3 **não** listam notificações de outros usuários via API.

### Payload `user.permissoes['notificacoes']`

Compilado em `UsuarioPermissions.permissoes_notificacoes()` — na v1 tipicamente metadado mínimo ou dict vazio com documentação viva; endpoints exigem autenticação e filtram `destinatario=request.user` no `get_queryset`.

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
