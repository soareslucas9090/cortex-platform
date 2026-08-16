# Follow-up — Revisão de fotos S3 (recursos + AppCore)

Plano **rastreável e reutilizável** para corrigir os 9 achados da revisão de código da branch `feat/imagens-recursos` contra a `main`.

Cada etapa é independente o bastante para ser feita **sozinha**, em outro dia, em outro computador, numa conversa nova com a IA.

**Origem:** revisão de código (skill `revisao-codigo`) em 16/08/2026.  
**Fontes de padrão:** [regras-do-projeto.md](../project/regras-do-projeto.md), [guia-implementacao.md](../project/guia-implementacao.md), [guia-revisao-de-codigo.md](../project/guia-revisao-de-codigo.md), [schema infraestrutura](../schema/infraestrutura.md), [domínio identidade](../domains/identidade.md).  
**Skill de implementação:** `.agents/skills/implementacao/SKILL.md`.  
**Migrations:** se a etapa gerar/alterar migration, usar a skill `django-safe-migration`.

---

## Como retomar (obrigatório em conversa nova)

Cole isto no chat (troque o ID):

```text
Implemente SOMENTE a etapa FOTO-S3-N de docs/planning/followup-revisao-fotos-s3.md.

Regras:
- Leia essa etapa por completo antes de editar.
- Não avance para outras etapas.
- Siga docs/project/regras-do-projeto.md e docs/project/guia-implementacao.md.
- Ao terminar: (1) rode os testes citados na etapa; (2) marque a etapa como Concluída neste arquivo (status + data); (3) atualize a tabela de progresso.
```

Para só inspecionar o que falta, sem implementar:

```text
Qual é a próxima etapa pendente em docs/planning/followup-revisao-fotos-s3.md? Resuma o que falta e a ordem sugerida.
```

### Convenção de status

| Valor | Significado |
|-------|-------------|
| `Pendente` | Ainda não começou |
| `Em andamento` | Alguém está fazendo agora (preencher “Quem / onde”) |
| `Concluída (AAAA-MM-DD)` | Critério de saída atendido e testes da etapa ok |
| `Adiada` | Decidiu não fazer agora; escrever o motivo na etapa |

Marque **somente** a etapa que acabou de fechar. Não reescreva etapas já concluídas além do status.

---

## Progresso

Ordem sugerida (dependências na coluna “Depende”). Pode pular a ordem se a etapa estiver `Pendente` e os pré-requisitos já estiverem `Concluída`.

| ID | Título | Severidade | Depende | Status |
|----|--------|------------|---------|--------|
| FOTO-S3-1 | Restringir proxy S3 ao prefixo do anexo | Importante | — | Concluída (2026-08-16) |
| FOTO-S3-2 | Validar formato real da imagem (não só Content-Type) | Importante | — | Pendente |
| FOTO-S3-3 | Erro de config S3 não vira 400 de validação | Importante | — | Pendente |
| FOTO-S3-4 | Validar/processar foto **antes** do `create` do recurso | Importante | FOTO-S3-2 (recomendado) | Pendente |
| FOTO-S3-5 | Tirar ORM do hook `CriarRecursoView` | Importante | — | Pendente |
| FOTO-S3-6 | Atualizar `documentacao_infraestrutura()` | Importante | — | Pendente |
| FOTO-S3-7 | `@extend_schema` no `get` + `BasicRetrieveAPIView` no proxy | Importante | — | Pendente |
| FOTO-S3-8 | `URLField` → `CharField` para chave S3 | Sugestão | — | Pendente |
| FOTO-S3-9 | Testes que travam os itens 2–4 e lacunas de API | Sugestão | FOTO-S3-1 a FOTO-S3-4 (cenários novos); o resto pode entrar junto de cada etapa | Pendente |

**Paralelizáveis sem conflito de arquivo:** 1, 5, 6, 7, 8.  
**Melhor em sequência:** 2 → 3 → 4 → 9.

---

## Decisões já tomadas (não reabrir)

