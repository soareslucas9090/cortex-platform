# Instruções para AI Coding Agents - Base DRF App

> **Última atualização:** 23 de maio de 2026

> [!IMPORTANT]
> **Sincronização com a documentação do projeto:**
> A pasta `docs/` é a referência obrigatória para qualquer decisão de arquitetura, domínio, regras de negócio, testes, convenções ou implementação. Antes de alterar código ou instruções, consulte `docs/antigravity/project-rules.md` e `docs/antigravity/rules/*.md`. Este arquivo deve permanecer sincronizado com essa documentação.

ATUALIZE O ARQUIVO .github/copilot-instructions.md sempre que houver mudanças significativas na estrutura, arquitetura ou convenções do projeto.

## Fontes de Verdade

- `docs/` sempre tem prioridade como documentação de referência do projeto.
- `docs/antigravity/project-rules.md` consolida as regras gerais de arquitetura e comportamento.
- `docs/antigravity/rules/*.md` consolida as regras específicas por domínio.
- `docs/seeds/` contém a documentação das entidades e os dados de seeds/inicialização do sistema (como `docs/seeds/documentação DER - cortex.md`).
- Se houver divergência entre este arquivo e a documentação em `docs/`, a documentação deve ser considerada a base a ser refletida na próxima atualização.

## Arquitetura em Camadas

Este projeto segue uma arquitetura modular de 4 camadas bem definidas. **Cada model deve ter suas próprias classes de camadas** localizadas no mesmo app.

### ⚠️ PRINCÍPIO FUNDAMENTAL: Views Leves

**SEMPRE prefira implementar lógica nas camadas (Business, Rules, Helpers, State) ao invés de nas views.**

- **Views devem ser "burras"**: Apenas recebem dados, delegam para o Business, e retornam resposta
- **Toda lógica de negócio** vai no `business.py`
- **Toda validação de regras** vai no `rules.py`
- **Toda query/utilitário** vai no `helpers.py`
- **Toda lógica de estado** vai no `state.py`

> **Proibições absolutas nas views:**
>
> - Views **NUNCA** fazem queries ORM diretamente (`Model.objects.get(...)`, `.filter(...)`, `.create(...)`, etc.) — toda query deve ir para o Business
> - Views **SEMPRE** herdam de exatamente **uma** view base do AppCore (`BasicPostAPIView`, `BasicGetAPIView`, `BasicRetrieveAPIView`, `BasicPutAPIView`, `BasicPatchAPIView`, `BasicDeleteAPIView`) — **`GenericAPIView` JAMAIS deve ser importado ou usado diretamente nos apps do projeto**; Views nunca devem usar herança múltipla a fim de realizar mais de uma função. Uma view tem uma única responsabilidade (ex: listar, criar, atualizar parcialmente, etc.) e herda da view base correspondente.
> - Views **NUNCA** sobrescrevem os métodos HTTP (`get`, `post`, `patch`, `put`, `delete`) sem justificativa — sempre use os hooks `do_action_*` das BasicViews. A única exceção aceita é quando a view precisa retornar `dados` na resposta (ex: objeto criado), e isso é feito **retornando um dict do hook**, não sobrescrevendo o método HTTP.
> - Views **NUNCA** definem funções soltas no nível do módulo (`def _funcao(...)`) — utilitários genéricos vão em mixins do AppCore (`RespostasMixin`, `IsOwnerOrAdminMixin`, etc.); utilitários exclusivos de um app vão em uma classe base herdada por todas as views do app; toda chamada é feita via `self.*`
> - Views **NUNCA** importam `transaction`, `handle_exceptions`, `RespostasMixin` ou chamam `transaction.atomic()` manualmente — tudo isso já é gerenciado pelas BasicViews automaticamente.
> - URLs que aceitam mais de um método HTTP usam **`roteador_por_metodo`** com views separadas — nunca uma única view com múltiplos métodos.

```python
# ❌ ERRADO - Lógica na view
def do_action_put(self, serializer_data, request):
    for attr, value in serializer_data.items():
        setattr(self.object, attr, value)
    self.object.save()

# ✅ CORRETO - View delega para business
def do_action_put(self, serializer_data, request):
    self.object.business.atualizar_dados(serializer_data)
```

### Hierarquia de Chamadas

```
View (entrada/saída)
  └── Business (orquestração)
        ├── Rules (validações)
        ├── Helpers (queries/utils)
        └── State (transições de estado)
```

**Importante:**

- Views só chamam **Business**
- Business pode chamar **Rules**, **Helpers** e **State**
- Rules, Helpers e State **NÃO** chamam uns aos outros diretamente

### 1. **Rules** (`rules.py`) - Regras de Negócio Teóricas

- **Responsabilidade**: Validar SE uma ação pode ser executada (retorna `bool` ou lança exceção)
- **Herda de**: `ModelInstanceRules` (AppCore.core.rules)
- **Não deve**: Conter lógica de persistência ou orquestração
- **Chamado por**: Business (nunca diretamente pela view)
- **Exemplo**: `UsuarioRules`, `ContaRules`

```python
from AppCore.core.rules.rules import ModelInstanceRules

class ProdutoRules(ModelInstanceRules):
    def can_delete(self):
        if self.object_instance.tem_vendas:
            self.return_exception('Produto com vendas não pode ser excluído')
        return True
```

