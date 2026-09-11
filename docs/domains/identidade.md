# Diretrizes do Domínio: Identidade

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Identidade** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Identidade` é responsável pela autenticação, perfis de usuários e informações básicas de contato e endereço.

### Modelos e Relacionamentos

- **Usuario**: Classe base central do sistema (autenticação por e-mail, CPF ou matrícula). Possui relacionamento 1:N com `Contato` e `Endereco`.
- **Contato**: Informações de contato do usuário (relacionamento N:1 com `Usuario`).
- **Endereco**: Endereços do usuário (relacionamento N:1 com `Usuario`).

A **matrícula** não é entidade própria em Identidade: ela vive como atributo opcional em `AlunoCurso`, `Servidor` e `Terceirizado`. Normalização em `AppCore/common/util/util.py` (`normalizar_matricula`); busca por login, elegibilidade e unicidade global em `Usuario().helper` e `Usuario().rules` (`Identidade/usuarios/helpers.py` e `rules.py`).

### Estrutura de Apps

```text
Identidade/
├── __init__.py
├── urls.py
├── usuarios/        # App Django do model Usuario (helpers/rules de matrícula)
├── contatos/        # App Django do model Contato
└── enderecos/       # App Django do model Endereco
```

---

## Regras Específicas do Domínio

### 1. Autenticação e Usuários
- **Login híbrido**: O endpoint aceita **e-mail**, **CPF** ou **matrícula** no campo `login` (`EmailOrCpfBackend`).
- **Fontes da matrícula**: Para autenticação e elegibilidade, a matrícula é resolvida em vínculos ativos de `AlunoCurso`, `Servidor` ou `Terceirizado`.
- **Elegibilidade**: Após localizar o usuário, o backend exige **CPF** ou **matrícula válida** em uma das três fontes para permitir login.
- **Não há auto-cadastro**: Usuários não podem se cadastrar sozinhos no sistema. A criação é feita exclusivamente por administradores.
- **Criação de Usuários**: Deve suportar criação individual ou em lote via payload JSON por um administrador ou via portal Admin. Não há fluxo de envio de e-mail para confirmação automática de cadastro.
- **Usuário coletivo**: flag `usuario_coletivo` na criação/edição do usuário. Conta compartilhada (ex.: guarita) usada na operação de Infraestrutura. O pool de associações (empresas, cargos, funções, setores) **não** é enviado na criação; é configurado em endpoints dedicados:
  - `GET/PUT /usuarios/{pk}/coletivo/` — consultar e substituir o pool
  - `POST /usuarios/{pk}/coletivo/itens/` — adicionar item (`tipo` + `id`)
  - `DELETE /usuarios/{pk}/coletivo/itens/{tipo}/{item_id}/` — remover item
  - Ao desativar a flag, o pool é limpo automaticamente.
  - Conta coletiva não pode ser solicitante nem responsável de empréstimo.
  - No cadastro, o **CPF é opcional**; sem CPF, a **matrícula é obrigatória** (identificador de login: e-mail, CPF ou matrícula).

#### Alteração de senha de acesso

Usuários autenticados podem alterar a **própria** senha de acesso via:

- **Endpoint:** `POST /cortex/identidade/usuarios/alterar-senha/`
- **Permissão:** qualquer usuário autenticado (L1–L3); requer `Authorization: Bearer <access_token>`
- **Tag Swagger:** `Usuarios`

**Request:**

```json
{
  "senha_atual": "Senha@123",
  "nova_senha": "NovaSenha@456"
}
```

**Response `200`:**

```json
{
  "status": "success",
  "mensagem": "Senha alterada com sucesso."
}
```

**Fluxo interno (View → Business → Rules):**

1. `AlterarSenhaView` valida o payload com `AlterarSenhaSerializer` e delega a `request.user.business.alterar_senha(...)`.
2. `UsuarioRules.pode_alterar_senha()` — bloqueia usuário inativo ou conta coletiva (`usuario_coletivo=True`).
3. `UsuarioRules.validar_senha_atual()` — confere a senha atual com `check_password`; em falha retorna `400` com mensagem genérica *"Senha atual incorreta."*.
4. `validar_senha()` (`AppCore.common.util.util`) — aplica a política de complexidade no Business.
5. `UsuarioBusiness.alterar_senha()` — impede reutilizar a senha atual e persiste com `set_password` + `save(update_fields=['password'])`.

**Política de complexidade da nova senha:**

- Mínimo 8 caracteres
- Pelo menos 1 letra maiúscula, 1 minúscula, 1 número e 1 caractere especial
- Deve ser **diferente** da senha atual

**Restrições e erros comuns:**

| Situação | HTTP | Mensagem / comportamento |
| -------- | ---- | ------------------------ |
| Token ausente ou inválido | `401` | Não autenticado |
| Senha atual incorreta | `400` | *Senha atual incorreta.* |
| Nova senha fraca ou igual à atual | `400` | Validação do serializer ou regra de negócio |
| Conta coletiva | `400` | *Contas coletivas não podem alterar a senha...* |
| Usuário inativo | `400` | *O usuário está inativo.* |

**O que este fluxo não cobre:**

- Redefinição por e-mail / código de verificação (não implementado).
- Alteração de senha de outro usuário via API (apenas Django Admin).
- O `PATCH /usuarios/{pk}/` **não** aceita senha — alteração de perfil e de senha são endpoints separados.

**Arquivos da implementação:**

| Camada | Arquivo | Responsabilidade |
| ------ | ------- | ---------------- |
| Rules | `Identidade/usuarios/rules.py` | `pode_alterar_senha`, `validar_senha_atual` |
| Business | `Identidade/usuarios/business.py` | `alterar_senha` |
| Serializer | `Identidade/usuarios/serializers.py` | `AlterarSenhaSerializer` |
| View / URL | `Identidade/usuarios/views.py`, `urls.py` | `AlterarSenhaView`, rota `usuario-alterar-senha` |
| Testes | `Identidade/usuarios/tests/test_views.py` | `AlterarSenhaUsuarioTest` |

#### Configuração de Autenticação do Model `Usuario`
```python
class Usuario(AbstractBaseUser, BasicModel):
    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome']

    # campos...
    cpf = models.CharField('CPF', max_length=11, unique=True)
    nome = models.CharField('Nome', max_length=255)
    # ...
```

### 2. Criação de Usuários (Via Admin JSON)
- Usuários são criados por administradores via endpoint específico.
- Suporte a criação individual ou em lote via JSON.
- Não há fluxo de auto-cadastro com envio de email.

### 3. Fotos do Usuário
- **`foto` (primária):** URL pública vinda de sistemas externos; atualizada por administradores via `PATCH /usuarios/{pk}/foto-primaria/`.
- **`foto_secundaria`:** upload pelo próprio usuário ou administrador via `POST /usuarios/{pk}/foto-secundaria/`; armazenada no S3 via `AppCore.common.storage.s3` (prefixo `Cortex/usuarios/fotos/`).
- **Limites da foto secundária:** formatos JPEG, PNG ou WebP; tamanho máximo de **3 MB**. Arquivos acima do limite retornam `400 Bad Request`.
- Para exibição no frontend, prefira `foto_secundaria` quando preenchida; caso contrário, use `foto`. A API devolve a URL do proxy (`GET /usuarios/{pk}/foto-secundaria/`), não a chave crua do bucket.