1. GET da foto do recurso (e da foto secundária do usuário) permanece **público** (`AllowAny`); o bucket S3 permanece privado.
2. Upload/remoção de foto de recurso exige capacidade `cadastrar`.
3. Foto do recurso: retrato obrigatório; recorte central 3:4; mínimo 480×640 após recorte; JPEG/PNG/WebP até 3 MB; armazenamento em `AppCore.common.storage`.
4. A API **não** devolve a chave crua do bucket; devolve a URL do proxy.
5. `__init__.py` de `AppCore.common.storage` permanece vazio; import pelo módulo concreto (`anexo`, `s3`, `imagens`).
6. Business: corpo inteiro em `try/except` + `relancar_ou_erro_sistema`. Não expor `str(e)` de erro interno ao cliente.

---

## FOTO-S3-1 — Restringir proxy S3 ao prefixo do anexo

| | |
|--|--|
| **Status** | Concluída (2026-08-16) |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | Implementação local / Cursor |

### Por quê

O GET da foto é anônimo. Hoje `AnexoS3.iterar` e `chave_normalizada` aceitam qualquer chave gravada no banco. A API atual não deixa o cliente gravar chave arbitrária, mas um PATCH futuro, shell ou bug transformaria o endpoint em proxy de **todo** o bucket.

### Arquivos

- `AppCore/common/storage/anexo.py` (principal)
- `AppCore/common/storage/s3.py` (`normalizar_chave_s3` / `iterar_objeto_s3` / `remover_objeto_s3` — só se o filtro ficar melhor no S3 do que no descritor)
- `Infraestrutura/recursos/business.py` (`obter_stream_foto`) — só se a exceção precisar ser `NotFoundException` aqui
- `Identidade/usuarios/business.py` (`obter_stream_foto_secundaria`) — o mesmo filtro vale para o proxy de usuário
- Testes: `Infraestrutura/tests/test_recurso_foto.py`; `Identidade/usuarios/tests/test_views.py` (foto secundária)

### O que fazer

1. Em `AnexoS3.iterar` (e de preferência em `chave_normalizada` / `remover`): se a chave normalizada **não** começar com `f'{self.prefixo}/'`, não chamar o S3.
2. Falha de prefixo = `NotFoundException` (404 genérico, sem vazar a chave). `anexo.py` hoje não importa exceções do AppCore — ou importa `NotFoundException`, ou devolve `None`/levanta `ValueError` e o **business** converte para `NotFoundException`. Preferir um único lugar, documentado no código.
3. Não alterar a política `AllowAny` do GET.

### Critério de saída

- [x] Chave fora do prefixo do anexo não dispara `get_object` no S3.
- [x] GET público de foto válida continua 200.
- [x] GET sem foto / recurso inexistente continua 404.
- [x] Remoção só tenta apagar objeto do próprio prefixo.

### Testes mínimos desta etapa

- Unidade (preferível em teste de storage ou business): chave `Cortex/outro/prefixo/x.jpg` → 404 / `NotFoundException`; mock de `iterar_objeto_s3` **não** chamado.
- Não quebrar `test_get_proxy_foto_sem_autenticacao` nem o proxy de foto secundária.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-1 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-2 — Validar formato real da imagem

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum (melhor antes de FOTO-S3-4) |
| **Quem / onde** | |

### Por quê

`validar_arquivo_foto` ignora o tipo se `content_type` vier vazio e confia no header se vier `image/jpeg`. GIF/BMP/TIFF forjado passa no `ImageField`, o Pillow abre, o recorte vira RGB e o S3 recebe JPEG. O schema exige JPEG, PNG ou WebP na **entrada**.

### Arquivos

- `AppCore/common/storage/imagens.py` (`abrir_imagem` e constantes de formato)
- `Infraestrutura/recursos/rules.py` (`validar_arquivo_foto`)
- `Identidade/usuarios/rules.py` (`validar_arquivo_foto`) — o mesmo furo existe na foto secundária; corrigir junto para não divergir
- Testes: `Infraestrutura/tests/test_recurso_foto.py`; testes de foto secundária em `Identidade/usuarios/tests/test_views.py`

### O que fazer