### 2. **Business** (`business.py`) - Lógica de Negócio Prática

- **Responsabilidade**: Orquestrar COMO fazer operações (CRUD, workflows complexos)
- **Herda de**: `ModelInstanceBusiness` (AppCore.core.business)
- **Pode chamar**: Rules (validações), Helpers (queries), State (transições)
- **Chamado por**: Views (única camada que views podem chamar diretamente)
- **Captura exceções**: Define `exceptions_handled = (AuthorizationException, BusinessRuleException, ValidationException, NotFoundException)`
- **Acesso**: Via `model.business.nome_do_metodo()` após configurar o mixin

```python
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

class ProdutoBusiness(ModelInstanceBusiness):
    def criar_produto(self, **dados):
        # Business orquestra a operação completa
        regras = ProdutoRules()
        if not regras.can_create():
            raise BusinessRuleException('Não pode criar')
        return Produto.objects.create(**dados)

    def atualizar_dados(self, dados):
        '''Método padrão para atualização de dados'''
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            raise SystemErrorException('Não foi possível atualizar os dados.')
```

### 3. **Helpers** (`helpers.py`) - Queries e Utilitários

- **Responsabilidade**: Fornecer ferramentas (queries customizadas, formatações, utils)
- **Herda de**: `ModelInstanceHelpers` (AppCore.core.helpers)
- **Acesso**: Queries reutilizáveis, transformações de dados
- **Chamado por**: Business (não pela view diretamente)

```python
from AppCore.core.helpers.helpers import ModelInstanceHelpers

class ProdutoHelpers(ModelInstanceHelpers):
    def deletar_codigos_expirados(self):
        return Produto.objects.filter(validade__lt=timezone.now()).delete()
```

### 4. **State** (`state.py`) - Máquina de Estados ⚠️ FUTURO

- **Campo obrigatório**: `status` (IntegerField com choices)
- **Pattern**: Cada estado do choice é uma classe que herda de uma superclasse base
- **Métodos**: `posso_editar()`, `posso_excluir()`, `posso_ver_detalhes()` (retornam bool)
- **Acesso**: Via `model.state.FUNCAO_EXEMPLO()`
- **Status**: **Não implementado ainda** - aguardar primeiro modelo que precise de máquina de estados

```python
# FUTURO - Exemplo de como será implementado
class DocumentoState:
    def posso_aprovar(self): return False

class DocumentoPendenteState(DocumentoState):
    def posso_aprovar(self): return True

# No modelo
documento.state.posso_aprovar()  # Acessa método do estado atual
```

## Integração com Models

**Use mixins para conectar camadas ao model:**

```python
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.basics.models.models import BasicModel

class Produto(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    business_class = ProdutoBusiness  # Define a classe de business
    helper_class = ProdutoHelpers     # Define a classe de helpers

    # Acesso via propriedades
    # produto.business.criar_produto(...)
    # produto.helper.deletar_codigos_expirados()
```

## Modelos de Usuário Base

### AbstractBaseAppUser

Use `AppCore.basics.models.user_model.AbstractBaseAppUser` como base para qualquer model de usuário:

- Campos: `email` (USERNAME_FIELD padrão), `nome`, `ativo`, `is_admin`, `is_staff`, `created_at`, `updated_at`, `history`
- Propriedade `is_active` delega para `ativo` (compatível com Django auth)
- Usa `BaseManagerUser` (BaseUserManager + BaseManager)

```python
from AppCore.basics.models.user_model import AbstractBaseAppUser
from AppCore.basics.models.models import BaseManagerUser

class MeuManager(BaseManagerUser):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseAppUser):
    objects = MeuManager()
    # Para login por CPF: sobrescreva USERNAME_FIELD = 'cpf' e adicione o campo
```

Defina no `settings.py`: `AUTH_USER_MODEL = 'meuapp.Usuario'`

### Model Base (não-usuário)

**Sempre herde de `BasicModel`** para obter timestamps e histórico:

```python
from AppCore.basics.models.models import BasicModel

class MinhaModel(BasicModel):
    pass
```

### Custom Managers

- User models: herde de `BaseManagerUser` (combina `BaseUserManager` e `BaseManager`)
- Todos os managers herdam de `BaseManager`: lançam `NotFoundException` e filtram `ativo=True` por padrão no `.filter()` _(`.all()` não é sobrescrito — comportamento intencional)_

## Instruções Específicas por Domínio

- As regras detalhadas por domínio ficam em `.github/instructions/*.instructions.md`.
- Cada instrução deve ter escopo explícito e refletir o conteúdo de `docs/antigravity/rules/*.md`.
- Domínios atualmente separados:
  - Identidade
  - Organizacional
  - PessoasInstitucionais
  - Acadêmico

## Autenticação

### Sistema de Auth Genérico (AppCore)

O AppCore fornece uma hierarquia de serializers de login extensíveis:

```
AppCore/basics/auth/
├── serializers.py   BaseLoginSerializer, BaseTypedLoginSerializer
├── views.py         BaseLoginView, AtualizarTokenView, VerificarTokenView
├── urls.py          urlpatterns genéricos
└── social/
    ├── adapters.py    JWTSocialAccountAdapter (allauth)
    ├── views.py       GoogleLoginView
    ├── serializers.py SocialTokenInputSerializer
    └── urls.py
```

### Auth/ Thin App (ponto de customização do projeto)

**Não modifique o AppCore** — customize em `Auth/auth/serializers.py`:

```python
# Login simples com dados do domínio
class LoginSerializer(BaseLoginSerializer):
    def get_extra_payload(self, user):
        return {'nome': user.nome, 'is_admin': user.is_admin}

# Login com tipo de usuário (ex: motorista vs empresa)
class LoginSerializer(BaseTypedLoginSerializer):
    tipo_choices = ['motorista', 'empresa']

    def _validate_user_tipo(self, user, tipo):
        if tipo == 'motorista' and not hasattr(user, 'motorista'):
            raise AuthenticationFailed('Usuário não é motorista.')

# Login por CPF
class LoginSerializer(BaseLoginSerializer):
    username_field = 'cpf'
```

### Configuração necessária no `settings.py`

O `SIMPLE_JWT['SIGNING_KEY']` é configurado automaticamente com `SECRET_KEY` como fallback.
Em produção, defina `SIMPLE_JWT_SIGNING_KEY` no `.env`.

Endpoints disponíveis após configurar:

- `POST /auth/token_jwt/` — login
- `POST /auth/token_jwt/refresh/` — renovar token
- `POST /auth/token_jwt/verify/` — verificar token
- `POST /auth/social/google/` — login com Google (requer allauth configurado)

## Serializers - Padrão de Montagem

**Serializers devem seguir estas convenções:**

1. **Serializers de Input** (dados recebidos):
   - Use `serializers.Serializer` (não ModelSerializer)
   - Defina `write_only=True` em campos sensíveis
   - Implemente validações customizadas em `validate_<field>()` e `validate()`
2. **Validações de senha**:
   - Mínimo 8 caracteres
   - Pelo menos 1 maiúscula, 1 minúscula, 1 número, 1 caractere especial
   - Use regex para validar: `r'[A-Z]'`, `r'[a-z]'`, `r'\d'`, e caracteres especiais

3. **Validações de código**:
   - Códigos de verificação devem ter exatamente 6 dígitos

```python
from rest_framework import serializers

class CriarContaSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    senha = serializers.CharField(write_only=True)

    def validate_senha(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Senha deve ter pelo menos 8 caracteres.")
        # ... outras validações
        return value
```

## Views - Padrão Básico

**Use as views base de `AppCore.basics.views.basic_views`:**

### Tabela de Views Disponíveis

| View                   | Método | Hook a implementar                             | Objeto disponível |
| ---------------------- | ------ | ---------------------------------------------- | ----------------- |
| `BasicPostAPIView`     | POST   | `do_action_post(serializer_data, request)`     | —                 |
| `BasicGetAPIView`      | GET    | `validate_get(request, ...)` _(opcional)_      | —                 |
| `BasicRetrieveAPIView` | GET    | `validate_retrieve(request, ...)` _(opcional)_ | `self.object`     |
| `BasicPutAPIView`      | PUT    | `do_action_put(serializer_data, request)`      | `self.object`     |
| `BasicPatchAPIView`    | PATCH  | `do_action_patch(serializer_data, request)`    | `self.object`     |
| `BasicDeleteAPIView`   | DELETE | `do_action_delete(request)`                    | `self.object`     |

**Todos os hooks de escrita** (POST, PUT, PATCH, DELETE) rodam dentro de `transaction.atomic()` com savepoint automático.

**Retorno dos hooks de escrita**: dict opcional com `mensagem` e/ou `status_code` para customizar a resposta.

### Views com Responsabilidade Única

**Cada view deve herdar de exatamente UM `BasicXxxAPIView`.** Herança múltipla de views base (`BasicGetAPIView + BasicPostAPIView`, etc.) é **proibida**.

Quando um endpoint aceita mais de um método HTTP (ex: `GET` + `POST`), crie **duas views separadas** e combine-as no `urls.py` com `roteador_por_metodo`:

```python
# urls.py
from AppCore.basics.views.basic_views import roteador_por_metodo

path('recursos/', roteador_por_metodo(GET=ListarRecursosView, POST=CriarRecursoView))
path('recursos/<int:pk>/', roteador_por_metodo(GET=DetalheView, PATCH=AtualizarView))
```

```python
# views.py — cada view com UMA responsabilidade

# ✅ CORRETO — view de listagem
@extend_schema(...)  # @extend_schema na CLASSE quando usa apenas hooks
class ListarSetoresView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = SetorSerializer
    mensagem_sucesso = 'Setores listados com sucesso.'

    def get_queryset(self):
        return Setor.objects.all()


# ✅ CORRETO — view de criação com retorno de dados (sobrescrita justificada)
class CriarSetorView(IsAdminMixin, RespostasMixin, BasicPostAPIView):
    serializer_class = CriarSetorSerializer

    @extend_schema(...)  # @extend_schema no MÉTODO quando há sobrescrita justificada
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                setor = SetorBusiness().criar_setor(**serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        return self.resposta_sucesso('Setor criado!', SetorSerializer(setor).data, status.HTTP_201_CREATED)


# ❌ ERRADO — herança múltipla de BasicXxx views
class SetoresView(IsAdminMixin, RespostasMixin, BasicGetAPIView, BasicPostAPIView):
    http_method_names = ['get', 'post']
    ...
```

