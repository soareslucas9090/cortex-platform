# Design de Autenticação por Email ou CPF

## Objetivo

Definir o desenho exato da autenticação do Cortex para permitir login usando:

- email
- CPF
- ou Matrícula

com um único endpoint, um único contrato de entrada e compatibilidade com:

- Django
- DRF
- SimpleJWT
- thin app `Auth`
- model concreto `Usuario` no app `Identidade.usuarios`

---

## Decisão principal

O sistema terá um único endpoint de login e um único campo de identificação:

- `login`

Esse campo aceitará:

- email
- CPF
- ou Matrícula

A senha continuará sendo enviada em:

- `password`

### Exemplo de request

```json
{
  "login": "usuario@email.com",
  "password": "Senha@123"
}
```

ou

```json
{
  "login": "12345678901",
  "password": "Senha@123"
}
```

ou

```json
{
  "login": "123.456.789-01",
  "password": "Senha@123"
}
```

---

## Model de usuário

O model concreto `Identidade.usuarios.Usuario` deve possuir, no mínimo:

- `email`
- `cpf`
- `password`
- `ativo`

### Requisitos

- `email` deve ser único
- `cpf` deve ser único
- `email` deve ser normalizado
- `cpf` deve ser persistido normalizado, contendo apenas dígitos

---

## Decisão sobre `USERNAME_FIELD`

O model concreto adota:

```python
USERNAME_FIELD = 'cpf'
REQUIRED_FIELDS = ['nome']
```

### Justificativa

O CPF é o identificador único central do usuário no Cortex. O suporte a e-mail como alternativa no login híbrido é resolvido pela camada de backend customizada (`EmailOrCpfBackend`), garantindo que tanto a integração com Django admin/auth quanto a autenticação DRF/SimpleJWT funcionem de maneira transparente e sem conflito de design.

---

## Estratégia de autenticação

A autenticação será composta por duas peças:

### 1. Backend customizado

Responsável por:

- detectar se o identificador é e-mail, CPF ou matrícula;
- localizar o usuário;
- aplicar o gate de elegibilidade (CPF ou matrícula válida);
- validar a senha;
- respeitar status de autenticação do usuário.

### 2. Serializer de login do projeto

Responsável por:

- expor `login` e `password`;
- autenticar usando o backend;
- gerar tokens JWT;
- enriquecer o payload, se necessário.

---

## Contrato do endpoint de login

### Endpoint

`POST /auth/token_jwt/`

### Request

Campos:

- `login`
- `password`

### Response de sucesso

Campos mínimos:

- `access`
- `refresh`

### Exemplo de sucesso

```json
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token"
}
```

### Response de erro

A autenticação deve falhar com mensagem genérica quando:

- usuário não existir;
- senha estiver incorreta;
- usuário estiver inativo;
- login for inválido.

### Exemplo conceitual

```json
{
  "detail": "Credenciais inválidas."
}
```

---

## Regra de detecção do identificador

### Regra 1

Se `login` contém `@`, tratar como e-mail.

### Regra 2

Caso contrário, se o valor normalizado tiver 11 dígitos, tratar como CPF.

### Regra 3

Caso contrário, tratar como matrícula ativa em `AlunoCurso`, `Servidor` ou `Terceirizado` (via `Usuario().helper.buscar_por_matricula_valida`).

---

## Regra de normalização do CPF

Antes da busca:

- remover pontos;
- remover hífen;
- remover espaços;
- manter apenas dígitos.

Exemplo:

- `123.456.789-01` → `12345678901`

---

## Regra de normalização do email

Antes da busca:

- aplicar `strip()`
- aplicar lowercase

Exemplo:

- `Usuario@Email.com ` → `usuario@email.com`

---

## Regra de normalização da matrícula

Antes da busca:

- aplicar `strip()`;
- valores vazios ou `NULL` são ignorados.

