---
name: revisao-codigo
description: "Revisão de código do projeto Cortex/DRF. Use para revisar arquivos Python (views, business, rules, helpers, models, serializers) verificando se os padrões da arquitetura em camadas estão corretos: views leves, hooks do_action_post/do_action_put/do_action_patch/do_action_delete implementados corretamente, delegação para Business, uso de exceções do AppCore, nomenclatura em português, documentação Swagger, permissões e serializers."
argument-hint: "Arquivo ou trecho de código a revisar (opcional)"
user-invocable: true
---

# Revisão de Código — Projeto Cortex

## Objetivo

Revisar arquivos Python do projeto verificando conformidade com os padrões arquiteturais definidos no `project-rules.md`. O revisor **aponta problemas, explica o padrão correto e sugere o código corrigido**.

---

## Processo de Revisão

### 1. Identificar o escopo

- Se o usuário indicou um arquivo ou trecho, revise esse alvo.
- Se não indicou, pergunte qual arquivo ou contexto revisar.
- Leia o arquivo completo antes de apontar qualquer problema.

### 2. Aplicar os checklist por tipo de arquivo

Execute o checklist correspondente ao tipo de arquivo detectado (Views, Business, Rules, Helpers, Models, Serializers). Um arquivo pode ter mais de um tipo.

### 3. Reportar os resultados

Para cada problema encontrado:

- Indique a **linha ou trecho** problemático.
- Explique **qual padrão está sendo violado**.
- Forneça o **código corrigido**.

Se nenhum problema for encontrado, confirme que o arquivo está em conformidade.

---

## Checklists

### Views (`views.py`)

#### Views Leves — Regra Fundamental

- [ ] A view **não contém lógica de negócio** (loops, cálculos, condicionais de domínio).
- [ ] A view apenas recebe dados, delega ao Business e retorna resposta.
- [ ] **Toda lógica** está no `business.py`, não na view.
- [ ] A view **não contém queries ORM diretas** (`Model.objects.get(...)`, `.filter(...)`, `.create(...)`, etc.) — toda query vai para o Business ou Helpers.
- [ ] A view usa uma **view base do AppCore** (`BasicPostAPIView`, `BasicGetAPIView`, `BasicRetrieveAPIView`, `BasicPutAPIView`, `BasicPatchAPIView`, `BasicDeleteAPIView`) — usar `GenericAPIView` diretamente é exceção justificada, não o padrão.

**Exemplo errado:**

```python
def do_action_post(self, serializer_data, request):
    for attr, value in serializer_data.items():   # ← lógica de negócio na view
        setattr(self.object, attr, value)
    self.object.save()
```

**Exemplo correto:**

```python
def do_action_post(self, serializer_data, request):
    UsuarioBusiness().criar_usuario(**serializer_data)
```

---

#### Responsabilidade Única e Sobrescritas de Métodos HTTP

- [ ] A view herda de **exatamente UM** `BasicXxxAPIView` — nunca dois ou mais ao mesmo tempo.
- [ ] A view **NÃO** combina `BasicGetAPIView + BasicPostAPIView` (ou qualquer par) via herança múltipla.
- [ ] Para um endpoint com múltiplos métodos HTTP na mesma URL, usa-se `roteador_por_metodo(...)` no `urls.py` com views separadas:
  ```python
  path('recursos/', roteador_por_metodo(GET=ListarRecursosView, POST=CriarRecursoView))
  ```
- [ ] A view **NÃO** sobrescreve métodos HTTP (`get()`, `post()`, `patch()`, `put()`, `delete()`) sem justificativa válida.
- [ ] Sobrescrita de método HTTP é justificada **apenas** quando:
  1. A view precisa **retornar dados** (objeto criado/atualizado) na resposta — `_build_success_response` só retorna `{status, mensagem}`, sem `dados`.
  2. A lógica não se encaixa nos hooks disponíveis (ex: busca não-padrão que não usa `queryset`).
- [ ] Métodos HTTP que apenas chamam `super()` (ex: `def post(self, ...): return super().post(...)`) **devem ser removidos** — são desnecessários.
- [ ] `@extend_schema` está na **CLASSE** quando a view usa apenas hooks (`do_action_*`) sem sobrescrever o método HTTP.
- [ ] `@extend_schema` está no **MÉTODO** sobrescrito quando há sobrescrita justificada do método HTTP.

---

#### Hooks das Views Base (`do_action_*`)

Os hooks `do_action_post`, `do_action_put`, `do_action_patch` e `do_action_delete` têm contratos específicos:

##### `do_action_post(self, serializer_data, request)`

- Parâmetro é `serializer_data` (dict de `validated_data`), **não** o serializer.
- Retorno: `dict` opcional com `mensagem` e/ou `status_code`. Se retornar `None` ou `{}`, usa `mensagem_sucesso` da view.
- **NÃO** deve retornar `Response` diretamente.
- **NÃO** deve conter `transaction.atomic()` — já é gerenciado pela view base.

