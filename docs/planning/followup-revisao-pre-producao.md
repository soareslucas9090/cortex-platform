# Follow-up — Revisão pré-produção (base completa)

Plano **rastreável e reutilizável** para corrigir os achados da revisão de código da base inteira antes de ir para produção.

Cada etapa é independente o bastante para ser feita **sozinha**, em outro dia, em outro computador, numa conversa nova com a IA.

**Origem:** revisão de código (skill `revisao-codigo`) em 16–17/08/2026, conversa “revisar toda a base / pré-produção”.  
**Parecer da revisão:** a arquitetura em camadas está majoritariamente no lugar; **ainda não está pronta para produção** enquanto as etapas **Crítico** desta lista estiverem `Pendente`.  
**Fontes de padrão:** [regras-do-projeto.md](../project/regras-do-projeto.md), [guia-implementacao.md](../project/guia-implementacao.md), [guia-revisao-de-codigo.md](../project/guia-revisao-de-codigo.md), [ADR-002](../decisions/ADR-002-permissoes-cortex-niveis.md), [identidade.md](../domains/identidade.md), [organizacional.md](../domains/organizacional.md), [pessoas-institucionais.md](../domains/pessoas-institucionais.md), [academico.md](../domains/academico.md), [schema infraestrutura](../schema/infraestrutura.md), [04-aggregates-and-invariants.md](../diagrams/04-aggregates-and-invariants.md).  
**Skill de implementação:** `.agents/skills/implementacao/SKILL.md`.  
**Migrations:** se a etapa gerar/alterar migration, usar a skill `django-safe-migration` (zero-downtime / PostgreSQL).

**Fora deste plano (já feito):** follow-up de fotos S3 — [followup-revisao-fotos-s3.md](followup-revisao-fotos-s3.md) (`FOTO-S3-1` a `FOTO-S3-14` concluídas). Não reabrir.

---

## Como retomar (obrigatório em conversa nova)

Cole isto no chat (troque o ID):

```text
Implemente SOMENTE a etapa PREPROD-N de docs/planning/followup-revisao-pre-producao.md.

Regras:
- Leia essa etapa por completo antes de editar.
- Não avance para outras etapas.
- Siga docs/project/regras-do-projeto.md e docs/project/guia-implementacao.md.
- Views leves: hooks do_action_* delegam ao Business; sem ORM de negócio, sem transaction, sem Rules/Helpers na view.
- Business: corpo inteiro em try/except + relancar_ou_erro_sistema; nunca expor str(e) de erro interno ao cliente.
- Se a etapa gerar migration: skill django-safe-migration.
- Ao terminar: (1) rode os testes citados na etapa; (2) marque a etapa como Concluída neste arquivo (status + data); (3) atualize a tabela de progresso.
```

Para só inspecionar o que falta, sem implementar:

```text
Qual é a próxima etapa pendente em docs/planning/followup-revisao-pre-producao.md? Resuma o que falta e a ordem sugerida.
```

Para retomar o pacote de go-live (só Críticos ainda pendentes):

```text
Liste as etapas Crítico ainda Pendentes em docs/planning/followup-revisao-pre-producao.md, na ordem da tabela de progresso. Não implemente.
```

### Convenção de status

| Valor | Significado |
|-------|-------------|
| `Pendente` | Ainda não começou |
| `Em andamento` | Alguém está fazendo agora (preencher “Quem / onde”) |
| `Concluída (AAAA-MM-DD)` | Critério de saída atendido e testes da etapa ok |
| `Desnecessária (AAAA-MM-DD)` | Não será implementada; regra vigente permanece — escrever o motivo na etapa |
| `Adiada` | Decidiu não fazer agora; escrever o motivo na etapa |

Marque **somente** a etapa que acabou de fechar. Não reescreva etapas já concluídas além do status.

---

## Contexto desta revisão (para outra máquina / conversa)

Revisão da base Django/DRF do Cortex (Identidade, Organizacional, Pessoas Institucionais, Acadêmico, Infraestrutura, Auth, Cortex/settings, Docker, AppCore na superfície).

**O que está certo (não “consertar”):**

- Views de domínio herdam **uma** `Basic*APIView` + mixin; `roteador_por_metodo` para vários verbos; `path(..., name=)`; `Cortex/urls.py` inclui só módulos.
- Business de domínio usa `relancar_ou_erro_sistema` no catch-all (contrato try/except).
- Sem instanciação `XxxBusiness()` / `XxxRules()` nos apps.
- Mixins Cortex L1/L2/L3 (`escopar_queryset_cortex`, `IsOwnerOrAdminMixin`, `IsAdminMixin`) e capacidades de Infraestrutura (`operar` / `cadastrar` / `autorizar`).
- Unique parcial `emprestimos_item_recurso_unico_aberto` no banco (impede dois itens abertos no mesmo recurso).
- Autorização XOR sala/recurso, vigência, revogação.
- Foto S3 via `AnexoS3` (prefixo, proxy, validação de conteúdo) — follow-up S3 concluído.
- GET da foto do recurso e da foto secundária do usuário permanece **público** (`AllowAny`); bucket privado. Não reabrir.

**Bugs de runtime confirmados no código:**

1. `GET .../emprestimos/<pk>/` usa `self.object` em `validate_retrieve` **antes** da `BasicRetrieveAPIView` atribuir o objeto → `AttributeError` → 500. A view também chama **Rules** direto (proibido).
2. `PATCH .../usuarios/<pk>/` (`IsOwnerOrAdminMixin`) aceita `usuario_coletivo` → L1/L2 ligam flag de conta coletiva.
3. `tipo_perfil in ('aluno')` é `in` sobre **string**, não tupla.
4. `SetorVinculo.__str__` usa `funcao.sigla` (campo inexistente; `Funcao` tem `papel_funcao`).
5. `AlunoCursoBusiness.atualizar_dados` não revalida `vinculo_unico_ativo` → PATCH `ativo=true` duplica vínculo ativo.
6. Senha padrão na criação/importação = CPF ou matrícula (não passa na política de complexidade).
7. Importação: ORM e `transaction.on_commit` na view; upload S3 que falha é ignorado; duas `EM_ANDAMENTO` possíveis; cancelar pode ser sobrescrito pela task.

**Nuance de ORM nas views:** `queryset = Model.objects.all()` e `get_queryset()` de listagem/retrieve são o padrão **já exemplificado** em `regras-do-projeto.md`. Não gastar etapas movendo todo `get_queryset` para Helpers. **Sim** mover: persistência, regras de negócio, `exists()`/`create()`/`save()` em `do_action_*`, e chamadas `*.helper` / `*.rules` a partir da view.

