---
name: implementacao
description: "Implementação de código no projeto Cortex/DRF seguindo os padrões arquiteturais. Use para criar ou modificar views, business, rules, helpers, models, serializers e urls. Aplica corretamente os mixins do AppCore, as views base (BasicPostAPIView, BasicGetAPIView, BasicRetrieveAPIView, BasicPutAPIView, BasicPatchAPIView, BasicDeleteAPIView), exceções, permissões, paginação, documentação Swagger e nomenclatura em português."
argument-hint: "Descreva o que precisa ser implementado (ex: endpoint de criação de produto, camada business de Aluno, etc.)"
user-invocable: true
---

# Implementação — Projeto Cortex

## Objetivo

Implementar código novo ou modificar existente seguindo rigorosamente os padrões do projeto. Esta skill conhece todos os componentes do `AppCore` e como aplicá-los corretamente.

---

## Processo de Implementação

1. **Entender o requisito** — identificar qual(is) camada(s) precisam ser criadas ou modificadas.
2. **Explorar o contexto** — ler os arquivos existentes do app antes de criar qualquer coisa.
3. **Implementar na ordem correta**: Models → Rules → Helpers → Business → Serializers → Views → URLs.
4. **Seguir os padrões** descritos nesta skill sem desvios.
5. **Verificar conformidade** — ao concluir cada arquivo, aplicar o Checklist de Conformidade Obrigatório abaixo.
6. **Testes** — ao criar ou modificar views, escrever testes é **essencial**. Ao alterar comportamentos importantes em qualquer camada, analisar se os testes existentes precisam ser atualizados.

---

## ⚠️ Checklist de Conformidade Obrigatório

Aplicar a cada arquivo gerado ou modificado **antes de considerar a implementação concluída**. Violações desses itens foram encontradas em código gerado mesmo após as instruções estarem vigentes — não assumir conformidade sem verificar.

### Views

- [ ] Toda view herda de uma view base do AppCore (`BasicPostAPIView`, `BasicGetAPIView`, `BasicRetrieveAPIView`, `BasicPutAPIView`, `BasicPatchAPIView`, `BasicDeleteAPIView`) — `GenericAPIView` direto é exceção justificada, não o padrão
- [ ] Nenhum hook `do_action_*` contém queries ORM (`Model.objects.get(...)`, `.filter(...)`, `.create(...)`, etc.) — toda query vai para o Business
- [ ] `do_action_post` recebe `serializer_data` (dict), não o serializer inteiro
- [ ] Nenhum hook retorna `Response` diretamente — retorna `dict` opcional ou `None`
- [ ] Nenhum hook chama `transaction.atomic()` manualmente — já é gerenciado pela view base

### Business

- [ ] Métodos com `try/except Exception` nunca expõem `str(e)` ao cliente — sempre `SystemErrorException` + `logger.exception(...)`
- [ ] Nenhuma query ORM está na view — pertence ao Business (ou Helpers, chamados pelo Business)

### Rules

- [ ] Todos os métodos do domínio estão nomeados em **português**: `pode_*`, `validar_*`, `verificar_*` — **nunca** `can_*`, `check_*`, `is_valid_*`
- [ ] Nenhum método contém `.save()`, `.create()`, `.delete()` — persistência pertence ao Business
- [ ] Métodos retornam `True` (sucesso) ou lançam exceção — nunca retornam `False` silenciosamente

### Nomenclatura geral

- [ ] Todos os métodos do domínio (Business, Rules, Helpers, State) estão em português
- [ ] Exceções apenas para overrides de framework: `get_queryset`, `get_serializer_class`, `validate`, `create`, `update`

### Estrutura de módulo

- [ ] O app está dentro do módulo de domínio correto (ex: `Identidade/identidade/`), não na raiz do repositório
- [ ] `apps.py` usa `name = 'Modulo.app'` (caminho completo)
- [ ] O módulo tem `__init__.py` e `urls.py` com `app_name`

### URLs

- [ ] Todo `path()` tem `name=` declarado — **sem exceção**
- [ ] Padrão: `<recurso>-list` (raiz), `<recurso>-detail` (com pk), `<recurso>-<verbo>` (ações)
- [ ] Sub-apps **não** declaram `app_name` — namespace gerenciado pelo domínio pai
- [ ] Testes de API usam `reverse('<namespace>:<name>')`, nunca paths hardcoded