1. Checar o formato **real** do Pillow (`imagem.format in {'JPEG', 'PNG', 'WEBP'}`) **antes** de `convert('RGB')` — depois do convert o `format` some.
2. Rejeitar `content_type` vazio **ou** tratar ausência de content-type exigindo o formato PIL (não “passar se não veio header”).
3. Manter a mensagem já usada: `'Formato de imagem não suportado. Use JPEG, PNG ou WebP.'`
4. A lógica genérica de “abrir e recusar formato” pode viver em `imagens.py`; a rule do app continua sendo quem lança `ValidationException` / `return_exception`. Não colocar persistência em rules.

### Critério de saída

- [ ] GIF/BMP/TIFF (mesmo com `Content-Type: image/jpeg`) → 400.
- [ ] JPEG, PNG e WebP válidos continuam aceitos (recurso reencodeia para JPEG; usuário pode manter o formato original).
- [ ] Arquivo sem `content_type` não burla a regra se o bytes não for JPEG/PNG/WebP.

### Testes mínimos desta etapa

- Recurso: `SimpleUploadedFile('foto.gif', bytes_gif, content_type='image/jpeg')` → 400; S3 `enviar` não chamado.
- Recurso: PNG/WebP válidos em retrato 3:4 ainda 200 (upload mockado).
- Opcional espelhado na foto secundária do usuário.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-2 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-3 — Erro de configuração S3 não vira 400

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

```python
except ValueError as e:
    raise ValidationException(str(e))
```

`enviar_arquivo_s3` levanta `ValueError('Configuração de armazenamento S3 inválida.')`. Isso vira **400** e pode vazar mensagem de infra. Erro interno deve ser `SystemErrorException` via `relancar_ou_erro_sistema` (mensagem genérica ao cliente).

### Arquivos

- `Infraestrutura/recursos/business.py` (`atualizar_foto`)
- `Identidade/usuarios/business.py` (`atualizar_foto_secundaria`) — o mesmo `except ValueError`
- Opcional e preferível: `AppCore/common/storage/s3.py` e `imagens.py` passarem a levantar `ValidationException` (arquivo) vs `SystemErrorException` (config), para o business não precisar adivinhar `ValueError`

### O que fazer

1. **Não** converter todo `ValueError` em `ValidationException(str(e))`.
2. Caminho preferido: em `s3.py`, config incompleta → `SystemErrorException` (ou deixar `ValueError` **não** convertido, para o catch-all virar 500 genérico). Em `imagens.py`, arquivo ilegível → `ValidationException` **ou** `ValueError` com mensagem de arquivo, convertido de forma explícita.
3. Cliente **nunca** recebe `str(e)` de falha de credencial/config.
4. Contrato try/except do business permanece: corpo inteiro no `try`; catch-all `relancar_ou_erro_sistema`.

### Critério de saída

- [ ] S3 sem credencial no upload → 500 genérico (`RESPONSE_ERRO_INTERNO_SERVIDOR`), não 400.
- [ ] Arquivo ilegível / formato inválido continua 400 com mensagem de arquivo.
- [ ] Nenhum `ValidationException(str(e))` genérico nesses métodos.

### Testes mínimos desta etapa

- Mock `enviar_arquivo_s3` levantando `ValueError('Configuração de armazenamento S3 inválida.')` (ou `SystemErrorException`) no POST da foto → 500, sem a string de config no `detail`.
- Paisagem / arquivo inválido continua 400.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-3 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-4 — Validar foto antes de criar o recurso

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | FOTO-S3-2 recomendado (senão a validação “antes” ainda aceita formato forjado) |
| **Quem / onde** | |

### Por quê

`criar_recurso` faz `Recurso.objects.create(...)` e só depois `atualizar_foto`. Na view o `atomic()` desfaz o insert se a foto falhar; o **business** sozinho (admin `run_business`, chamada direta) não é atômico. Ordem correta: validar/processar → persistir → enviar S3.

### Arquivos

- `Infraestrutura/recursos/business.py` (`criar_recurso`, `atualizar_foto`)
- `Infraestrutura/recursos/rules.py` (reutilizar `validar_arquivo_foto` / orientação / resolução)
- Testes: `Infraestrutura/tests/test_recurso_foto.py`