### Quando sobrescrever métodos HTTP (get, post, patch, put, delete)

> ⚠️ **NUNCA sobrescreva métodos HTTP sem justificativa.** Este é o erro mais comum e recorrente. Sempre use os hooks `do_action_*`.

O objetivo das `BasicXxxAPIViews` é **minimizar código nas views**. Sobrescrever `get`, `post`, `patch`, `put` ou `delete` é **proibido** como padrão.

**A única exceção aceita** é quando `do_action_*` precisa retornar dados na resposta (objeto criado/atualizado). Isso é feito **retornando um dict do hook** — não sobrescrevendo o método HTTP:

```python
# ✅ CORRETO — retornar dados via hook (sem sobrescrita de método)
def do_action_post(self, serializer_data, request, *args, **kwargs):
    setor = SetorBusiness().criar_setor(**serializer_data)
    return {
        'mensagem': self.mensagem_sucesso,
        'dados': SetorSerializer(setor).data,
        'status_code': status.HTTP_201_CREATED,
    }

# ❌ ERRADO — sobrescrita do método HTTP
def post(self, request, *args, **kwargs):
    ...
    return self.resposta_sucesso(...)
```

**Nunca importe ou use** `transaction`, `handle_exceptions`, `RespostasMixin`, `GenericAPIView` nas views dos apps do projeto — as BasicViews já gerenciam tudo isso.

### Posição do `@extend_schema`

- **Sempre** na **CLASSE** — as views usam apenas hooks (`do_action_*`), não sobrescrevem métodos HTTP.

### Exemplo (padrão obrigatório)

```python
from AppCore.basics.views.basic_views import BasicPostAPIView

@extend_schema(
    tags=['Produtos'],
    summary='Desativar produto',
    ...
)
class DesativarProdutoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Produto desativado com sucesso.'
    queryset = Produto.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()
```

### Tratamento de Exceções

As views básicas **capturam automaticamente** e retornam HTTP adequado:

- `BusinessRuleException` → 400 Bad Request
- `ValidationException` → 400 Bad Request
- `AuthorizationException` → 403 Forbidden
- `NotFoundException` → 404 Not Found
- `SystemErrorException` → 500 Internal Server Error

## Permissions - Padrão

Use os mixins de `AppCore.basics.mixins.mixins`:

- `AllowAnyMixin` — endpoints públicos (sem autenticação)
- `IsOwnerOrAdminMixin` — dono do recurso ou admin
  - Usa `getattr(user, 'is_admin', False)` — campo `is_admin` é opcional no model
  - Requer implementar `obter_usuario_dono(obj)` na view
- `IsAdminMixin` — apenas superusuários ou `is_admin=True`

Permissões padrão do DRF: `IsAuthenticated` (configurado no REST_FRAMEWORK).

## Exceções Customizadas

**Sempre use exceções do AppCore** (`AppCore.core.exceptions.exceptions`):

- `BusinessRuleException` - Regra de negócio violada
- `ValidationException` - Dados inválidos
- `AuthorizationException` - Sem permissão
- `NotFoundException` - Objeto não encontrado (auto-lançada pelos managers)
- `SystemErrorException` - Erro interno do sistema

## Convenções de Código

### Estrutura de Apps

**Regra: cada app corresponde a um model principal.** É incomum que um `models.py` declare mais de um model. Exceções aceitas:

- **Tabelas de domínio** (choices/lookups simples sem lógica própria)
- **Tabelas auxiliares** ou de suporte ao model principal
- **Tabelas M:N com campos extras** (through tables) quando não justificarem um app próprio
- **Lógica de negócio que autorize** dois models juntos (ex: model + seu histórico manual)

Na dúvida, crie um app separado.

```
AppNome/
├── __init__.py
├── apps.py
├── business.py      # Lógica de negócios (opcional)
├── choices.py       # Choices para campos (opcional)
├── rules.py         # Regras de validação (opcional)
├── helpers.py       # Queries e utilitários (opcional)
├── models.py        # Models Django
├── serializers.py   # DRF Serializers
├── state.py         # Classes de estados e máquina de estados (opcional)
├── views.py         # DRF Views
└── urls.py          # URL routing
```

### Estilo de Código

- **Aspas simples**: SEMPRE use `'texto'` (nunca aspas duplas)
- **Imports**: Organizados (stdlib → Django → DRF → AppCore → apps locais)
- **Nomes**:
  - Módulos principais: PascalCase (`AppCore`, `Cortex`)
  - Apps: snake_case minúsculo (`usuarios`, `auth`)
  - Arquivos: snake_case (`business.py`, `helpers.py`)
- **Nomenclatura em Português**:
  - Variáveis e funções: português (`mensagem_sucesso`, `obter_usuario_dono()`)
  - Estruturas de pastas: `AppCore/common/textos/` (emails, mensagens)
  - Funções utilitárias: `enviar_email_simples()` (não `send_simple_email()`)