**Stack de deploy atual:** `docker/Dockerfile` e `docker/docker-compose-production.yml` usam `runserver`; Gunicorn está em `requirements.txt` mas não é o CMD. `DEBUG` default `True`; `ALLOWED_HOSTS` default `*`; `debug_toolbar` sempre em `INSTALLED_APPS` + middleware + `debug_toolbar_urls()`. JWT access = **1 dia** (Swagger ainda diz 30 min). Sem `LOGGING`, sem `SECURE_*`.

---

## Decisões já tomadas (não reabrir nesta execução)

1. GET público das fotos (recurso e foto secundária) permanece `AllowAny`.
2. Capacidades de Infraestrutura (`operar` / `cadastrar` / `autorizar` / `retirada_irrestrita`) **não** se fundem com Cortex L1–L3.
3. Flag `usuario_coletivo` e o pool M2M só são **escritos** por L3 (`IsAdminMixin` / `EDITAR_TUDO`). L1/L2 não ligam a flag.
4. Access JWT: **30 minutos**. Refresh: **7 dias**. Rotação de refresh + blacklist após rotação.
5. Criação de usuário **via API** e importação em lote: política de senha **mantida como está** (senha padrão = CPF/matrícula quando `password` vazio). PREPROD-5 marcada desnecessária (2026-08-17).
6. `__init__.py` de pacotes AppCore permanece vazio (sem barrel). Import pelo módulo concreto.
7. Business: corpo inteiro em `try/except` + `relancar_ou_erro_sistema`. Não expor `str(e)` de erro interno ao cliente.
8. Setor **pode** existir sem responsável no momento da criação do setor (fluxo atual: cria setor, depois vínculos). A invariante “sempre um responsável” vale ao **remover** o último responsável — não exigir responsável no `POST` de setor. Atualizar a doc na etapa de documentação, não mudar o fluxo.
9. Terceirizado **pode** ter `Cargo` (FK opcional no código). A frase “terceirizados não possuem Cargo” em `04-aggregates-and-invariants.md` está errada — corrigir a **doc**, não remover o campo.

---

## Progresso

Ordem sugerida (dependências na coluna “Depende”). Pode pular a ordem se a etapa estiver `Pendente` e os pré-requisitos já estiverem `Concluída` ou `Desnecessária`.

| ID | Título | Severidade | Depende | Status |
|----|--------|------------|---------|--------|
| PREPROD-1 | Corrigir GET detalhe de empréstimo (500) | Crítico | — | Concluída (2026-08-17) |
| PREPROD-2 | Impedir L1/L2 de ligar `usuario_coletivo` | Crítico | — | Concluída (2026-08-17) |
| PREPROD-3 | Corrigir filtro `tipo_perfil` (tupla) | Importante | — | Concluída (2026-08-17) |
| PREPROD-4 | Corrigir `SetorVinculo.__str__` | Importante | — | Concluída (2026-08-17) |
| PREPROD-5 | Senha obrigatória na API; importação sem senha=CPF | Crítico | — | Desnecessária (2026-08-17) |
| PREPROD-6 | JWT 30 min + blacklist | Crítico | — | Concluída (2026-08-17) |
| PREPROD-7 | Settings/Docker de produção (DEBUG, Gunicorn, toolbar) | Crítico | — | Concluída (2026-08-17) |
| PREPROD-8 | Empréstimo: duplicatas, IntegrityError, lock, desativar recurso | Crítico | PREPROD-1 | Concluída (2026-08-17) |
| PREPROD-9 | Importação: business, lock, S3, cancelamento | Crítico | — | Pendente |
| PREPROD-10 | Unique global de matrícula + login | Importante | — | Pendente |
| PREPROD-11 | AlunoCurso: revalidar ativo no PATCH + unique parcial | Crítico | — | Pendente |
| PREPROD-12 | SetorVinculo: função NOT NULL + unique no banco | Importante | PREPROD-4 | Pendente |
| PREPROD-13 | Views de Infraestrutura/Identidade não chamam Helper/Rules | Importante | PREPROD-1, PREPROD-8 | Pendente |
| PREPROD-14 | `AlunoRules` em português (remover `can_*`) | Importante | — | Pendente |
| PREPROD-15 | Validar datas de terceirizado | Importante | — | Pendente |
| PREPROD-16 | `except Exception: pass` em serializer/permissions | Importante | — | Pendente |
| PREPROD-17 | Prefetch N+1 do pool coletivo | Sugestão | — | Pendente |
| PREPROD-18 | CORS, `EMAIL_USE_TLS`, `LOGGING`, `SECURE_*` | Importante | PREPROD-7 | Pendente |
| PREPROD-19 | Testes de lacuna (I.8, permissões, importação, auth) | Importante | PREPROD-1 a PREPROD-11 | Pendente |
| PREPROD-20 | Alinhar documentação com o código | Importante | PREPROD-6, PREPROD-11, PREPROD-12 | Pendente |
| PREPROD-21 | Rate-limit no login (ops/nginx ou lib) | Sugestão | PREPROD-6 | Pendente |

**Paralelizáveis sem conflito de arquivo (enquanto 1–2 não estiverem em andamento no mesmo checkout):** 3, 4, 10, 14, 15, 17.  
**Melhor em sequência (go-live):** 1 → 2 → 6 → 7 → 8 → 9 → 11.

**Não ir para produção com usuários reais** enquanto PREPROD-1, 2, 6, 7, 8, 9 e 11 estiverem `Pendente`.

---

## PREPROD-1 — Corrigir GET detalhe de empréstimo (500)

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`BasicRetrieveAPIView.get` chama `validate_retrieve` **antes** de `self.object = self.get_object()`. `DetalheEmprestimoView.validate_retrieve` usa `self.object.rules.pode_consultar(...)` → `AttributeError` em **todo** GET de detalhe. A view também viola View → Business (chama Rules). Não há teste cobrindo `emprestimo-detail`.

### Arquivos

- `AppCore/basics/views/basic_views.py` (`BasicRetrieveAPIView.get`)
- `Infraestrutura/emprestimos/views.py` (`DetalheEmprestimoView`)
- `Infraestrutura/emprestimos/business.py` (método fino que chama a rule)
- `Infraestrutura/tests/test_emprestimos_views.py` (criar/estender)

### O que fazer