---

## Componentes do AppCore

### Classes Base dos Models

```python
# Model comum — sempre herde de BasicModel
from AppCore.basics.models.models import BasicModel
# Fornece: created_at, updated_at, history (django-simple-history)
# Manager padrão: BaseManager (lança NotFoundException no .get())

# Model de usuário — herde de AbstractBaseAppUser
from AppCore.basics.models.user_model import AbstractBaseAppUser
# Fornece: email, nome, ativo, is_admin, is_staff, created_at, updated_at, history
# USERNAME_FIELD padrão: 'email' (sobrescreva para 'cpf' quando necessário)

# Manager de usuário
from AppCore.basics.models.models import BaseManagerUser
# Combina BaseUserManager + BaseManager
```

### Mixins de Model (Business e Helpers)

```python
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

class Produto(ModelBusinessMixin, ModelHelperMixin, BasicModel):
    business_class = ProdutoBusiness   # obrigatório ao usar ModelBusinessMixin
    helper_class   = ProdutoHelpers    # obrigatório ao usar ModelHelperMixin

# Acesso:
# produto.business.criar_produto(...)   → instancia ProdutoBusiness(object_instance=produto)
# produto.helper.buscar_ativos()        → instancia ProdutoHelpers(object_instance=produto)
```

### Classes Base das Camadas

```python
# Business
from AppCore.core.business.business import ModelInstanceBusiness
# Atributo: self.object_instance  (o model passado no construtor)
# exceptions_handled: AuthorizationException, BusinessRuleException, ValidationException, NotFoundException

# Rules
from AppCore.core.rules.rules import ModelInstanceRules
# Atributo: self.object_instance
# Métodos: return_exception(msg), return_not_allowed(), return_response(msg, execute_exception)

# Helpers
from AppCore.core.helpers.helpers import ModelInstanceHelpers
# Atributo: self.object_instance
```

### Views Base

```python
from AppCore.basics.views.basic_views import (
    BasicPostAPIView,      # POST  — hook: do_action_post(serializer_data, request)
    BasicGetAPIView,       # GET   — hook: validate_get(request, ...) [opcional]
    BasicRetrieveAPIView,  # GET   — hook: validate_retrieve(request, ...) [opcional], self.object disponível
    BasicPutAPIView,       # PUT   — hook: do_action_put(serializer_data, request), self.object disponível
    BasicPatchAPIView,     # PATCH — hook: do_action_patch(serializer_data, request), self.object disponível
    BasicDeleteAPIView,    # DELETE— hook: do_action_delete(request), self.object disponível
)
```

**Retorno dos hooks de escrita** (POST, PUT, PATCH): `dict` opcional com `mensagem` e/ou `status_code`.
`do_action_delete` não retorna nada (view base responde 204).

### Permissões (Mixins de View)

```python
from AppCore.basics.mixins.mixins import AllowAnyMixin, IsOwnerOrAdminMixin, IsAdminMixin

# AllowAnyMixin       → endpoints públicos (sem autenticação)
# IsAdminMixin        → apenas is_admin=True ou superusuário
# IsOwnerOrAdminMixin → dono do recurso ou admin
#   ↳ obrigatório implementar: obter_usuario_dono(self, obj) → retorna o usuário dono
```

### Paginação

```python
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
# page_size=10, query param: ?paginacao=N (min 1, max 100)
```

### Exceções

```python
from AppCore.core.exceptions.exceptions import (
    BusinessRuleException,   # regra de negócio violada → 400
    ValidationException,     # dados inválidos → 400
    AuthorizationException,  # sem permissão → 403
    NotFoundException,       # não encontrado → 404
    SystemErrorException,    # erro interno → 500 (nunca expõe str(e) ao cliente)
)
```

### Decorator de Exceções (views manuais)

```python
from AppCore.basics.decorators.decorators import handle_exceptions
# Captura todas as exceções do AppCore e retorna Response adequado.
# Obrigatório quando a view NÃO herda de uma BasicView.
```

---

## Templates de Implementação

### Model

