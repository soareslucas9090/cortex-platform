---
name: corrigir-testes
description: "Executa todos os testes do projeto Cortex/DRF, identifica falhas e corrige a origem correta de cada erro: seja no código testado (view, business, serializer, model) ou no próprio teste (escrito para uma versão anterior). Use quando: testes estão falhando; após refatorar views ou business; ao atualizar uma feature e os testes quebrarem; para validar se a implementação está correta."
argument-hint: "Opcional: módulo ou app específico (ex: Identidade.usuarios, Organizacional). Deixe vazio para rodar todos."
user-invocable: true
---

# Corrigir Testes — Projeto Cortex

## Objetivo

Rodar os testes do projeto, diagnosticar cada falha, decidir onde está o problema (teste desatualizado vs código com bug) e aplicar a correção certa — sem nunca mascarar uma falha real apagando asserções ou tornando o teste trivial.

---

## Processo Passo a Passo

### 1. Rodar os testes

Se um módulo/app foi especificado como argumento, rodar apenas aquele escopo. Caso contrário, rodar todos:

```bash
# Todos os testes
python manage.py test --verbosity=2

# Apenas um módulo de domínio
python manage.py test Identidade --verbosity=2

# Apenas um app específico
python manage.py test Identidade.usuarios --verbosity=2
```

Capturar **toda** a saída: número de testes, falhas, erros e o traceback completo de cada um.

---

### 2. Triagem: classificar cada falha

Para cada teste falhando, ler:

- O traceback completo
- O arquivo de teste (`tests/test_views.py` ou similar)
- O arquivo de código sendo testado (view, business, serializer, etc.)

Classificar a falha em uma das categorias:

| Categoria               | Critério                                                                                                     |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Bug no código**       | O teste descreve comportamento correto, mas a implementação está errada ou incompleta                        |
| **Teste desatualizado** | A implementação mudou (refatoração, renomeação, nova assinatura) e o teste ainda aponta para a versão antiga |
| **Configuração**        | Problema de URL, namespace, `setUp`, fixtures ou dependência entre testes                                    |
| **Ambíguo**             | Não é possível determinar sem mais contexto — registrar e perguntar ao usuário                               |

> ⚠️ **Regra fundamental**: nunca classificar como "teste desatualizado" apenas porque é mais fácil de corrigir. O teste deve ser respeitado como a especificação do comportamento esperado, a menos que haja evidência clara de que ele foi escrito para uma versão anterior.

---

### 3. Diagnóstico por categoria

#### Bug no código

- Ler o traceback e o código da view/business/serializer
- Identificar o ponto exato da falha (`AttributeError`, `AssertionError`, resposta inesperada, etc.)
- Verificar se viola algum padrão do `regras-do-projeto.md` (ex: query ORM na view, hook retornando `Response` diretamente, exceção exposta ao cliente)

#### Teste desatualizado

Evidências que confirmam que o teste é o problema:

- O teste referencia URL, campo, parâmetro ou status code que foi intencionalmente alterado
- O teste usa `reverse()` com um nome de rota que foi renomeado
- O teste envia um payload com campos que foram removidos ou renomeados no serializer
- O teste espera um status code diferente do atual comportamento documentado

#### Configuração

- Checar `urls.py` do módulo de domínio (ex: `Identidade/urls.py`) se o erro for `NoReverseMatch`
- Checar `INSTALLED_APPS` e `apps.py` se o erro for de importação
- Checar `setUp` se o erro ocorrer antes do teste em si (`ERROR` vs `FAIL`)

---

### 4. Aplicar a correção

#### Se for **bug no código**:

- Corrigir a implementação (view, business, rules, helpers, serializer, model)
- **Não modificar o teste**
- Seguir os padrões da arquitetura (ver `regras-do-projeto.md`):
  - Views herdam de `BasicXxxAPIView` e usam hooks `do_action_*`
  - Business orquestra queries e lógica
  - Exceções do AppCore (`BusinessRuleException`, `NotFoundException`, etc.)