1. Em `BasicRetrieveAPIView.get`: obter o objeto **antes** do hook, no mesmo espírito de `BasicPatchAPIView` / `BasicPutAPIView`:
   - `try: self.object = self.get_object()` → `Http404` vira `NotFoundException`
   - depois `self.validate_retrieve(...)`
   - depois serializar `self.object`
2. Conferir que nenhum outro `validate_retrieve` no repo **dependia** de `self.object` ainda não existir (hoje só o de empréstimo usa `self.object` nesse hook). `validate_get` de listagens **não** muda.
3. Na view: o hook chama **Business**, não Rules:
   ```python
   def validate_retrieve(self, request, *args, **kwargs):
       self.object.business.verificar_consulta(request.user)
   ```
4. Em `EmprestimoBusiness.verificar_consulta`: `try` + `self.object_instance.rules.pode_consultar(usuario)` + `relancar_ou_erro_sistema`.
5. Não alterar a regra de quem pode ver (L1 só ativo próprio; quem tem `operar` vê qualquer).

### Critério de saída

- [x] `GET reverse('infraestrutura:emprestimo-detail')` não retorna 500.
- [x] L1: 200 no empréstimo **ativo próprio**; 403 no encerrado próprio e no ativo de outro.
- [x] Quem tem `operar`: 200 em qualquer empréstimo.
- [x] View não chama `.rules` nem `.helper`.

### Testes mínimos desta etapa

- `test_emprestimos_views.py`: os três casos L1 acima + operador 200.
- Não quebrar `test_emprestimos.py` (operações de negócio).

### Prompt curto

```text
Implemente SOMENTE PREPROD-1 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-2 — Impedir L1/L2 de ligar `usuario_coletivo`

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`AtualizarUsuarioView` é `IsOwnerOrAdminMixin` (dono ou L2 leitura / L3 escrita no objeto). `AtualizarUsuarioSerializer` inclui `usuario_coletivo`. `atualizar_dados` chama `definir_flag_coletivo`. Um L1 no próprio perfil (ou L2, se a permissão de objeto permitir escrita no próprio) vira conta coletiva sem ser admin. O pool continua L3, mas a flag abre o fluxo de guarita.

### Arquivos

- `Identidade/usuarios/serializers.py` (`AtualizarUsuarioSerializer`)
- `Identidade/usuarios/views.py` (`AtualizarUsuarioView` + `@extend_schema`)
- `Identidade/usuarios/business.py` (`atualizar_dados` / `definir_flag_coletivo` — defesa em profundidade)
- `Identidade/usuarios/rules.py` (opcional: `pode_alterar_flag_coletivo` só se L3)
- `Identidade/usuarios/documentacao.py` se o texto de permissão da flag mudar
- `Identidade/usuarios/tests/test_usuario_coletivo.py` e/ou `test_views.py`

### O que fazer

1. Remover `usuario_coletivo` de `AtualizarUsuarioSerializer`.
2. Atualizar description do PATCH: flag coletiva **não** se altera neste endpoint; usar criação (admin) ou um caminho L3 explícito.
3. Defesa no business: `definir_flag_coletivo` só via fluxos L3. Se `atualizar_dados` ainda receber a chave (payload antigo), ignorar ou `AuthorizationException` — preferir **não aceitar o campo** no serializer (400 do DRF).
4. Manter criação (`CriarUsuarioSerializer` + `IsAdminMixin`) e endpoints `/coletivo/` como estão (já L3).
5. Atualizar Swagger `**Permissões:**` do PATCH (L2 lê; escrita dono ou L3; campo coletivo fora).

### Critério de saída

- [x] L1 PATCH no próprio usuário com `usuario_coletivo: true` **não** altera a flag (campo ignorado/400).
- [x] L3 continua podendo criar usuário coletivo e configurar o pool.
- [x] Teste de regressão no arquivo de coletivo.

### Testes mínimos desta etapa

- L1 autenticado: PATCH `usuario_coletivo=true` no próprio pk → flag permanece `false` (ou 400).
- Admin: criação com `usuario_coletivo=true` continua 201.

### Prompt curto

```text
Implemente SOMENTE PREPROD-2 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-3 — Corrigir filtro `tipo_perfil` (tupla)

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

Em `ListarUsuariosView.get_queryset`:

```python
if tipo_perfil in ('aluno'):  # isto é: tipo_perfil in 'aluno'
```

`'a' in 'aluno'` é True (filtra errado). `'alunos'` (citado na description) não filtra. O mesmo vale para `terceirizado`/`servidor`.

### Arquivos

- `Identidade/usuarios/views.py` (`ListarUsuariosView`)
- `Identidade/usuarios/tests/test_filtro_perfil.py`

### O que fazer

1. Usar tuplas reais: `('aluno', 'alunos')`, `('terceirizado', 'terceirizados')`, `('servidor', 'servidores')`.
2. Alinhar `enum` do `@extend_schema` e a description (aceitar singular e plural).
3. Valores fora da lista: ignorar silenciosamente (padrão de query params do projeto).

### Critério de saída

- [x] `tipo_perfil=alunos` filtra alunos.
- [x] `tipo_perfil=a` **não** filtra como aluno.

### Testes mínimos desta etapa

- Estender `test_filtro_perfil.py`: plural `alunos` / `servidores` / `terceirizados`; valor lixo ignorado; substring `'a'` não reduz a alunos.

### Prompt curto

```text
Implemente SOMENTE PREPROD-3 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-4 — Corrigir `SetorVinculo.__str__`

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`return f'{self.usuario} — {self.setor} ({self.funcao.sigla})'` — `Funcao` não tem `sigla` (tem `papel_funcao`); `funcao` pode ser `null` até PREPROD-12. Quebra o Django admin.

### Arquivos

- `Organizacional/vinculos/models.py`

### O que fazer

1. Usar `papel_funcao` com guarda se `funcao` for `None`.
2. Não alterar regras de negócio.

### Critério de saída

- [x] `str(vinculo)` não levanta `AttributeError` com função nula ou preenchida.

### Testes mínimos desta etapa

- Unidade curta no teste de vínculos (criar vínculo e chamar `str`), ou teste de admin se já existir.

### Prompt curto

```text
Implemente SOMENTE PREPROD-4 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-5 — Senha obrigatória na API; importação sem senha=CPF