### O que fazer

1. Se veio `foto`, rodar as rules de arquivo + orientação + resolução (e o recorte, se a resolução é **após** o recorte) **antes** do `create`.
2. Evitar processar a imagem duas vezes: extrair algo como `_processar_foto_para_upload(arquivo) -> BytesIO` usado por `atualizar_foto` e por `criar_recurso`, ainda **dentro** do `try` de cada método público (não criar função de módulo solta nas views).
3. Só então `create` + upload + `save(update_fields=['foto'])`.
4. Código inválido / sala inválida continua falhando **antes** de qualquer S3.

### Critério de saída

- [ ] POST `/recursos/` multipart com paisagem → 400 e **nenhum** `Recurso` com aquele `codigo`.
- [ ] POST com retrato válido continua 201 e persiste a chave S3 (upload mockado).
- [ ] `criar_recurso` sem foto permanece igual.

### Testes mínimos desta etapa

Obrigatório (também listado em FOTO-S3-9; pode nascer aqui):

- `test_criar_recurso_com_foto_paisagem_nao_persiste` → 400 + `Recurso.objects.filter(codigo='...').exists() is False`

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-4 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-5 — Tirar ORM do hook de criação

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

Views não fazem `Model.objects.get(...)`. O hook atual busca de novo só para `select_related('sala')` e serializar. Isso pertence ao business/helpers.

O `context={'request': request}` no `RecursoSerializer` **deve permanecer** — sem request a URL do proxy some quando não há `CORTEX_PUBLIC_BASE_URL`.

### Arquivos

- `Infraestrutura/recursos/business.py` (`criar_recurso`)
- `Infraestrutura/recursos/helpers.py` (se a query reutilizável couber melhor aqui)
- `Infraestrutura/recursos/views.py` (`CriarRecursoView.do_action_post`)

### O que fazer

1. `criar_recurso` devolve o recurso já com `select_related('sala')` (reconsultar por pk **no business/helper**, não na view).
2. View fica só:

```python
recurso = Recurso().business.criar_recurso(**serializer_data)
return {
    'mensagem': self.mensagem_sucesso,
    'dados': RecursoSerializer(recurso, context={'request': request}).data,
    'status_code': status.HTTP_201_CREATED,
}
```

3. Não mover serialização para o business.

### Critério de saída

- [ ] `CriarRecursoView` sem `.objects.get` / `.filter` / `.create`.
- [ ] POST de criação (com e sem foto) continua 201 com `sala` e `foto` (URL de proxy) corretos.

### Testes mínimos desta etapa

- Os testes de cadastro em `Infraestrutura/tests/test_cadastro_views.py` e `test_cadastrador_cria_recurso_com_foto_retrato` continuam verdes.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-5 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-6 — Documentação compilada de permissões

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

`GET /cortex/identidade/permissoes/documentacao/` alimenta o frontend. Listagem de recursos exige autenticação; **GET da foto é público**. `documentacao_infraestrutura()` ainda descreve leitura só como “catálogos autenticados” e não cita upload/remoção de foto em `cadastrar`.

### Arquivos

- `Identidade/usuarios/documentacao.py` (`documentacao_infraestrutura`)
- Testes que snapshotam essa documentação, se existirem (`Identidade/usuarios/tests/` — procurar `documentacao_infraestrutura` / `infraestrutura`)
- Opcional: [schema infraestrutura](../schema/infraestrutura.md) só se o texto de permissão da foto estiver incompleto (hoje o schema já diz proxy público)

### O que fazer

1. Em `cadastrar.pode` (e `descricao` se fizer sentido): incluir enviar e remover foto do recurso (`POST`/`DELETE /recursos/{pk}/foto/` e foto no multipart de criação).
2. Deixar explícito que `GET /recursos/{pk}/foto/` é **público** (AllowAny); bucket privado; listagem/detalhe JSON continuam autenticados.
3. Não inventar capacidade nova.

### Critério de saída

- [ ] Texto compilado menciona GET público da foto e escrita da foto na capacidade `cadastrar`.
- [ ] Nenhuma mudança de mixin/regra de acesso neste item (só documentação).