```python
# ✅ CORRETO
def do_action_post(self, serializer_data, request):
    usuario = UsuarioBusiness().criar_usuario(**serializer_data)
    return {
        'mensagem': 'Usuário criado com sucesso.',
        'status_code': status.HTTP_201_CREATED,
    }

# ❌ ERRADO — retornando Response diretamente
def do_action_post(self, serializer_data, request):
    UsuarioBusiness().criar_usuario(**serializer_data)
    return Response({'mensagem': 'ok'}, status=201)

# ❌ ERRADO — gerenciando transação manualmente
def do_action_post(self, serializer_data, request):
    with transaction.atomic():
        UsuarioBusiness().criar_usuario(**serializer_data)
```

##### `do_action_put(self, serializer_data, request)` e `do_action_patch(self, serializer_data, request)`

- `self.object` está disponível (objeto recuperado pelo `get_object()`).
- Parâmetro é `serializer_data` (dict), **não** o serializer.
- Retorno: `dict` opcional com `mensagem` e/ou `status_code`.
- **NÃO** deve retornar `Response`.
- **NÃO** deve chamar `get_object()` novamente — já está em `self.object`.

```python
# ✅ CORRETO
def do_action_patch(self, serializer_data, request):
    self.object.business.atualizar_dados(serializer_data)

# ❌ ERRADO — chamando get_object() de novo
def do_action_patch(self, serializer_data, request):
    obj = self.get_object()   # ← desnecessário, gera query extra
    obj.business.atualizar_dados(serializer_data)

# ❌ ERRADO — lógica de atualização diretamente na view
def do_action_patch(self, serializer_data, request):
    for attr, value in serializer_data.items():
        setattr(self.object, attr, value)
    self.object.save()
```

##### `do_action_delete(self, request)`

- `self.object` está disponível.
- **NÃO** deve retornar nada — a view base responde com `204 No Content`.
- **NÃO** deve retornar `Response`.

```python
# ✅ CORRETO
def do_action_delete(self, request):
    self.object.business.excluir()

# ❌ ERRADO — retornando Response
def do_action_delete(self, request):
    self.object.delete()
    return Response(status=204)
```

---

#### Views que NÃO usam as views base

Quando a view herda de `GenericAPIView` diretamente (sem usar `BasicPostAPIView` etc.):

- [ ] A view usa `@handle_exceptions` no método HTTP.
- [ ] A view gerencia `transaction.atomic()` com savepoint manualmente:
  ```python
  with transaction.atomic():
      sid = transaction.savepoint()
      try:
          # lógica
      except Exception:
          transaction.savepoint_rollback(sid)
          raise
      transaction.savepoint_commit(sid)
  ```
- [ ] Exceções são propagadas (nunca silenciadas com `except Exception: pass`).

---

#### Permissões

- [ ] Toda view usa um mixin de permissão: `AllowAnyMixin`, `IsOwnerOrAdminMixin` ou `IsAdminMixin`.
- [ ] Endpoints públicos usam `AllowAnyMixin` explicitamente.
- [ ] Views com `IsOwnerOrAdminMixin` implementam `obter_usuario_dono(self, obj)`.

---

#### Documentação Swagger (`@extend_schema`)

- [ ] **Toda view** possui `@extend_schema` com `tags`, `summary`, `description`, `responses`.
- [ ] `tags` usa PascalCase consistente com o módulo (ex: `['Identidade']`).
- [ ] `description` menciona as permissões necessárias.
- [ ] `responses` lista pelo menos os códigos `200/201`, `401`, `403`, `404` quando aplicável.
- [ ] Query params estão declarados em `parameters=[OpenApiParameter(...)]`.
- [ ] A descrição de query params menciona que **"apenas reduzem o conjunto, nunca expandem o acesso"**.

---

#### Query Params

- [ ] O queryset base já está restrito pela permissão (URL context ou verificação de acesso).
- [ ] Filtros por query param só são aplicados **depois** do escopo base.
- [ ] Valores inválidos são ignorados silenciosamente (nunca retornam erro 400).
- [ ] Valores booleanos aceitam apenas `'true'` e `'false'` (case-insensitive):
  ```python
  ativo = self.request.query_params.get('ativo')
  if ativo is not None and ativo.lower() in ('true', 'false'):
      qs = qs.filter(ativo=ativo.lower() == 'true')
  ```

---

### Business (`business.py`)

- [ ] Herda de `ModelInstanceBusiness`.
- [ ] Usa `self.object_instance` para acessar o objeto (não `self.object`).
- [ ] Orquestra chamadas a `Rules`, `Helpers` e `State` — não implementa lógica de domínio que pertença a essas camadas.
- [ ] Blocos `try/except Exception` **nunca** retornam `str(e)` ao cliente — sempre lançam `SystemErrorException` com mensagem genérica e logam com `logger.exception(...)`.
- [ ] Método padrão de atualização:
  ```python
  def atualizar_dados(self, dados: dict):
      try:
          for attr, value in dados.items():
              setattr(self.object_instance, attr, value)
          self.object_instance.save()
      except Exception as e:
          logger.exception('Erro ao atualizar dados: %s', e)
          raise SystemErrorException('Não foi possível atualizar os dados.')
  ```