| | |
|--|--|
| **Status** | Desnecessária (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

**Motivo:** a política de senha vigente (CPF/matrícula quando `password` vazio na API e na importação) **permanece**. Não implementar obrigatoriedade de senha forte nem geração aleatória na importação.

### Por quê

`criar_usuario` e a importação usam CPF/matrícula como senha se `password` vier vazio. CPF é o identificador de login → senha previsível. `validate_password` do serializer só roda se o campo for enviado. `AUTH_PASSWORD_VALIDATORS` do Django **não** são aplicados em `create_user` deste projeto.

**Decisão travada:** API de criação exige senha forte. Importação gera senha aleatória que passa na mesma política; não devolve a senha na resposta.

### Arquivos

- `Identidade/usuarios/serializers.py` (`CriarUsuarioSerializer`: `password` required)
- `Identidade/usuarios/business.py` (`criar_usuario`, `_criar_ou_atualizar_usuario` / trecho de senha da importação ~712)
- `AppCore/common/util/util.py` (`validar_senha`) — reutilizar no business da importação
- Testes: `Identidade/usuarios/tests/test_views.py`, `test_usuario_coletivo.py`, testes de importação

### O que fazer

1. `CriarUsuarioSerializer.password`: `required=True` (manter `write_only` e `validate_password`).
2. `criar_usuario`: se `password` ausente, `ValidationException` (não cair para CPF). Ainda assim validar complexidade no business se a chamada não vier do serializer (admin/shell).
3. Importação: gerar senha aleatória (ex. `secrets`) que cumpra maiúscula, minúscula, dígito, especial, ≥8; `set_password`; **nunca** logar nem gravar a senha em `resultado_json`.
4. Atualizar testes que criavam usuário via API sem senha (coletivo, etc.).
5. Swagger da criação: senha obrigatória.

Não implementar reset por e-mail nesta etapa (PREPROD-21 / futuro).

### Critério de saída

- [ ] POST criar usuário sem `password` → 400.
- [ ] POST com senha `12345678901` (CPF) → 400 pela política.
- [ ] Importação não grava senha = CPF; usuários importados têm hash que não é o CPF.

### Testes mínimos desta etapa

- API: 400 sem senha; 400 senha fraca; 201 senha forte.
- Coletivo: testes de criação passam a enviar senha válida.
- Importação (se houver teste de `create_user`): mock/assert de que a senha usada não é o CPF da linha.

### Prompt curto

```text
Implemente SOMENTE PREPROD-5 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-6 — JWT 30 min + blacklist

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`ACCESS_TOKEN_LIFETIME = timedelta(days=1)` e `BLACKLIST_AFTER_ROTATION = False`. Token roubado vale 24 h; logout/refresh não invalida. Swagger (`LoginResponseSerializer`, `LoginView`) já fala em 30 min.

### Arquivos

- `Cortex/rest_framework_settings.py`
- `Cortex/settings.py` (`INSTALLED_APPS`: `rest_framework_simplejwt.token_blacklist`)
- `Auth/auth/serializers.py` / `Auth/auth/views.py` (alinhar texto se ainda divergir)
- Migration do blacklist (app SimpleJWT)

### O que fazer

1. `ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)`.
2. `REFRESH_TOKEN_LIFETIME` permanece 7 dias.
3. `ROTATE_REFRESH_TOKENS = True` e `BLACKLIST_AFTER_ROTATION = True`.
4. Incluir `rest_framework_simplejwt.token_blacklist` em `INSTALLED_APPS` (não no AppCore).
5. Rodar `makemigrations`/`migrate` do app de blacklist (é app de terceiros — só `migrate`).
6. Confirmar que o refresh view do AppCore continua funcionando com rotação.

Não implementar endpoint de logout nesta etapa, a menos que já exista gancho trivial no SimpleJWT (`TokenBlacklistView`). Se adicionar logout, usar BasicPost + `AllowAny`/`IsAuthenticated` conforme o padrão SimpleJWT, com `@extend_schema` e `name=` na URL.

### Critério de saída

- [x] Settings: access 30 min; blacklist após rotação ligado.
- [x] App `token_blacklist` instalado; `migrate` aplica.
- [x] Texto Swagger de login = 30 min / 7 dias (já deve bater).

### Testes mínimos desta etapa

- Login + refresh existentes em `Identidade/usuarios/tests/test_views.py` continuam 200.
- Se houver logout: refresh antigo após rotate → 401.

### Prompt curto

```text
Implemente SOMENTE PREPROD-6 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-7 — Settings/Docker de produção

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`DEBUG` default `'True'`; `ALLOWED_HOSTS` default `'*'`; senha DB default `cortex`; `debug_toolbar` sempre no middleware e em `Cortex/urls.py`; Dockerfile e `docker-compose-production.yml` usam `runserver` e expõem Postgres/Redis no host; compose de “produção” monta `.:/app` como dev.

### Arquivos

- `Cortex/settings.py`
- `Cortex/urls.py`
- `docker/Dockerfile`
- `docker/docker-compose-production.yml`
- `.env.example` (documentar vars obrigatórias de prod, sem secretos reais)

### O que fazer

1. Manter `DEBUG` derivado de `DJANGO_DEBUG` (dev local pode ser True). Em **compose de produção**, `DJANGO_DEBUG=False` obrigatório no exemplo.
2. Se `DEBUG=False`: `ALLOWED_HOSTS` não pode ser `['*']` — `ImproperlyConfigured` se vazio ou `*`.
3. `debug_toolbar`: só em `INSTALLED_APPS` / middleware / `debug_toolbar_urls()` quando `DEBUG` é True.
4. Dockerfile: `CMD` Gunicorn, por exemplo `gunicorn Cortex.wsgi:application --bind 0.0.0.0:8000 --workers 3` (já está em `requirements.txt`).
5. `docker-compose-production.yml`: **não** usar `runserver`; **não** montar o código-fonte; **não** publicar `5432`/`6379` no host (só rede interna). `migrate` pode ficar no entrypoint/command uma vez.
6. Não commitar `media/importacoes/` (já no `.gitignore`).
7. Não alterar o compose de **dev** (`docker-compose.yml` com debugpy) nesta etapa, salvo se compartilhar o mesmo Dockerfile CMD — nesse caso o compose de dev deve **sobrescrever** o command para `runserver`/debugpy.

### Critério de saída

- [x] `DEBUG=False` + `ALLOWED_HOSTS=*` recusa subir.
- [x] Toolbar ausente quando `DEBUG=False`.
- [x] Imagem de produção não inicia `runserver`.
- [x] Compose production não publica portas do banco/redis.

### Testes mínimos desta etapa

- Não há teste Django para Docker. Verificar manualmente: `grep runserver docker/docker-compose-production.yml` vazio; settings com `DEBUG=False` não inclui toolbar. Se existir teste de `ImproperlyConfigured` de `SECRET_KEY`, espelhar para `ALLOWED_HOSTS`.