### Localização

- Idioma: Português (pt-BR)
- Timezone: `America/Fortaleza`
- Verbose names em português: `verbose_name='Usuário'`

## Comandos Essenciais

### Desenvolvimento

```bash
# Ativar ambiente virtual
venv\Scripts\activate

# Rodar servidor
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Celery Worker (Linux/Mac)
celery -A Cortex worker -l INFO

# Celery Worker (Windows - requer pool=solo para funcionar corretamente)
celery -A Cortex worker -l INFO --pool=solo
```

### Criar Novo App

**Script `create_app.py` está vazio** - criar apps manualmente:

```bash
mkdir NomeApp
cd NomeApp
# Criar: __init__.py, apps.py, models.py, business.py, rules.py, helpers.py, serializers.py, views.py, urls.py
```

## Stack Técnica

- **Django 5.2.7** + **DRF 3.16.1**
- **Auth**: SimpleJWT (tokens 30min/7 dias) + django-allauth 65.9.0 (login social)
- **Database**: PostgreSQL (dev usa SQLite)
- **Background Tasks**: Celery 5.4.0 + Redis 5.0.3 (usado para importações assíncronas)
- **Docs API**: drf-spectacular (Swagger/ReDoc em `/api/schema/swagger/`)
- **Auditoria**: django-simple-history (histórico automático em models)
- **Email**: SMTP (padrão Gmail, configurável via env)

## Segurança (comportamentos obrigatórios)

- **`except Exception` genérico** nunca deve retornar `str(err)` ao cliente (OWASP A03). Sempre use `RESPONSE_ERRO_INTERNO_SERVIDOR` e logue o erro com `logging.getLogger`.
- **`SECRET_KEY`** nunca deve ter valor hardcoded. O `ImproperlyConfigured` é lançado em produção (`DEBUG=False`) se a chave for o valor default.
- **CORS**: `CORS_ALLOW_ALL_ORIGINS = False` por padrão. Configure via env `CORS_ALLOW_ALL_ORIGINS=True` apenas em dev.
- **`is_admin`**: sempre acesse com `getattr(user, 'is_admin', False)` em código genérico, pois o campo é opcional dependendo do model de usuário do projeto.

## Paginação

O projeto usa uma classe de paginação customizada (`AppCore.basics.pagination.pagination.PaginacaoCustomizada`):

- **Tamanho padrão**: 10 itens por página
- **Query param**: `paginacao` - permite definir o tamanho da página dinamicamente
- **Limites**: Mínimo 1, Máximo 100
  - Valores menores que 1 são ajustados para 1
  - Valores maiores que 100 são ajustados para 100

```python
# Exemplos de uso:
# /api/usuarios/              → 10 itens (padrão)
# /api/usuarios/?paginacao=25 → 25 itens
# /api/usuarios/?paginacao=0  → 1 item (mínimo)
# /api/usuarios/?paginacao=500 → 100 itens (máximo)
```

## Query Params em Endpoints de Listagem

**Princípio obrigatório:** query params apenas reduzem o conjunto de resultados — **nunca expandem o acesso além do que a permissão do usuário já permite**.

### Regras

1. A filtragem por query params é aplicada **após** o escopo de permissão estar estabelecido (URL context + verificação de acesso).
2. Em endpoints de sub-recursos com `usuario_pk` na URL, o queryset já está restrito ao usuário. Filtros adicionais nunca podem retornar dados de outro usuário.
3. Valores de query param inválidos (fora do domínio esperado) devem ser **ignorados silenciosamente** — não retornam erro, apenas não filtram.

### Implementação padrão

```python
def get_queryset(self):
    # 1. Escopo base — já restrito pela URL ou permissão
    qs = Modelo.objects.filter(usuario_id=self.kwargs['usuario_pk'])

    # 2. Filtros adicionais via query param — só reduzem o escopo
    situacao = self.request.query_params.get('situacao')
    if situacao is not None:
        try:
            situacao_int = int(situacao)
            if situacao_int in SituacaoModelo.values:   # valida domínio
                qs = qs.filter(situacao=situacao_int)
        except (ValueError, TypeError):
            pass  # valor inválido: ignora silenciosamente

    return qs
```

Para filtros booleanos (ex: `?ativo=true|false`):

```python
ativo = self.request.query_params.get('ativo')
if ativo is not None and ativo.lower() in ('true', 'false'):
    qs = qs.filter(ativo=ativo.lower() == 'true')
```

### Documentação Swagger obrigatória para query params

Todo query param deve ser declarado em `@extend_schema(parameters=[...])`:

```python
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

@extend_schema(
    parameters=[
        OpenApiParameter(
            'situacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por situação: 1 = Ativa, 2 = Inativa.',
            enum=[1, 2],
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    ...
)
```

A descrição deve mencionar explicitamente que **"query params apenas reduzem o conjunto, nunca expandem o acesso"**.

## Documentação da API (Swagger/OpenAPI)

**OBRIGATÓRIO**: Toda view deve ter documentação completa usando `drf-spectacular`.

### Decorador @extend_schema

Sempre adicione o decorador `@extend_schema` em todas as views:

```python
from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    tags=['NomeDoModulo'],
    summary='Descrição curta da operação',
    description='''
    Descrição detalhada da operação.

    **Permissões:** Quem pode acessar
    **Paginação:** Informações sobre paginação (se aplicável)

    **Retorno:**
    - Lista dos campos retornados
    ''',
    request=SerializerDeInput,  # Para POST/PUT
    responses={
        status.HTTP_200_OK: SerializerDeOutput,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão'},
        status.HTTP_404_NOT_FOUND: {'description': 'Não encontrado'},
    },
    examples=[  # Opcional, mas recomendado
        OpenApiExample(
            'Exemplo de Requisição',
            value={'campo': 'valor'},
            request_only=True,
        ),
    ],
)
class MinhaView(BasicGetAPIView):
    ...
```

### Padrões de Tags

Use tags consistentes para agrupar endpoints no Swagger:

- `Auth` - Autenticação e tokens
- `Usuarios` - Operações de usuários
- `Usuarios.Password reset` - Reset de senha
- `Campus`, `Setores`, `Empresas`, etc. - Entidades do domínio

### Serializers para Documentação

Para endpoints de input (POST/PUT), crie serializers separados quando necessário:

- `SerializerInput` - Para documentar o request body
- `SerializerResponse` - Para documentar a resposta

Veja exemplo em `Auth.auth.serializers` com `LoginInputSerializer` e `LoginResponseSerializer`.

## URLs e Estrutura de Rotas

- `Cortex/urls.py` inclui os módulos de domínio (`Identidade.urls`, `Organizacional.urls`)
- O `urls.py` de cada módulo de domínio agrega as rotas dos apps internos
- Apps internos **não** são incluídos diretamente em `Cortex/urls.py`
- Documentação: `/api/schema/`, `/api/schema/swagger/`, `/api/schema/redoc/`

## Testing

O projeto **inclui testes** como parte da implementação normal. Cada app interno deve conter um diretório `tests/` com testes unitários e de integração relevantes.

Testes são exigidos para avançar entre milestones — veja `docs/planning/master-implementation-plan.md`.

## Deploy (Futuro)

**Planejado mas não configurado**:

- Deploy com Docker
- Server: Gunicorn (Linux) / Waitress (Windows)
- Static files: WhiteNoise (já configurado)

---

## Modelos do Domínio (DER/Diagrama de Classes)

Abaixo está o resumo dos modelos, seus relacionamentos e o status de implementação atual. Os modelos marcados como **implementado** já possuem app interno criado e funcional.

### Autenticação

- **Login por CPF** (não email)
- **Criação de usuários**: Via JSON por admin (individual ou em lote) ou por portal Admin
- **Não há auto-cadastro**: Usuários são criados por administradores

### Hierarquia de Herança

```
                    Usuario
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │              │              │
    Servidor      Terceirizado     Aluno       Estagiario
```

### Modelos e Relacionamentos

| Modelo                 | Status          | App interno                                    | Relacionamentos                                           |
| ---------------------- | --------------- | ---------------------------------------------- | --------------------------------------------------------- |
| **Usuario**            | ✅ Implementado | `Identidade/usuarios/`                         | Classe base central (login CPF); 1:N com Contato/Endereco |
| **Contato**            | ✅ Implementado | `Identidade/contatos/`                         | N:1 com Usuario                                           |
| **Endereco**           | ✅ Implementado | `Identidade/enderecos/`                        | N:1 com Usuario                                           |
| **Matricula**          | ✅ Implementado | `Identidade/matriculas/`                       | N:1 com Usuario                                           |
| **Setor**              | ✅ Implementado | `Organizacional/setores/`                      | M:N com Usuario via SetorVinculo                          |
| **Funcao**             | ✅ Implementado | `Organizacional/funcoes/`                      | Entidade independente; usada em SetorVinculo              |
| **SetorVinculo**       | ✅ Implementado | `Organizacional/vinculos/`                     | N:1 com Usuario, N:1 com Setor, N:1 com Funcao            |
| **Cargo**              | ✅ Implementado | `PessoasInstitucionais/cargos/`                | Entidade independente                                     |
| **Servidor**           | ✅ Implementado | `PessoasInstitucionais/servidores/`            | OneToOne com Usuario, N:1 com Cargo                       |
| **EmpresaInstituicao** | ✅ Implementado | `PessoasInstitucionais/empresas_instituicoes/` | 1:N com Terceirizado                                      |
| **Terceirizado**       | ✅ Implementado | `PessoasInstitucionais/terceirizados/`         | OneToOne com Usuario, N:1 com EmpresaInstituicao          |
| **Aluno**              | ✅ Implementado | `Academico/alunos/`                            | OneToOne com Usuario                                      |
| **Curso**              | ✅ Implementado | `Academico/cursos/`                            | M:N com Aluno via AlunoCurso                              |

### Apps Internos por Módulo de Domínio

A ordem de criação respeita as dependências entre domínios. Apps dentro do mesmo módulo seguem a ordem abaixo:

**Módulo `Identidade/`** (Milestone 1 — concluído):