### Testes mínimos desta etapa

- Se houver assert de string da documentação, atualizar. Caso contrário, revisão manual do dict retornado.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-6 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-7 — Schema no método `get` e view de retrieve no proxy

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Importante |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

Sobrescrever `get()` para `StreamingHttpResponse` é justificado. O guia pede `@extend_schema` **no método** quando o HTTP é sobrescrito. `BasicGetAPIView` é listagem: se o `get()` for apagado por engano, a view lista JSON de recursos. `BasicRetrieveAPIView` é “um objeto por pk”.

Aplicar nos dois proxies (recurso **e** foto secundária) para não deixar o de usuário no padrão antigo.

### Arquivos

- `Infraestrutura/recursos/views.py` (`ObterFotoRecursoView`)
- `Identidade/usuarios/views.py` (`ObterFotoSecundariaView`)
- URLs: não mudar os `name=` (`recurso-foto`, `usuario-foto-secundaria`)

### O que fazer

1. Trocar a base de `BasicGetAPIView` para `BasicRetrieveAPIView`.
2. Manter `AllowAnyMixin`, `queryset`, `get_object().business.obter_stream_*`, `StreamingHttpResponse`, `Cache-Control`.
3. Mover `@extend_schema` para o `def get`.
4. Manter `@handle_exceptions` no `get` (a base de retrieve monta JSON; o override substitui o método inteiro).
5. Não sobrescrever `get` nas views de listagem/detalhe JSON.

### Critério de saída

- [ ] GET anônimo da foto (recurso e usuário) continua 200 com bytes e content-type.
- [ ] `@extend_schema` está no método `get`.
- [ ] Classe herda `BasicRetrieveAPIView` (uma view base só).

### Testes mínimos desta etapa

- `test_get_proxy_foto_sem_autenticacao`
- `test_get_proxy_foto_secundaria_sem_autenticacao` (nome aproximado em `Identidade/usuarios/tests/test_views.py`)

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-7 de docs/planning/followup-revisao-fotos-s3.md
```

---

## FOTO-S3-8 — `CharField` para chave S3 (não `URLField`)

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Sugestão |
| **Pré-requisito** | Nenhum |
| **Quem / onde** | |

### Por quê

A coluna guarda chave (`Cortex/infraestrutura/recursos/fotos/{id}/uuid.jpg`), não URL. `URLField` só não quebra porque `save()` não chama `full_clean()`. A URL pública continua no serializer via `ANEXO_FOTO.url_proxy`.

O mesmo vale para `Usuario.foto_secundaria` (e só ela; `Usuario.foto` primária **é** URL externa — **não** converter a primária).

### Arquivos

- `Infraestrutura/recursos/models.py`
- `Identidade/usuarios/models.py` (`foto_secundaria` apenas)
- Novas migrations (histórico simple-history incluso)
- Admin: `readonly_fields` da foto do recurso pode permanecer

### O que fazer

1. `foto` do recurso: `CharField(max_length=500, null=True, blank=True)` com o mesmo `verbose_name` / `help_text` (ajustar help_text para “chave S3”, não “URL”).
2. `foto_secundaria` do usuário: o mesmo, se o campo hoje é `URLField`.
3. Gerar migration com a skill **django-safe-migration**. No PostgreSQL, `URLField` → `CharField` de mesmo `max_length` costuma ser no-op / `ALTER` trivial; mesmo assim revisar lock e `SeparateDatabaseAndState` se o autodetector inventar rewrite.
4. Serializer de leitura **não** muda o contrato JSON (continua URL de proxy).
5. Não aceitar chave crua no PATCH de recurso.

### Critério de saída

- [ ] Models não usam `URLField` para chave S3.
- [ ] Migration aplica em banco vazio e em banco que já tem `0002_recurso_foto`.
- [ ] Upload + listagem/detalhe continuam devolvendo URL de proxy.
- [ ] `Usuario.foto` (primária) permanece `URLField`.

### Testes mínimos desta etapa

- Testes de foto existentes verdes.
- Se houver `full_clean()` em teste de model, chave S3 deve passar.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-8 de docs/planning/followup-revisao-fotos-s3.md
Use a skill django-safe-migration na migration.
```