### Prompt curto

```text
Implemente SOMENTE PREPROD-7 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-8 — Empréstimo: duplicatas, IntegrityError, lock, desativar recurso

| | |
|--|--|
| **Status** | Concluída (2026-08-17) |
| **Severidade** | Crítico |
| **Pré-requisito** | PREPROD-1 (detalhe e business de consulta já no lugar) |
| **Quem / onde** | |

### Por quê

`validar_recursos_informados` compara `len(ids_encontrados)` com `len(set(recurso_ids))` — `[1,1]` passa e o segundo insert estoura a unique → 500. Corrida entre dois operadores: check-then-act sem `select_for_update`; `IntegrityError` vira `SystemErrorException`. `RecursoRules.pode_desativar` não olha item em aberto.

### Arquivos

- `Infraestrutura/emprestimos/rules.py`
- `Infraestrutura/emprestimos/business.py`
- `Infraestrutura/recursos/rules.py`
- `Infraestrutura/tests/test_emprestimos.py`
- `Infraestrutura/tests/test_cadastro_views.py` ou `test_emprestimos_views.py`

### O que fazer

1. Se `len(recurso_ids) != len(set(recurso_ids))` → `BusinessRuleException` / `return_exception` “IDs de recurso duplicados”.
2. Mesmo para `item_ids` em `validar_itens_para_devolucao`.
3. Em `realizar_emprestimo`: `Recurso.objects.select_for_update().filter(pk__in=...)` **dentro** do `try` (a view já abre `atomic`).
4. `except IntegrityError` **antes** do catch-all → `BusinessRuleException` amigável (“já possui empréstimo em aberto”), depois `relancar_ou_erro_sistema`.
5. `pode_desativar` do recurso: se `Emprestimo().helper.recurso_esta_emprestado(self.object_instance)` → não desativa.
6. Rules continuam sem persistência; query de “está emprestado” já está no helper — **Business** pode chamar helper, ou a rule continua chamando helper (hoje já chama). Nesta etapa **não** refatore rules→helper (isso é PREPROD-13); só acrescente a checagem.

### Critério de saída

- [x] `recurso_ids=[1,1]` → 400, não 500.
- [x] Segundo empréstimo no mesmo recurso (corrida ou sequencial) → 400 com mensagem de negócio, não 500.
- [x] Desativar recurso com item aberto → 400.

### Testes mínimos desta etapa

- Duplicata na API e/ou no business.
- Recurso já emprestado (já existe teste de duplo — garantir que não é 500).
- Desativar recurso emprestado.

### Prompt curto

```text
Implemente SOMENTE PREPROD-8 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-9 — Importação: business, lock, S3, cancelamento

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`PreVisualizarImportacaoUsuariosView`, `ImportarUsuariosLoteView`, `CancelarImportacaoView` e `StatusImportacaoLoteView` fazem ORM, `ValidationError`/`Http404` do DRF, `transaction.on_commit` e upload S3 na **view**. Upload S3 retorna `False` e a view responde 202 mesmo assim. Duas requisições passam no `exists()` de `EM_ANDAMENTO`. A task grava `CONCLUIDA` mesmo após cancelar (checagem só a cada 10 linhas). `str(exc)` vai para `erro_fatal`.

### Arquivos

- `Identidade/usuarios/views.py` (views de importação)
- `Identidade/usuarios/business.py` (novos métodos no `UsuarioBusiness` **ou** business de `ImportacaoLote` se o model ganhar mixin — preferir métodos em `UsuarioBusiness` / instância `ImportacaoLote` se já tiver business; hoje o lote é model auxiliar no mesmo app)
- `Identidade/usuarios/models.py` (`ImportacaoLote`)
- `Identidade/usuarios/tasks.py`
- `Identidade/usuarios/importacao/s3_helper.py`
- Testes de importação em `Identidade/usuarios/tests/`

### O que fazer

1. View só: `Usuario().business.iniciar_importacao(arquivo=...)`, `cancelar_importacoes_em_andamento()`, `obter_status_recente()`, `pre_visualizar_importacao` (já existe). Sem `ImportacaoLote.objects` na view.
2. Exceções AppCore (`ValidationException`, `NotFoundException`), não `rest_framework.exceptions.ValidationError` / `Http404`.
3. Lock: `select_for_update` na linha `EM_ANDAMENTO` **ou** `UniqueConstraint` parcial `status=EM_ANDAMENTO` (migration segura). Preferir constraint + tratamento de `IntegrityError` → 400 “já existe importação em andamento”.
4. Upload S3: se falhar, não enfileirar Celery; marcar lote `ERRO` ou nem criar; resposta 500 genérica / `SystemErrorException` (não 202).
5. `transaction.on_commit(task)` permanece **dentro do business** (não na view). A BasicView já envolve `do_action_post` em `atomic` — `on_commit` no business dispara no commit da view. Não abrir segundo `atomic` desnecessário.
6. Task: se `status != EM_ANDAMENTO` no início **e** imediatamente antes do `save` final, abortar sem sobrescrever `ERRO` de cancelamento. Checar cancelamento a cada linha (não só a cada 10).
7. `erro_fatal`: mensagem fixa ao cliente/admin (`'Falha interna na importação.'`); detalhe só no `logger.exception`.
8. `StatusImportacaoLoteView`: voltar ao envelope `{status, mensagem, dados}` da BasicGet, se possível, em vez de serializer cru.
9. Tirar `from rest_framework import parsers` do meio do `views.py` (import no topo).

### Critério de saída

- [ ] Nenhuma view de importação faz `.objects.create` / `.save` / `transaction.on_commit`.
- [ ] Falha de S3 não retorna 202 com task enfileirada.
- [ ] Cancelar + task lenta não vira `CONCLUIDA`.
- [ ] Segunda importação paralela → 400.

### Testes mínimos desta etapa

- Já existem `CancelarImportacaoViewTests` (`TestCase` — nesta etapa pode permanecer; PREPROD-19 troca para `APITestCase`).
- Novo: mock S3 `False` → não 202; status após cancel + save da task permanece `ERRO`.

### Prompt curto