A matrícula é buscada apenas em vínculos **ativos** de `AlunoCurso`, `Servidor` ou `Terceirizado`.

---

## Gate de elegibilidade para login

Após localizar o usuário (por qualquer identificador), o backend só autentica se:

1. o usuário possui `cpf` preenchido; **ou**
2. o usuário possui ao menos uma matrícula ativa em `AlunoCurso`, `Servidor` ou `Terceirizado` (`user.helper.tem_matricula_valida()`).

Sem CPF nem matrícula válida, a autenticação falha de forma genérica.

---

## Fluxo exato de autenticação

1. O cliente envia:
   - `login`
   - `password`

2. O serializer valida a presença dos campos.

3. O serializer chama `authenticate(...)`.

4. O backend detecta se o identificador é email, CPF ou Matrícula.

5. O backend localiza o usuário pelo model configurado em `AUTH_USER_MODEL`.

6. O backend valida:
   - existência do usuário;
   - elegibilidade (CPF ou matrícula válida);
   - senha;
   - possibilidade de autenticação (`ativo`).

7. O serializer recebe o usuário autenticado.

8. O serializer gera:
   - `refresh`
   - `access`

9. A view retorna os tokens.

---

## Componentes necessários

### Backend de autenticação

Arquivo sugerido:

- `AppCore/basics/auth/backends.py`

Classe sugerida:

- `EmailOrCpfBackend`

### Utilitário de normalização

Arquivo sugerido:

- `AppCore/common/util/util.py`
  ou
- `AppCore/basics/auth/utils.py`

Função sugerida:

- `normalizar_cpf(valor: str) -> str`

### Serializer de login do projeto

Arquivo:

- `Auth/auth/serializers.py`

Mudança:

- expor `login` e `password`

### Serializer de documentação

Arquivo:

- `Auth/auth/serializers.py`

Mudança:

- documentar `login` como e-mail, CPF ou matrícula

### View de login

Arquivo:

- `Auth/auth/views.py`

### Configuração do Django

Arquivo:

- `Cortex/settings.py`

Mudança:

- registrar backend customizado em `AUTHENTICATION_BACKENDS`

### Model concreto

Arquivo:

- `Identidade/usuarios/models.py`

---

## Manager de usuário

O app `Identidade.usuarios` possui um manager concreto em `Identidade/usuarios/models.py`:

- `UsuarioManager(BaseManagerUser)`

Responsável por:

- normalizar email;
- normalizar CPF;
- implementar `create_user`;
- implementar `create_superuser` (recebendo o CPF como primeiro argumento).

---

## Regras de autenticação

1. O sistema usa identificador híbrido de login (e-mail, CPF, matrícula).
2. CPF deve autenticar com ou sem máscara.
3. E-mail deve autenticar ignorando capitalização.
4. Matrícula deve ser resolvida nas três fontes (`AlunoCurso`, `Servidor`, `Terceirizado`).
5. Usuário sem CPF precisa de matrícula válida para autenticar.
6. Usuário inativo não autentica.
7. A resposta de erro deve ser genérica.

---

## O que não fazer

- não criar um endpoint separado para email e outro para CPF;
- não depender apenas de `USERNAME_FIELD` para resolver login híbrido;
- não persistir CPF com múltiplos formatos;
- não manter contrato ambíguo no `Auth`.

---

## Resultado esperado

Ao final:

- o sistema terá login por e-mail, CPF ou matrícula;
- o endpoint continuará único;
- o contrato será claro;
- o `Auth` ficará coerente com o domínio do projeto;
- a autenticação continuará compatível com SimpleJWT.

---

## Resumo executivo

O Cortex deve adotar um modelo de autenticação com:

- campo único `login`;
- senha em `password`;
- backend customizado para e-mail, CPF ou matrícula;
- `Usuario` concreto com `email` e `cpf` únicos;
- documentação Swagger alinhada com o contrato real da API.