1. `Identidade/usuarios/` — Model: `Usuario` (base de autenticação; sem dependências externas)
2. `Identidade/contatos/` — Model: `Contato` (depende de `usuarios`)
3. `Identidade/enderecos/` — Model: `Endereco` (depende de `usuarios`)
4. `Identidade/matriculas/` — Model: `Matricula` (depende de `usuarios`)

**Módulo `Organizacional/`** (Milestone 2 — concluído):

5. `Organizacional/setores/` — Model: `Setor` (sem dependências externas)
6. `Organizacional/funcoes/` — Model: `Funcao` (sem dependências externas)
7. `Organizacional/vinculos/` — Model: `SetorVinculo` (depende de `usuarios`, `setores`, `funcoes`)

**Módulo `PessoasInstitucionais/`** (Milestone 3 — concluído):

8. `PessoasInstitucionais/cargos/` — Model: `Cargo` (sem dependências externas)
9. `PessoasInstitucionais/servidores/` — Model: `Servidor` (depende de `usuarios`, `cargos`)
10. `PessoasInstitucionais/empresas_instituicoes/` — Model: `EmpresaInstituicao` (sem dependências externas)
11. `PessoasInstitucionais/terceirizados/` — Model: `Terceirizado` (depende de `usuarios`, `empresas_instituicoes`)

**Módulo `Academico/`** (Milestone 4 — concluído):

12. `Academico/alunos/` — Model: `Aluno` (depende de `usuarios`)
13. `Academico/cursos/` — Model: `Curso` (sem dependências externas)
14. `Academico/aluno_cursos/` — Model: `AlunoCurso` (depende de `alunos`, `cursos`)

### Choices Definidos

- **Status genérico**: `STATUS_ATIVO`, `STATUS_INATIVO`
- **Situação do Aluno**: `MATRICULADO`, `TRANCADO`, `FORMADO`, `DESISTENTE`, `TRANSFERIDO`
- **Turno**: `MATUTINO`, `VESPERTINO`, `NOTURNO`, `INTEGRAL`
- **Forma de Ingresso**: `VESTIBULAR`, `ENEM`, `TRANSFERENCIA`, `REINGRESSO`
- **Jornada de Trabalho Servidor**: `20`, `40`, `0` (Dedicação Exclusiva)

### Padrão de Herança nos Models

Usamos **OneToOneField com primary_key=True** para herança:

```python
class Servidor(BasicModel):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='servidor',
        primary_key=True,
    )
    # campos específicos do servidor...

class Aluno(BasicModel):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='aluno',
        primary_key=True,
    )
    # campos específicos do aluno...
```

### Usuario - Configuração de Autenticação

```python
class Usuario(AbstractBaseUser, BasicModel):
    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome']

    # campos...
    cpf = models.CharField('CPF', max_length=11, unique=True)
    nome = models.CharField('Nome', max_length=255)
    # ...
```

### SetorVinculo — Tabela Associativa

Representa o vínculo entre um usuário e um setor. A função desempenhada pelo usuário no setor (incluindo monitoria) é representada pelo FK `funcao`, não por booleanos.

```python
class SetorVinculo(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, ...)
    setor = models.ForeignKey('setores.Setor', on_delete=models.CASCADE, ...)
    funcao = models.ForeignKey('funcoes.Funcao', on_delete=models.PROTECT, ...)
    responsavel = models.BooleanField('Responsável', default=False)
```

### Criação de Usuários (Via Admin JSON)

- Usuários são criados por administradores via endpoint específico
- Suporte a criação individual ou em lote via JSON
- Não há fluxo de auto-cadastro com envio de email

### Convenção de nomenclatura para métodos e funções

- Não misture inglês e português em nomes de métodos, funções e variáveis do domínio.
- Prefira nomes em português para métodos e funções implementados no projeto.
- Use inglês apenas quando isso for exigido por sobrescrita de framework, convenção do Django/DRF/Python ou interface externa.

**Exemplos corretos:**

- `obter_contatos()`
- `criar_usuario()`
- `atualizar_dados()`

**Evitar:**

- `get_contatos()`
- `create_usuario()`
- `update_dados()`

**Exceções aceitáveis:**

- métodos exigidos por sobrescrita ou convenção, como:
  - `get_queryset`
  - `get_serializer_class`
  - `validate`
  - `create`
  - `update``

## Estrutura física do projeto

### Domínios e apps

No Cortex, **domínio não é app**.

Um domínio representa um contexto de negócio e deve ser estruturado como um **módulo agregador**, contendo um ou mais apps internos.

Exemplos de módulos de domínio:

- `Identidade/`
- `Organizacional/`
- `PessoasInstitucionais/`
- `Academico/`

### Regra preferencial de modelagem física

A regra padrão do projeto é:

- **cada app corresponde a um model principal**

Exceções aceitas:

- tabelas de domínio;
- tabelas auxiliares;
- relações many-to-many sem lógica própria relevante;
- casos explicitamente aprovados pelo usuário.

Na dúvida, prefira separar em apps menores.

### Estrutura esperada

Exemplo de módulo de domínio:

```text
Identidade/
├── __init__.py
├── urls.py
├── usuarios/
├── contatos/
├── enderecos/
└── matriculas/
```

Exemplo de app interno:

```text
usuarios/
├── __init__.py
├── apps.py
├── models.py
├── business.py
├── rules.py
├── helpers.py
├── serializers.py
├── views.py
├── urls.py
├── tests.py
└── migrations/
```

### Regras obrigatórias

- Apps Django **não devem ficar soltos na raiz do repositório**.
- Apps devem ficar dentro do módulo de domínio correspondente.
- O `Cortex/urls.py` deve incluir o **módulo de domínio**, nunca os apps internos diretamente.
- O `urls.py` do módulo de domínio é o agregador das rotas dos apps internos.
- O `PROJECT_APPS` no `settings.py` deve registrar os apps internos.
- O `AUTH_USER_MODEL` deve apontar para o app interno que contém o model real do usuário.

### Arquitetura em camadas

Cada app deve seguir a arquitetura em camadas do projeto.

Em regra, um app interno deve conter:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`
- `tests.py`