```text
Implemente SOMENTE PREPROD-9 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-10 — Unique global de matrícula + login

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum (migration: skill `django-safe-migration`) |
| **Quem / onde** | |

### Por quê

`Matricula.matricula` não é unique. Login por matrícula usa `.first()` (`AppCore/basics/auth/backends.py`). Duplicatas escolhem um usuário ao acaso. `criar_usuario` já valida unicidade global; `adicionar_matricula` / importação não necessariamente.

### Arquivos

- `Identidade/matriculas/models.py`
- `Identidade/matriculas/rules.py` e/ou `Identidade/usuarios/rules.py` (`matricula_nao_duplicada` hoje é por usuário)
- `Identidade/usuarios/business.py` (`adicionar_matricula`, importação)
- Migration nova
- `AppCore/basics/auth/backends.py` (`.get()` em vez de `.first()`, tratando múltiplos como falha de login genérica)
- Testes de matrícula e login por matrícula

### O que fazer

1. `UniqueConstraint` em `matricula` (valor da string). Antes: data migration que reporta/impede duplicatas existentes (fail a migration se houver duplicata, com mensagem clara).
2. Rules: unicidade **global**, não só no mesmo usuário.
3. Backend: se 0 matches → None; se 2+ (não deveria após unique) → None + log, sem vazar qual usuário.
4. Unificar criação API, `adicionar_matricula` e importação.

### Critério de saída

- [ ] Segunda matrícula com o mesmo número (outro usuário) → 400.
- [ ] Login por matrícula continua 200 no caso feliz.
- [ ] Migration recusa ambiente com duplicatas.

### Testes mínimos desta etapa

- `Identidade/matriculas/tests/test_views.py`: duplicata global 400.
- Login por matrícula existente continua passando.

### Prompt curto

```text
Implemente SOMENTE PREPROD-10 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-11 — AlunoCurso: revalidar ativo no PATCH + unique parcial

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Crítico |
| **Pré-requisito** | Nenhum (migration: skill `django-safe-migration`) |
| **Quem / onde** | |

### Por quê

`vinculo_unico_ativo` só na criação. `atualizar_dados` faz `setattr` + `save` e o serializer de PATCH expõe `ativo`. Dá para reativar um vínculo encerrado com outro ainda ativo para o mesmo par aluno+curso.

### Arquivos

- `Academico/aluno_cursos/business.py`
- `Academico/aluno_cursos/rules.py` (`vinculo_unico_ativo` com `excluir_id`)
- `Academico/aluno_cursos/models.py` + migration (`UniqueConstraint` condicional `ativo=True` em `aluno`+`curso`)
- `Academico/aluno_cursos/tests/test_aluno_cursos.py`

### O que fazer

1. Em `atualizar_dados`, se `ativo` for True (ou o registro ficar ativo), chamar `vinculo_unico_ativo(..., excluir_id=pk)`.
2. Unique parcial no PostgreSQL: um ativo por `(aluno, curso)`.
3. `IntegrityError` → `ValidationException` / `BusinessRuleException` amigável, não 500.
4. `encerrar` permanece o caminho oficial para `ativo=False`.

### Critério de saída

- [ ] PATCH `ativo=true` com outro vínculo ativo do mesmo par → 400.
- [ ] Banco recusa o mesmo estado mesmo via ORM/admin.

### Testes mínimos desta etapa

- Já há teste de duplicidade na **criação**; acrescentar PATCH de reativação.

### Prompt curto

```text
Implemente SOMENTE PREPROD-11 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-12 — SetorVinculo: função NOT NULL + unique no banco

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | PREPROD-4; migration: skill `django-safe-migration` |
| **Quem / onde** | |

### Por quê

Invariante (`04-aggregates-and-invariants.md`): vínculo **sempre** tem função. O model tem `null=True`. Unicidade `(usuario, setor, funcao)` só em Python → corrida duplica. **Não** exigir responsável na criação do setor (decisão 9).

### Arquivos

- `Organizacional/vinculos/models.py`
- `Organizacional/vinculos/rules.py` (já tem `vinculo_sem_duplicata`)
- Migration (backfill se existirem `funcao_id` nulos — falhar se não der para preencher)
- Testes de vínculos

### O que fazer

1. Inventário: se houver `funcao` nula em prod/dev, parar e documentar; não inventar função.
2. `null=False`, `blank=False` no FK.
3. `UniqueConstraint` em `(usuario, setor, funcao)`.
4. `IntegrityError` no `criar_vinculo` → mensagem da rule, não 500.

### Critério de saída

- [ ] ORM não aceita vínculo sem função.
- [ ] Duplicata (usuario, setor, funcao) → 400.

### Testes mínimos desta etapa

- `Organizacional/vinculos/tests/test_views.py`: duplicata já coberta em regra; garantir 400 e não 500.

### Prompt curto

```text
Implemente SOMENTE PREPROD-12 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-13 — Views não chamam Helper/Rules

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | PREPROD-1, PREPROD-8 |
| **Quem / onde** | |

### Por quê

Hierarquia obrigatória: View → Business → Rules/Helpers. Hoje:

- `Infraestrutura/emprestimos/views.py`: funções de módulo `queryset_emprestimo_detalhado`, `_extrair_ids_recursos_da_query`; `Emprestimo().helper.*`; `Usuario().helper.listar_responsaveis_do_coletivo`
- `Infraestrutura/autorizacoes/views.py`: `queryset_autorizacao_detalhado`; `Autorizacao().helper.listar_para_filtros`
- `Identidade/usuarios/views.py` ~319: `instance.helper.obter_configuracao_coletivo()` em `get_serializer`

Rules de empréstimo/autorização/usuário que chamam `.helper` **podem** permanecer nesta etapa ou ganhar um método de business que a rule deixe de orquestrar. Prioridade: **tirar Helper/Rules da view**. Refatorar rules→helper só se for barato no mesmo PR; senão deixar registrado na etapa como “ainda há rules→helper, aceitável até um PREPROD futuro”.

### Arquivos

- `Infraestrutura/emprestimos/views.py`, `helpers.py`, `business.py`
- `Infraestrutura/autorizacoes/views.py`, `helpers.py`, `business.py`
- `Identidade/usuarios/views.py`, `business.py`
- Testes de views de empréstimo/autorização/coletivo

### O que fazer

1. Mover funções soltas para `helpers.py` (classe `EmprestimoHelpers` / `AutorizacaoHelpers`).
2. Business expõe `listar_solicitantes_elegiveis_para_recursos`, `listar_para_usuario`, `listar_para_filtros`, `obter_configuracao_coletivo` com try/except.
3. `get_queryset` das views chama `Emprestimo().business....` / `Autorizacao().business....` (criação sem pk usa `Model().business` — padrão do projeto).
4. `ObterUsuarioColetivoView`: `get_serializer` não chama helper; o business devolve o DTO/dict e a view só serializa, **ou** o serializer lê campos já anotados.

Não reescrever todos os `queryset = Bloco.objects.all()` do cadastro.