---

## FOTO-S3-9 — Testes que fecham as lacunas

| | |
|--|--|
| **Status** | Pendente |
| **Severidade** | Sugestão |
| **Pré-requisito** | Ideal depois de FOTO-S3-1..4 (os asserts dependem do comportamento novo). Pode ir **parcialmente** junto de cada etapa. |
| **Quem / onde** | |

### Por quê

A suíte atual cobre retrato, recorte, 3 MB, L1 403, substitui/remove, GET anônimo e URL de proxy. Não trava rollback da criação, formato forjado, 404 de recurso vs sem foto, nem “PATCH não aceita foto”.

### Arquivos

- `Infraestrutura/tests/test_recurso_foto.py` (principal)
- `Infraestrutura/tests/test_cadastro_views.py` (PATCH sem campo foto, se couber)
- `Identidade/usuarios/tests/test_views.py` só se FOTO-S3-1/2/3 tiverem mudado o proxy de usuário e ainda faltar assert
- Padrão: `APITestCase`, `reverse('infraestrutura:...')`, sem path hardcoded (`docs/project/regras-do-projeto.md`)

### Cenários obrigatórios (marcar quando existir no código)

- [ ] `test_criar_recurso_com_foto_paisagem_nao_persiste` — 400 e recurso não criado (FOTO-S3-4)
- [ ] `test_rejeita_gif_com_content_type_jpeg` — 400; `enviar_arquivo_s3` não chamado (FOTO-S3-2)
- [ ] `test_get_proxy_foto_recurso_inexistente` — 404
- [ ] `test_get_proxy_foto_retorna_404_sem_foto` — já existe; conferir se ainda passa após FOTO-S3-1
- [ ] `test_patch_recurso_nao_aceita_foto` — PATCH com arquivo/string `foto` não altera a chave
- [ ] `test_iterar_rejeita_chave_fora_do_prefixo` — 404; S3 não chamado (FOTO-S3-1)
- [ ] `test_s3_nao_configurado_retorna_500` — upload com S3 inválido → 500 sem detalhe de config (FOTO-S3-3)

Não duplicar teste que a etapa anterior já tiver adicionado: nesta etapa só complete o que ainda estiver em aberto.

### Critério de saída

- [ ] Todos os checkboxes acima existem (aqui ou nascidos nas etapas 1–4).
- [ ] `python manage.py test Infraestrutura.tests.test_recurso_foto Identidade.usuarios.tests.test_views` (ou o módulo equivalente da foto secundária) passa.

### Prompt curto

```text
Implemente SOMENTE FOTO-S3-9 de docs/planning/followup-revisao-fotos-s3.md
Não refatore produção além do indispensável para um teste. Complete só os cenários ainda não cobertos.
```

---

## Verificação final (quando as 9 estiverem Concluída)

Rodar, no ambiente do projeto:

```bash
python manage.py test Infraestrutura.tests.test_recurso_foto Infraestrutura.tests.test_cadastro_views Identidade.usuarios.tests.test_views
```

Conferir à mão:

1. Nenhuma view de recurso com ORM no `do_action_*`.
2. `AnexoS3.iterar` recusa chave fora do prefixo.
3. `documentacao_infraestrutura` cita GET público e escrita da foto.
4. `Recurso.foto` e `Usuario.foto_secundaria` são `CharField` (se FOTO-S3-8 foi feita).

Depois disso, este follow-up pode ser arquivado (status geral Concluído no progresso) sem apagar o arquivo — serve de histórico.

---

## Fora de escopo

- Tornar o GET da foto autenticado (decisão de produto já documentada).
- Processar/recorte 3:4 na foto secundária do usuário (requisito só do recurso).
- Trocar o descritor `AnexoS3` ou o prefixo `Cortex/infraestrutura/recursos/fotos`.
- Refatoração geral de Infraestrutura, empréstimos ou importação de usuários.
- Reabrir a revisão dos 9 itens: se aparecer achado novo, criar **outra** etapa `FOTO-S3-10+` no fim deste arquivo, não editar o enunciado das etapas já concluídas.
