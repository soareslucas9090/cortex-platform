# ADR-004 — Sistema de notificações (bounded context Notificacoes)

- **Status:** Aceito
- **Data:** 2026-10-21

## Contexto

Diversos módulos do Cortex precisam informar usuários sobre eventos relevantes (aprovações, lembretes operacionais, falhas de processos assíncronos, etc.). Hoje não existe um mecanismo transversal: cada domínio tenderia a duplicar persistência de mensagens, envio de e-mail ou acoplamento a sinais Django.

O monolith Django/DRF já dispõe de Celery + Redis para trabalho assíncrono, de `Usuario` e `Contato` no mesmo banco (Identidade), de helper SMTP (`enviar_email_simples` em AppCore) e de frontend que consome exclusivamente esta API REST. A modularização por domínio (ADR-001) exige que capacidades transversais de produto tenham fronteira explícita, e não fiquem espalhadas em AppCore ou Identidade.

Requisitos da v1:

- Caixa de entrada **in-app** (canal `sistema`) consultável via REST.
- Entrega **e-mail** assíncrona quando aplicável.
- **SMS** e **WhatsApp** reservados como adaptadores de canal (stubs ignorados até credenciais).
- **Sem** WebSocket ou SSE na v1.
- **Dispatcher genérico** invocável por qualquer módulo a partir da camada `business`.
- **Sem** acoplamento a eventos específicos de Infraestrutura ou Transporte nesta entrega (apenas a infraestrutura de disparo).

---

## Decisão

Implementar notificações como **bounded context próprio** no monolith Django:

| Item | Valor |
|------|--------|
| Módulo agregador | `Notificacoes/` |
| Prefixo HTTP | `/cortex/notificacoes/` |
| `app_name` do agregador | `notificacoes` |
| Chave de permissões no payload | `notificacoes` |

### Apps internos

| App | Model principal | Observação |
|-----|-----------------|------------|
| `notificacoes/` | `Notificacao` | Agregado principal (caixa in-app) |
| (mesmo app) | `Envio` | Registro por canal/tentativa — **exceção documentada** à regra um-app-um-model |

A exceção `Notificacao` + `Envio` no mesmo app é aceita porque `Envio` é entidade auxiliar de rastreio de entrega (status por canal), sem produto HTTP próprio; separar em outro app Django não agregaria coesão de negócio.

### Dispatcher (único ponto de criação)

Outros domínios **não** expõem POST de criação para o frontend. A criação ocorre apenas via:

```text
Notificacao().business.disparar(...)
```

Chamada a partir de `business.py` de outros módulos, no mesmo fluxo de negócio que motivou a notificação. **Como usar** (import, exemplo no `try` do emissor, `tipo`, idempotência, canais, transação): [docs/domains/notificacoes.md](../domains/notificacoes.md#como-um-business-dispara-uma-notificação).

**Proibido** na v1:

- endpoint HTTP de criação para clientes MeuIF ou terceiros;
- `post_save` / signals Django como gatilho genérico de notificação.

### Canais (v1)

| Canal | Comportamento |
|-------|----------------|
| `sistema` | Persiste registro em `Notificacao` (inbox); sempre que o disparo incluir este canal |
| `email` | Task Celery após `transaction.on_commit`; corpo via `enviar_email_simples` |
| `sms`, `whatsapp` | Adaptadores previstos; **ignorados** em runtime até configuração de credenciais — não falham o disparo dos demais canais |

Canal `sistema` **não** duplica linha em `Envio` quando a entrega in-app é o próprio `Notificacao`; `Envio` registra tentativas de canais externos (e-mail e, no futuro, SMS/WhatsApp).

### Privacidade e operação

- API REST: usuário autenticado acessa **somente a própria inbox** (`destinatario = request.user`), **inclusive** para L2/L3 — níveis Cortex **não** ampliam leitura de notificações de terceiros via API.
- Django Admin: consulta e suporte operacional (sem substituir a inbox do usuário).

### Fora do escopo da v1

- WebSocket, SSE ou push em tempo real.
- Preferências de canal por usuário.
- Integração automática com eventos de domínio (Infraestrutura, Transporte, etc.) — wiring fica para marcos posteriores.
- Fila Celery dedicada `notificacoes` (usa fila/worker padrão existente).

---

## Justificativa

1. **Celery + Redis já operacionais** — entrega assíncrona de e-mail sem novo runtime.
2. **`Usuario` e `Contato` no mesmo banco** — resolução de e-mail sem integração externa de identidade.
3. **ADR-001** — produto transversal como módulo agregador na raiz, não pasta genérica nem “utilitário” solto.
4. **`enviar_email_simples` existente** — reutilização do helper SMTP do AppCore.
5. **Frontend consome esta API REST** — inbox e contadores como recursos HTTP estáveis sob `/cortex/notificacoes/`.
6. **Dispatcher em `business`** — mantém views leves, testabilidade e controle explícito do emissor (sem magia de signals).

---

## Alternativas consideradas e rejeitadas

| Alternativa | Motivo da rejeição |
|-------------|-------------------|
| Microserviço **FastAPI** separado | Duplica identidade, filas e deploy; quebra monolith modular ADR-001 |
| Módulo dentro de **AppCore** | AppCore é base técnica, não bounded context de produto |
| Módulo dentro de **Identidade** | Notificação não é atributo de identidade; poluiria `Usuario` com inbox de produto |
| **Django signals** (`post_save` genérico) | Acoplamento oculto, ordem imprevisível e difícil auditoria do emissor |
| WebSocket/SSE na v1 | Complexidade operacional e contrato frontend fora do necessário imediato |

---

## Implicações

### Fluxo transacional

1. `disparar` persiste `Notificacao` (e `Envio` quando canal externo) **na transação corrente** do caller.
2. Após commit, enfileira task Celery para canais assíncronos (`email`, futuros SMS/WhatsApp).
3. Falha no envio de e-mail **não** remove nem reverte o registro da inbox (`sistema`); atualiza status em `Envio` e permite reprocessamento operacional via admin se necessário.

### Permissões (ADR-002)

Hooks em `Identidade/usuarios/`:

- `UsuarioPermissions.permissoes_notificacoes()`
- `documentacao_notificacoes()` em `documentacao.py`

Escopo da API independente de L1–L3 para leitura alheia (sempre próprio destinatário). Detalhes em `docs/domains/notificacoes.md`.

### Artefatos relacionados

- `docs/domains/notificacoes.md` — contrato operacional e endpoints
- `docs/diagrams/02-bounded-contexts.md` — mapa canônico (seção Notificacoes)
- `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- `docs/decisions/ADR-002-permissoes-cortex-niveis.md`

---

## Resumo

Fica decidido o bounded context **Notificacoes** no monolith Django, com inbox in-app, e-mail assíncrono via Celery, dispatcher `Notificacao().business.disparar(...)` para outros módulos, API somente leitura/atualização de leitura para o próprio usuário, e rejeição de microserviço FastAPI, AppCore/Identidade como donos do produto e signals genéricos.