### Critério de saída

- [ ] `rg "\.helper\.|\.rules\." Infraestrutura/**/views.py Identidade/usuarios/views.py` sem hits de domínio (exceto comentários).
- [ ] Sem `def queryset_*` / `def _extrair_*` no módulo de views.

### Testes mínimos desta etapa

- Views de listagem de empréstimo, solicitantes, responsáveis, autorizações e GET coletivo continuam 200 nos testes existentes.

### Prompt curto

```text
Implemente SOMENTE PREPROD-13 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-14 — `AlunoRules` em português

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`can_create` / `can_update` / `can_delete` retornam `True` e nunca lançam. Violam nomenclatura e o contrato de Rules. `AlunoBusiness.criar_aluno` chama `can_create()` — código morto.

### Arquivos

- `Academico/alunos/rules.py`
- `Academico/alunos/business.py`

### O que fazer

1. Remover os três `can_*`.
2. Tirar a chamada em `criar_aluno` (a unicidade OneToOne já é checada no business).
3. Não inventar regras acadêmicas (IRA, situação) nesta etapa.

### Critério de saída

- [ ] Nenhum `def can_` em `Academico/**/rules.py`.
- [ ] Criar aluno continua 201 nos testes.

### Testes mínimos desta etapa

- `Academico/alunos/tests/test_alunos.py` intactos.

### Prompt curto

```text
Implemente SOMENTE PREPROD-14 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-15 — Validar datas de terceirizado

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`data_inicio` / `data_fim` existem; serializer exige início na criação; **não** há rule para `data_fim < data_inicio`. Flag `ativo` é independente das datas.

### Arquivos

- `PessoasInstitucionais/terceirizados/rules.py`
- `PessoasInstitucionais/terceirizados/business.py`
- `PessoasInstitucionais/terceirizados/tests/test_terceirizados.py`

### O que fazer

1. `validar_vigencia(data_inicio, data_fim)`: se `data_fim` informada e `< data_inicio` → exceção.
2. Chamar na criação e no `atualizar_dados`.
3. Não auto-desativar por `data_fim` no passado nesta etapa (isso seria job/Celery — fora de escopo).

### Critério de saída

- [ ] Criação/PATCH com fim antes do início → 400.

### Testes mínimos desta etapa

- Caso 400 nas views/business de terceirizado.

### Prompt curto

```text
Implemente SOMENTE PREPROD-15 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-16 — `except Exception: pass` em serializer/permissions

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`UsuarioSerializer.get_servidor` / `get_terceirizado` / `get_vinculos` e `UsuarioPermissions.permissoes_cortex` engolem qualquer exceção → L1 indevido ou perfil `null` em erro de DB.

### Arquivos

- `Identidade/usuarios/serializers.py`
- `Identidade/usuarios/permissions.py`

### O que fazer

1. Capturar só `ObjectDoesNotExist` / related OneToOne ausente (ou `getattr`/`hasattr` sem `except Exception`).
2. Não mascarar erro de banco.

### Critério de saída

- [ ] Nenhum `except Exception: pass` nesses dois arquivos.
- [ ] Listagem de usuário sem servidor continua com `servidor: null`.

### Testes mínimos desta etapa

- Testes de perfil institucional / serializer existentes.

### Prompt curto

```text
Implemente SOMENTE PREPROD-16 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-17 — Prefetch N+1 do pool coletivo

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Sugestão |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`queryset_usuario_com_perfis` não faz prefetch de `empresas_coletivo`, `cargos_coletivo`, `funcoes_coletivo`, `setores_coletivo`. `UsuarioSerializer` consulta os quatro M2M por linha.

### Arquivos

- `Identidade/usuarios/querysets.py`
- Teste de listagem (opcional `assertNumQueries` folgado)

### O que fazer

1. `prefetch_related` dos quatro M2M no queryset base de listagem/detalhe.

### Critério de saída

- [ ] Listagem não dispara 4 queries extras por usuário para os IDs do pool.

### Testes mínimos desta etapa

- Listagem de usuários (admin) continua 200. `assertNumQueries` só se for estável.

### Prompt curto

```text
Implemente SOMENTE PREPROD-17 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-18 — CORS, `EMAIL_USE_TLS`, `LOGGING`, `SECURE_*`

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | PREPROD-7 |
| **Quem / onde** | |

### Por quê

`CorsMiddleware` está depois de `CommonMiddleware`. `EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", True)` trata `"False"` como True. Não há `LOGGING`. Sem `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_SSL_REDIRECT` / HSTS quando `DEBUG=False` (admin Django usa sessão).

### Arquivos

- `Cortex/settings.py`
- `.env.example`

### O que fazer

1. Ordem: `SecurityMiddleware` → `WhiteNoise` → `CorsMiddleware` → Session → Common → CSRF → Auth → …
2. Parse booleano de env (`'true'/'1'/'yes'` vs `'false'/'0'/'no'`) para `EMAIL_USE_TLS` (e `EMAIL_PORT` como `int`).
3. `LOGGING` mínimo: console + arquivo opcional; `INFO` em prod, `DEBUG` se `DEBUG=True`; loggers `Identidade`, `Infraestrutura`, `celery`.
4. Se `DEBUG=False`: `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_SSL_REDIRECT` via env (`DJANGO_SECURE_SSL_REDIRECT`, default True em prod). HSTS só se o TLS terminar no Django ou o proxy estiver documentado (`SECURE_PROXY_SSL_HEADER` se houver).
5. Aspas simples no que for tocado neste arquivo (convenção do projeto).

Não adicionar Sentry nesta etapa (ops externo).

### Critério de saída

- [ ] `"False"` em `EMAIL_USE_TLS` desliga TLS.
- [ ] CORS antes de `CommonMiddleware`.
- [ ] `LOGGING` definido.
- [ ] Cookies secure quando `DEBUG=False`.

### Testes mínimos desta etapa

- Nenhum obrigatório. Smoke: `DEBUG=False` carrega settings sem exceção com `ALLOWED_HOSTS` e `SECRET_KEY` válidos.

### Prompt curto