```python
import logging
from django.db import models
from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

logger = logging.getLogger(__name__)


class Produto(ModelBusinessMixin, ModelHelperMixin, BasicModel):
    business_class = None   # preencher após criar ProdutoBusiness
    helper_class   = None   # preencher após criar ProdutoHelpers

    nome = models.CharField('Nome', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return self.nome
```

**Herança de usuário** (relação especialização):

```python
class Servidor(BasicModel):
    usuario = models.OneToOneField(
        'identidade.Usuario',
        on_delete=models.CASCADE,
        related_name='servidor',
        primary_key=True,
        verbose_name='Usuário',
    )
    jornada = models.IntegerField('Jornada', choices=JornadaTrabalho.choices)

    class Meta:
        verbose_name = 'Servidor'
        verbose_name_plural = 'Servidores'
```

---

### Rules

```python
import logging
from AppCore.core.rules.rules import ModelInstanceRules

logger = logging.getLogger(__name__)


class ProdutoRules(ModelInstanceRules):

    def pode_excluir(self):
        if self.object_instance.tem_vendas_ativas:
            self.return_exception('Produto com vendas ativas não pode ser excluído.')
        return True

    def pode_desativar(self):
        if not self.object_instance.ativo:
            self.return_exception('Produto já está inativo.')
        return True
```

---

### Business

```python
import logging
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import ProdutoRules

logger = logging.getLogger(__name__)


class ProdutoBusiness(ModelInstanceBusiness):

    # ------------------------------------------------------------------
    # Operações sem object_instance (criação)
    # ------------------------------------------------------------------

    def criar_produto(self, nome: str, **kwargs):
        from .models import Produto
        try:
            return Produto.objects.create(nome=nome, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar produto: %s', e)
            raise SystemErrorException('Não foi possível criar o produto.')

    # ------------------------------------------------------------------
    # Operações com object_instance
    # ------------------------------------------------------------------

    def atualizar_dados(self, dados: dict):
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar produto: %s', e)
            raise SystemErrorException('Não foi possível atualizar o produto.')

    def excluir(self):
        regras = ProdutoRules(object_instance=self.object_instance)
        regras.pode_excluir()
        try:
            self.object_instance.delete()
        except Exception as e:
            logger.exception('Erro ao excluir produto: %s', e)
            raise SystemErrorException('Não foi possível excluir o produto.')

    def desativar(self):
        regras = ProdutoRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar produto: %s', e)
            raise SystemErrorException('Não foi possível desativar o produto.')
```

---

### Helpers

```python
from django.utils import timezone
from AppCore.core.helpers.helpers import ModelInstanceHelpers


class ProdutoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        from .models import Produto
        return Produto.objects.filter(ativo=True)

    def buscar_por_nome(self, nome: str):
        from .models import Produto
        return Produto.objects.filter(nome__icontains=nome)
```

---

### Serializers

```python
from rest_framework import serializers
from .models import Produto


# Input (POST/PUT/PATCH) — use serializers.Serializer
class CriarProdutoSerializer(serializers.Serializer):
    nome  = serializers.CharField(max_length=255)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_nome(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError('Nome deve ter pelo menos 3 caracteres.')
        return value.strip()


class AtualizarProdutoSerializer(serializers.Serializer):
    nome  = serializers.CharField(max_length=255, required=False)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


# Output (resposta) — pode usar ModelSerializer
class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Produto
        fields = ['id', 'nome', 'preco', 'ativo', 'created_at']


# Serializers de documentação Swagger (quando necessários)
class CriarProdutoInputSerializer(serializers.Serializer):
    '''Usado apenas para documentar o request body no Swagger.'''
    nome  = serializers.CharField()
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)
```

**Validação de senha** (padrão obrigatório):

```python
import re
from rest_framework import serializers

def validate_senha(self, value):
    if len(value) < 8:
        raise serializers.ValidationError('Senha deve ter pelo menos 8 caracteres.')
    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError('Senha deve conter pelo menos uma letra maiúscula.')
    if not re.search(r'[a-z]', value):
        raise serializers.ValidationError('Senha deve conter pelo menos uma letra minúscula.')
    if not re.search(r'\d', value):
        raise serializers.ValidationError('Senha deve conter pelo menos um número.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise serializers.ValidationError('Senha deve conter pelo menos um caractere especial.')
    return value
```