Arquivos opcionais:

- `choices.py`
- `state.py`

### Views leves

As views devem continuar extremamente leves:

- recebem dados;
- delegam para o Business;
- retornam a resposta.

Views não devem conter lógica de negócio, queries ORM diretas, nem implementação manual de fluxo já coberto pelas BasicViews.

### Convenção de nomenclatura

- Não misture inglês e português em nomes de métodos, funções e variáveis do domínio.
- Prefira português para código do domínio.
- Use inglês apenas em sobrescritas obrigatórias de framework, convenções do Django/DRF/Python ou interfaces externas.

Exemplos corretos:

- `obter_contatos()`
- `criar_usuario()`
- `atualizar_dados()`

Evitar:

- `get_contatos()`
- `create_usuario()`
- `update_dados()`

### Regras práticas

- Não criar apps diretamente na raiz do repositório.
- Não criar um módulo técnico genérico como `Apps/` apenas para agrupar tudo.
- Ao criar um novo app, ele deve ser colocado dentro do módulo de domínio adequado.
- Mesmo que um módulo de domínio tenha apenas um app inicialmente, ele deve ser estruturado de forma a permitir crescimento futuro.
- A organização física deve seguir a linguagem do domínio do projeto.

### Convenção de nomenclatura no `apps.py`

O campo `name` do `AppConfig` deve sempre refletir o caminho Python completo do app dentro do módulo:

```python
class UsuariosConfig(AppConfig):
    name = 'Identidade.usuarios'  # caminho completo: Módulo.app
    verbose_name = 'Usuários'
```

O `label` (usado em `AUTH_USER_MODEL`, migrations e referencias de model) é derivado automaticamente do **último segmento** do `name` — não precisa ser declarado explicitamente, a menos que haja conflito de nomes entre apps.

### `urls.py` do módulo de domínio — obrigatório

Cada módulo de domínio **deve ter um `urls.py`** próprio na raiz do módulo. Esse arquivo:

- define `app_name` com o nome do domínio (em minúsculo);
- inclui as URLs de cada app do módulo;
- é o **único ponto de entrada** registrado no `Cortex/urls.py`.

```python
# Identidade/urls.py
from django.urls import path, include

app_name = 'identidade'

urlpatterns = [
    path('', include('Identidade.usuarios.urls')),
    path('', include('Identidade.contatos.urls')),
    path('', include('Identidade.enderecos.urls')),
    path('', include('Identidade.matriculas.urls')),
]
```

Cada include pode receber um prefixo se houver convenção de rota, por exemplo `path('contatos/', include('Identidade.contatos.urls'))`. A estrutura real do projeto atual omite prefixos, deixando a responsabilidade para os `urls.py` de cada app.

O app interno **não deve ter `app_name`** em seu `urls.py` — o namespace é gerenciado pelo módulo.

O `Cortex/urls.py` inclui **sempre o módulo**, nunca o app diretamente:

```python
# ✅ correto — aponta para o módulo
path('identidade/', include('Identidade.urls')),

# ❌ errado — acessa o app diretamente, bypassa o agregador do módulo
# path('identidade/', include('Identidade.identidade.urls')),
```

### Estrutura mínima de um módulo de domínio

```
Identidade/                  ← módulo de domínio (PascalCase)
├── __init__.py              ← torna o diretório um pacote Python
├── urls.py                  ← agregador de rotas do módulo (app_name obrigatório)
├── usuarios/                ← app Django (minúsculo)
│   ├── __init__.py
│   ├── apps.py              ← name = 'Identidade.usuarios'
│   ├── urls.py              ← sem app_name
│   └── ...
├── contatos/
│   └── ...
└── enderecos/
    └── ...
```

### Convenção de nomenclatura para métodos e funções

- Não misture inglês e português em nomes de métodos, funções e variáveis do domínio.
- Prefira nomes em português para métodos e funções implementados no projeto.
- Use inglês apenas quando isso for exigido por sobrescrita de framework, convenção do Django/DRF/Python ou interface externa.

**Exemplos corretos:**

- `obter_contatos()`
- `criar_usuario()`
- `atualizar_dados()`

**Evitar:**

- `get_contatos()`
- `create_usuario()`
- `update_dados()`

**Exceções aceitáveis:**

- métodos exigidos por sobrescrita ou convenção, como:
  - `get_queryset`
  - `get_serializer_class`
  - `validate`
  - `create`
  - `update`