```text
Implemente SOMENTE PREPROD-18 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-19 — Testes de lacuna

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | PREPROD-1 a PREPROD-11 (comportamentos já corrigidos) |
| **Quem / onde** | |

### Por quê

A revisão listou buracos: detalhe L1 de empréstimo (coberto em PREPROD-1, conferir); `retirada_irrestrita`; autorização expirada no fluxo de `realizar_emprestimo`; filtros L2; CRUD salas/salas-setores; login por e-mail; status/histórico de importação; L1/L2 em servidores/alunos; classes `TestCase` em vez de `APITestCase`.

### Arquivos

- `Infraestrutura/tests/test_emprestimos.py`
- `Infraestrutura/tests/test_emprestimos_views.py`
- `Infraestrutura/tests/test_cadastro_views.py`
- `Identidade/usuarios/tests/test_views.py` (trocar `TestCase` de importação por `APITestCase` onde for teste de API)
- `PessoasInstitucionais/*/tests/`
- `Academico/alunos/tests/test_alunos.py`

### O que fazer

Cobrir pelo menos:

1. `retirada_irrestrita` permite empréstimo sem ser servidor/autorização pontual.
2. Autorização **expirada** e **futura** bloqueiam `realizar_emprestimo`.
3. Filtros L2 de listagem de empréstimo (`ativo`, `solicitante_id`, …) só reduzem conjunto.
4. CRUD mínimo de salas e salas-setores + 403 L1.
5. Login por e-mail 200.
6. GET status e histórico de importação 200 (admin).
7. Um 403 L1 em `POST` servidores e em `POST` alunos.
8. Testes de **API** herdam `APITestCase` (parser/business unitários podem permanecer `TestCase` se não usam `self.client` — a regra do projeto pede `APITestCase` em todas as classes; cumprir nos que batem na API; nos de parser, herdar `APITestCase` mesmo sem cliente, para padronizar).

Não exigir teste de corrida multithread (frágil); o 400 de IntegrityError em PREPROD-8 basta.

### Critério de saída

- [ ] Os cenários 1–7 existem e passam.
- [ ] `python manage.py test` da suíte afetada verde.

### Testes mínimos desta etapa

- Esta etapa **é** a de testes.

### Prompt curto

```text
Implemente SOMENTE PREPROD-19 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-20 — Alinhar documentação com o código

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | PREPROD-6, PREPROD-11, PREPROD-12 |
| **Quem / onde** | |

### Por quê

`regras-do-projeto.md` ainda marca Cargo/Servidor/Aluno como “planejado”, cita `BaseManager.filter(ativo=True)` (o código **não** filtra mais), JWT 30 min vs settings (após PREPROD-6 deve bater), `create_app.py` vazio. `04-aggregates-and-invariants.md` diz que terceirizado não tem Cargo e que todo setor já nasce com responsável. Swagger de detalhe de usuário diz “próprio ou admin” mas L2 lê. `identidade.md` mistura “login só CPF” com e-mail/matrícula.

### Arquivos

- `docs/project/regras-do-projeto.md` (tabela de models + parágrafo do BaseManager + JWT)
- `docs/diagrams/04-aggregates-and-invariants.md`
- `docs/domains/identidade.md`
- `docs/project/django-project-tree.md` se ainda desatualizado
- `Identidade/usuarios/views.py` (bloco `**Permissões:**` de detalhe/PATCH)
- `Identidade/usuarios/documentacao.py` se o texto L2 de leitura estiver errado
- Este README de docs (link deste follow-up — se ainda não estiver)

### O que fazer

1. Marcar milestones 3–4 e Infraestrutura como implementados na tabela de models.
2. BaseManager: só `get()` → `NotFoundException`; `.filter()` **não** força `ativo=True`.
3. JWT: 30 min / 7 dias (após PREPROD-6).
4. Terceirizado: Cargo opcional.
5. Setor: responsável obrigatório ao **remover o último**, não na criação do setor.
6. Login: e-mail **ou** CPF **ou** matrícula ativa.
7. Detalhe usuário: L2+ lê; escrita dono ou L3.
8. Não reescrever o guia inteiro.

### Critério de saída

- [ ] Nenhum “🔜 Planejado” para apps que já existem em `PROJECT_APPS`.
- [ ] BaseManager documentado como o código.
- [ ] `@extend_schema` de detalhe de usuário menciona L2.

### Testes mínimos desta etapa

- Nenhum. Revisão humana do diff de docs.

### Prompt curto

```text
Implemente SOMENTE PREPROD-20 de docs/planning/followup-revisao-pre-producao.md
```

---

## PREPROD-21 — Rate-limit no login

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Sugestão |
| **Pré-requisito** | PREPROD-6 |
| **Quem / onde** | |

### Por quê

Sem limite, credential stuffing no `POST /cortex/auth/token_jwt/` é barato (ainda mais se algum fluxo legado tiver senha previsível).

### Arquivos

- Ops (nginx / API gateway) **ou** dependência nova no Django — **perguntar** se ainda não estiver decidido. Preferir nginx/`limit_req` na frente do Gunicorn para não colocar regra de infra no AppCore.
- Se for no Django: documentar a lib e aplicar só na `LoginView`, sem inventar captcha.

### O que fazer

1. Se a decisão for nginx: documentar trecho em `docs/project/` ou neste arquivo (Adiada com motivo “feito no proxy”).
2. Se for Django: implementar com a lib escolhida pelo usuário; testes de 429 após N falhas.

### Critério de saída

- [ ] Login tem limite documentado e ativo em produção (proxy **ou** app).

### Testes mínimos desta etapa

- Só se o limite for no Django: 429 após o teto.

### Prompt curto

```text
Implemente SOMENTE PREPROD-21 de docs/planning/followup-revisao-pre-producao.md
```

Se a etapa for só documentação de nginx, o prompt é o mesmo: não adicionar lib sem o usuário escolher a opção A (proxy) ou B (Django).

---

## Itens conscientemente fora do plano (não criar etapa)

- Refatorar **todas** as listagens para tirar `Model.objects` de `get_queryset` (padrão exemplificado nas regras).
- Reset de senha por e-mail / first-login obrigatório (produto; mitiga senha padrão = CPF/matrícula).
- Login social Google (comentado de propósito).
- Máquina de estados (`state.py`) — ainda “futuro” nas regras.
- Remover migrations históricas `emprestimos/0002` e `0004` (cargo servente) — débito; não reescrever histórico.
- Teste de corrida com threads no empréstimo.
- Sentry / APM.
- Alterar política `AllowAny` das fotos.

---

## Checklist rápido do implementador (toda etapa)

1. Ler a etapa inteira + arquivos listados.
2. Seguir Models → Rules → Helpers → Business → Serializers → Views → URLs → Testes, só o que a etapa pedir.
3. `relancar_ou_erro_sistema` em método novo/alterado de business.
4. `@extend_schema` com `**Permissões:**` se a view mudar.
5. Testes com `reverse('namespace:name')`.
6. Marcar status + data **neste arquivo**.