---

### Rules (`rules.py`)

- [ ] Herda de `ModelInstanceRules`.
- [ ] Métodos retornam `True` (sucesso) ou lançam exceção do AppCore (nunca retornam `False` silenciosamente).
- [ ] **Não contém** lógica de persistência (nenhum `.save()`, `.create()`, `.delete()`).
- [ ] **Não é chamada diretamente pela view** — somente pelo Business.

```python
# ✅ CORRETO — método em português
def pode_desativar(self):
    if not self.object_instance.ativo:
        self.return_exception('Usuário já está inativo.')
    return True

# ❌ ERRADO — nome em inglês
def can_desativar(self):
    ...
```

---

### Helpers (`helpers.py`)

- [ ] Herda de `ModelInstanceHelpers`.
- [ ] Contém apenas queries reutilizáveis e transformações de dados.
- [ ] **Não contém** lógica de negócio.
- [ ] **Não é chamada diretamente pela view** — somente pelo Business.

---

### Models (`models.py`)

- [ ] Models não-usuário herdam de `BasicModel`.
- [ ] Model de usuário herda de `AbstractBaseAppUser`.
- [ ] Models com Business usam `ModelBusinessMixin` e definem `business_class`.
- [ ] Models com Helpers usam `ModelHelperMixin` e definem `helper_class`.
- [ ] `verbose_name` e `verbose_name_plural` estão em português.
- [ ] `related_name` está em português e é descritivo.
- [ ] Herança de usuário usa `OneToOneField` com `primary_key=True`.

---

### Serializers (`serializers.py`)

- [ ] Serializers de input usam `serializers.Serializer` (não `ModelSerializer` por padrão).
- [ ] Campos sensíveis têm `write_only=True`.
- [ ] Validações de senha verificam: mínimo 8 caracteres, maiúscula, minúscula, número e caractere especial.
- [ ] Validações de código numérico verificam exatamente 6 dígitos.
- [ ] Serializers de documentação (`*InputSerializer`, `*ResponseSerializer`) estão separados quando necessário.

---

## Convenções Gerais

### Nomenclatura

- [ ] Variáveis, funções e métodos do domínio estão em **português** — aplica-se a **todas as camadas**: Business, Rules, Helpers e State.
- [ ] Métodos de Rules usam prefixo em português: `pode_*`, `validar_*`, `verificar_*` — **nunca** `can_*`, `check_*`, `is_*` para lógica de domínio.
- [ ] Exceções apenas para overrides de framework: `get_queryset`, `get_serializer_class`, `validate`, `create`, `update`.
- [ ] Módulos e apps: snake_case minúsculo (`usuarios`, `auth`).

**Exemplos:**

```python
# ✅ CORRETO
def obter_contatos(self): ...
def criar_usuario(self, dados): ...
def atualizar_dados(self, dados): ...

# ❌ ERRADO
def get_contatos(self): ...
def create_usuario(self, dados): ...
def update_dados(self, dados): ...
```

### Aspas

- [ ] **Sempre aspas simples** em strings Python: `'texto'` (nunca `"texto"`).
- [ ] Exceção: f-strings ou strings que contêm aspas simples internas.

### Imports

- [ ] Ordem: stdlib → Django → DRF → AppCore → apps locais.
- [ ] Sem imports não utilizados.

### Exceções

- [ ] **Sempre** use exceções do AppCore (`BusinessRuleException`, `ValidationException`, `AuthorizationException`, `NotFoundException`, `SystemErrorException`).
- [ ] **Nunca** use `raise Exception(...)` ou `raise ValueError(...)` para erros de domínio.
- [ ] `except Exception` genérico sempre loga com `logger.exception(...)` e relança `SystemErrorException`.

---

## Hierarquia de Chamadas — Validação Rápida

```
View → Business → Rules / Helpers / State
```

- [ ] View chama apenas Business (nunca Rules ou Helpers diretamente).
- [ ] Business chama Rules, Helpers e State conforme necessário.
- [ ] Rules, Helpers e State **não se chamam entre si**.

---

## Referências

- Padrões completos: [`docs/antigravity/project-rules.md`](../project-rules.md)
- Views base: [`AppCore/basics/views/basic_views.py`](../../../AppCore/basics/views/basic_views.py)
- Exceções: [`AppCore/core/exceptions/exceptions.py`](../../../AppCore/core/exceptions/exceptions.py)
- Exemplo de implementação: [`Identidade/identidade/views.py`](../../../Identidade/identidade/views.py), [`Identidade/identidade/business.py`](../../../Identidade/identidade/business.py)