#### Se for **teste desatualizado**:

- Corrigir o teste para refletir o comportamento atual e correto
- **Não alterar a lógica de negócio** apenas para o teste passar
- Manter a intenção original do teste (o que ele quer validar)
- Atualizar: nomes de URL (`reverse()`), campos do payload, status codes esperados, estrutura da resposta

#### Se for **configuração**:

- Corrigir o `urls.py`, `apps.py`, ou `setUp` conforme necessário
- Não inventar fixtures — usar `create_user` ou `Model.objects.create` como nos testes existentes

---

### 5. Verificar a correção

Após cada correção, rodar novamente apenas os testes que estavam falhando:

```bash
python manage.py test Identidade.usuarios.tests.test_views.CriarUsuarioViewTest --verbosity=2
```

Se o teste passar, prosseguir para o próximo. Se continuar falhando, revisar o diagnóstico antes de tentar outra abordagem.

---

### 6. Rodar a suíte completa

Após corrigir todos os testes identificados, rodar a suíte completa novamente para garantir que nenhuma correção quebrou outro teste:

```bash
python manage.py test --verbosity=2
```

Confirmar: **0 failures, 0 errors**.

---

## Estrutura dos Testes no Projeto

```
Identidade/
└── usuarios/
    └── tests/
        ├── __init__.py
        └── test_views.py
Organizacional/
└── organizacional/
    └── tests/
        ├── __init__.py
        └── test_views.py
```

### Padrão dos arquivos de teste

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False, **kwargs):
    return Usuario.objects.create_user(cpf=cpf, password=password, nome=nome, is_admin=is_admin, **kwargs)


class MinhaViewTest(APITestCase):

    def setUp(self):
        self.usuario = criar_usuario('00000000001', is_admin=True)
        self.token = obter_tokens(self.usuario)
        self.url = reverse('identidade:nome-da-url')

    def test_caso_de_uso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
```

---

## Checklist de Qualidade da Correção

Antes de declarar um teste corrigido, verificar:

- [ ] O teste descreve um comportamento que **deveria** acontecer (não apenas "o que acontece hoje")
- [ ] O status HTTP está correto para a operação (200 GET, 201 POST de criação, 204 DELETE, 400 validação, 401 sem auth, 403 sem permissão, 404 não encontrado)
- [ ] A URL usa `reverse()` com o namespace do módulo de domínio (ex: `'identidade:usuarios'`)
- [ ] O payload do teste bate com os campos do serializer atual
- [ ] O `setUp` não depende de ordem de execução entre testes
- [ ] Nenhum teste foi tornado trivial (asserções removidas ou substituídas por `pass`)
- [ ] A correção no código segue os padrões da arquitetura (sem queries ORM na view, sem lógica no hook, etc.)

---

## Casos Especiais

### `NoReverseMatch`

Verificar na ordem:

1. Nome da URL em `reverse()` (ex: `'identidade:usuarios'`)
2. `app_name` no `urls.py` do módulo (ex: `Identidade/urls.py`)
3. `include()` correto no `Cortex/urls.py`
4. Kwargs obrigatórios (ex: `kwargs={'usuario_pk': self.usuario.pk}`)

### `AssertionError` em status code

Fazer a requisição com `print(resposta.data)` mentalmente — ler o traceback com atenção ao valor real vs esperado. Verificar:

- Permissões da view (`IsAdminMixin`, `IsOwnerOrAdminMixin`, `AllowAnyMixin`)
- Se o objeto existe no banco no momento do teste
- Se o `setUp` criou todos os dados necessários

### `AttributeError: 'NoneType' object has no attribute ...`

Geralmente o `setUp` não criou um objeto que o teste assume existir, ou a view retorna `None` onde não deveria.

### Falha em cadeia (muitos testes com o mesmo erro)

Resolver o problema raiz primeiro (ex: URL errada, model sem migration) antes de tentar corrigir cada teste individualmente.