---

### Views

#### View com `BasicPostAPIView`

```python
from rest_framework import status
from drf_spectacular.utils import extend_schema

from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.views.basic_views import BasicPostAPIView

from .business import ProdutoBusiness
from .serializers import CriarProdutoSerializer, ProdutoSerializer


@extend_schema(
    tags=['Produtos'],
    summary='Criar produto',
    description='''
    Cria um novo produto no sistema.

    **Permissões:** Apenas administradores.
    ''',
    request=CriarProdutoSerializer,
    responses={
        status.HTTP_201_CREATED: ProdutoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class CriarProdutoView(IsAdminMixin, BasicPostAPIView):
    serializer_class  = CriarProdutoSerializer
    mensagem_sucesso  = 'Produto criado com sucesso.'

    def do_action_post(self, serializer_data, request):
        ProdutoBusiness().criar_produto(**serializer_data)
        # retorno opcional — sobrescreve mensagem_sucesso e status_code
        return {'status_code': status.HTTP_201_CREATED}
```

#### View com `BasicPatchAPIView`

```python
from AppCore.basics.views.basic_views import BasicPatchAPIView
from AppCore.basics.mixins.mixins import IsOwnerOrAdminMixin
from .models import Produto
from .serializers import AtualizarProdutoSerializer, ProdutoSerializer


@extend_schema(
    tags=['Produtos'],
    summary='Atualizar produto',
    description='Atualiza parcialmente um produto.\n\n**Permissões:** Dono ou administrador.',
    request=AtualizarProdutoSerializer,
    responses={
        status.HTTP_200_OK: ProdutoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Produto não encontrado.'},
    },
)
class AtualizarProdutoView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    serializer_class = AtualizarProdutoSerializer
    queryset         = Produto.objects.all()
    mensagem_sucesso = 'Produto atualizado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj.criado_por   # campo FK para o usuário dono

    def do_action_patch(self, serializer_data, request):
        # self.object já está disponível
        self.object.business.atualizar_dados(serializer_data)
```

#### View com `BasicGetAPIView` (listagem paginada)

```python
from AppCore.basics.views.basic_views import BasicGetAPIView
from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Produto
from .serializers import ProdutoSerializer


@extend_schema(
    tags=['Produtos'],
    summary='Listar produtos',
    description='''
    Retorna lista paginada de produtos.

    **Permissões:** Apenas administradores.

    **Segurança:** query params apenas reduzem o conjunto de resultados dentro do
    escopo já autorizado — nunca expandem o acesso além do permitido pela permissão.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por status: true (ativos) ou false (inativos).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: ProdutoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ListarProdutosView(IsAdminMixin, BasicGetAPIView):
    serializer_class  = ProdutoSerializer
    pagination_class  = PaginacaoCustomizada
    mensagem_sucesso  = 'Produtos listados com sucesso.'

    def get_queryset(self):
        qs = Produto.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs
```

#### View com `BasicDeleteAPIView`

```python
from AppCore.basics.views.basic_views import BasicDeleteAPIView
from AppCore.basics.mixins.mixins import IsAdminMixin
from .models import Produto


@extend_schema(
    tags=['Produtos'],
    summary='Excluir produto',
    description='Exclui um produto.\n\n**Permissões:** Apenas administradores.',
    responses={
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Produto não encontrado.'},
    },
)
class ExcluirProdutoView(IsAdminMixin, BasicDeleteAPIView):
    queryset = Produto.objects.all()

    def do_action_delete(self, request):
        # self.object já está disponível
        self.object.business.excluir()
        # não retorna nada — view base responde 204
```

#### View Manual (sem view base) — apenas quando necessário

Use `GenericAPIView` diretamente apenas quando a view mistura vários métodos HTTP com lógicas muito distintas e as views base seriam redundantes. Nesse caso, **sempre** use `@handle_exceptions` e gerencie a transação manualmente:

```python
import logging
from django.db import transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import IsAdminMixin

logger = logging.getLogger(__name__)


class ProdutoView(IsAdminMixin, GenericAPIView):
    queryset = Produto.objects.all()

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        produto = self.get_object()
        return Response({
            'status': 'success',
            'mensagem': 'Produto obtido com sucesso.',
            'dados': ProdutoSerializer(produto).data,
        })

    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        produto = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                produto.business.atualizar_dados(serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return Response({
            'status': 'success',
            'mensagem': 'Produto atualizado com sucesso.',
            'dados': ProdutoSerializer(produto).data,
        })
```

---

### URLs

```python
# produtos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListarProdutosView.as_view(), name='produto-list'),
    path('<int:pk>/', views.ProdutoView.as_view(), name='produto-detail'),
    path('<int:pk>/atualizar/', views.AtualizarProdutoView.as_view(), name='produto-atualizar'),
    path('<int:pk>/excluir/', views.ExcluirProdutoView.as_view(), name='produto-excluir'),
]

# No urls.py principal (Cortex/urls.py)
# path('produtos/', include('produtos.urls')),
```

> **Regras obrigatórias para URLs:**
> - Todo `path()` deve ter `name=` declarado — sem exceção.
> - Padrão de nomenclatura: `<recurso>-<ação>` no singular, em kebab-case.
>   - Listagem/criação (rota raiz): `<recurso>-list`
>   - Detalhe/atualização (rota com pk): `<recurso>-detail`
>   - Ações específicas: `<recurso>-<verbo>` (ex: `produto-desativar`, `produto-reativar`)
> - Sub-apps **não** devem declarar `app_name` — o namespace é gerenciado exclusivamente pelo `urls.py` do domínio pai (que tem `app_name`).
> - Nos testes, sempre use `reverse('<namespace>:<name>')` ao invés de hardcoded paths.


---

## Convenções Obrigatórias

### Aspas e Estilo

- Sempre aspas **simples**: `'texto'` (nunca aspas duplas).
- Imports organizados: stdlib → Django → DRF → AppCore → apps locais.
- `logger = logging.getLogger(__name__)` no topo de todo arquivo com logging.

### Nomenclatura

- Variáveis, funções, métodos: **português** (`criar_produto`, `atualizar_dados`, `listar_ativos`).
- Exceções do framework (override obrigatório): `get_queryset`, `get_serializer_class`, `validate`, `create`, `update`.
- `verbose_name` e mensagens sempre em português.

### Segurança

- `except Exception` **nunca** retorna `str(e)` ao cliente — sempre `SystemErrorException` + `logger.exception(...)`.
- Query params inválidos são ignorados silenciosamente (nunca retornam 400).
- Permissões validadas antes de qualquer filtro adicional.

### Estrutura de App

```
nome_app/
├── __init__.py
├── apps.py
├── models.py
├── choices.py       (se houver choices)
├── rules.py         (se houver regras de negócio)
├── helpers.py       (se houver queries reutilizáveis)
├── business.py      (se houver lógica de negócio)
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

---

## Referências Rápidas

| Componente                 | Caminho no AppCore                     |
| -------------------------- | -------------------------------------- |
| `BasicModel`               | `AppCore.basics.models.models`         |
| `AbstractBaseAppUser`      | `AppCore.basics.models.user_model`     |
| `BaseManagerUser`          | `AppCore.basics.models.models`         |
| `ModelBusinessMixin`       | `AppCore.core.business.business_mixin` |
| `ModelHelperMixin`         | `AppCore.core.helpers.helpers_mixin`   |
| `ModelInstanceBusiness`    | `AppCore.core.business.business`       |
| `ModelInstanceRules`       | `AppCore.core.rules.rules`             |
| `ModelInstanceHelpers`     | `AppCore.core.helpers.helpers`         |
| `BasicPostAPIView` …       | `AppCore.basics.views.basic_views`     |
| `AllowAnyMixin` …          | `AppCore.basics.mixins.mixins`         |
| `PaginacaoCustomizada`     | `AppCore.basics.pagination.pagination` |
| `handle_exceptions`        | `AppCore.basics.decorators.decorators` |
| Todas as exceções          | `AppCore.core.exceptions.exceptions`   |
| `BaseLoginSerializer`      | `AppCore.basics.auth.serializers`      |
| `BaseTypedLoginSerializer` | `AppCore.basics.auth.serializers`      |
