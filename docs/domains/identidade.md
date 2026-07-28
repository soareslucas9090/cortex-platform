# Diretrizes do Domínio: Identidade

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Identidade** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Identidade` é responsável pela autenticação, perfis de usuários e informações básicas de contato e endereço.

### Modelos e Relacionamentos

- **Usuario**: Classe base central do sistema (autenticação baseada em CPF). Possui relacionamento 1:N com `Contato` e `Endereco`.
- **Contato**: Informações de contato do usuário (relacionamento N:1 com `Usuario`).
- **Endereco**: Endereços do usuário (relacionamento N:1 com `Usuario`).
- **Matricula**: Matrículas vinculadas ao usuário (relacionamento N:1 com `Usuario`).

### Estrutura de Apps

```text
Identidade/
├── __init__.py
├── urls.py
├── usuarios/        # App Django do model Usuario
├── contatos/        # App Django do model Contato
├── enderecos/       # App Django do model Endereco
└── matriculas/      # App Django do model Matricula
```

---

## Regras Específicas do Domínio

### 1. Autenticação e Usuários
- **Login por CPF**: O identificador único para login é o **CPF** (`cpf`), não o e-mail.
- **Não há auto-cadastro**: Usuários não podem se cadastrar sozinhos no sistema. A criação é feita exclusivamente por administradores.
- **Criação de Usuários**: Deve suportar criação individual ou em lote via payload JSON por um administrador ou via portal Admin. Não há fluxo de envio de e-mail para confirmação automática de cadastro.
- **Usuário coletivo**: flag `usuario_coletivo` na criação/edição do usuário. Conta compartilhada (ex.: guarita) usada na operação de Infraestrutura. O pool de associações (empresas, cargos, funções, setores) **não** é enviado na criação; é configurado em endpoints dedicados:
  - `GET/PUT /usuarios/{pk}/coletivo/` — consultar e substituir o pool
  - `POST /usuarios/{pk}/coletivo/itens/` — adicionar item (`tipo` + `id`)
  - `DELETE /usuarios/{pk}/coletivo/itens/{tipo}/{item_id}/` — remover item
  - Ao desativar a flag, o pool é limpo automaticamente.
  - Conta coletiva não pode ser solicitante nem responsável de empréstimo.
  - No cadastro, o **CPF é opcional**; sem CPF, a **matrícula é obrigatória** (identificador de login: e-mail, CPF ou matrícula).

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
- **`foto_secundaria`:** upload pelo próprio usuário ou administrador via `POST /usuarios/{pk}/foto-secundaria/`; armazenada no S3.
- **Limites da foto secundária:** formatos JPEG, PNG ou WebP; tamanho máximo de **3 MB**. Arquivos acima do limite retornam `400 Bad Request`.
- Para exibição no frontend, prefira `foto_secundaria` quando preenchida; caso contrário, use `foto`.
