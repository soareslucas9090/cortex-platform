# Especificação da Planilha de Importação em Lote de Usuários

## Objetivo

Definir o contrato funcional e estrutural da planilha `.ods` utilizada para importação em lote de usuários no Cortex.

A planilha segue um modelo **multiaba por entidade**, refletindo a estrutura relacional do domínio institucional/acadêmico do projeto.

## Formato do arquivo

- Formato-alvo: `.ods`
- Estrutura: múltiplas abas
- Cada aba representa uma entidade ou relação do domínio

## Abas do arquivo

### Abas operacionais de importação
Estas abas participam diretamente do processamento da importação:

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`
- `Aluno`
- `Aluno_Curso`
- `Servidor`
- `Terceirizado`
- `Setor_Lotacao`

### Abas de referência
Estas abas podem existir no arquivo, mas **não devem ser persistidas pela importação operacional** na primeira versão, pois seus dados já devem existir no banco por meio de migrações seed:

- `Curso`
- `Cargo`
- `Empresa_Instituicao`
- `Setor`
- `Funcao`

## Regra geral de correlação interna

Os campos `usuario_id`, `aluno_id`, `curso_id`, `cargo_id`, `empresa_instituicao_id` e `setor_id` existentes na planilha **não devem ser tratados como chaves primárias reais do banco**.

Eles devem ser usados apenas como **identificadores temporários internos do arquivo**, para correlacionar registros entre abas durante o processamento da importação.

### Exemplo
- a aba `Usuario` cria um mapa entre `usuario_id` da planilha e o `Usuario` real criado/localizado no banco;
- a aba `Aluno` cria um mapa entre `aluno_id` da planilha e o `Aluno` real do banco;
- a aba `Aluno_Curso` consome esse mapa.

## Ordem recomendada de processamento

1. `Usuario`
2. `Contato`
3. `Endereco`
4. `Matricula`
5. `Aluno`
6. `Servidor`
7. `Terceirizado`
8. `Setor_Lotacao`
9. `Aluno_Curso`

## Abas e colunas esperadas

---

## Aba `Usuario`

### Colunas
- `usuario_id (int, PK)`
- `cpf (String)`
- `nome (String)`
- `foto (String)`
- `deficiencia (String)`
- `ativo (boolean)`
- `ultimo_login (Date)`

### Regras
- `usuario_id` é obrigatório para correlação interna;
- `cpf` é obrigatório;
- `nome` é obrigatório;
- `ativo` deve ser interpretável como booleano;
- `ultimo_login`, se informado, deve ser data válida.

---

## Aba `Contato`

### Colunas
- `usuario_id (int, FK)`
- `email_academico (String)`
- `email_pessoal (String)`
- `telefone (String)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- pelo menos um meio de contato pode ser aceito conforme regra de negócio futura.

---

## Aba `Endereco`

### Colunas
- `usuario_id (int, FK)`
- `endereco (String)`
- `bairro (String)`
- `cep (String)`
- `complemento (String)`
- `numero (int)`
- `cidade (String)`
- `estado (String)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`.

---

## Aba `Matricula`

### Colunas
- `usuario_id (int, FK)`
- `matricula (String)`
- `situacao (String)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `situacao` deve ser compatível com a modelagem do projeto.

---

## Aba `Aluno`

### Colunas
- `aluno_id (int, PK)`
- `usuario_id (int, FK)`
- `ira (float)`

### Regras
- `aluno_id` é obrigatório para correlação interna com `Aluno_Curso`;
- `usuario_id` deve existir previamente na aba `Usuario`.

---

## Aba `Aluno_Curso`

### Colunas
- `aluno_id (int, FK)`
- `curso_id (int, FK)`
- `ano_conclusao (int)`

### Regras
- `aluno_id` deve existir previamente na aba `Aluno`;
- `curso_id` deve ser resolvido contra os dados seed já existentes no banco;
- esta aba não deve criar cursos.

---

## Aba `Servidor`

### Colunas
- `servidor_id (int, PK)`
- `usuario_id (int, FK)`
- `cargo_id (int, FK)`
- `categoria (String)`
- `ativo (boolean)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `cargo_id` deve ser resolvido contra os dados seed já existentes no banco;
- esta aba não deve criar cargos.

---

## Aba `Terceirizado`

### Colunas
- `terceirizado_id (int, PK)`
- `usuario_id (int, FK)`
- `empresa_instituicao_id (int, FK)`
- `ativo (boolean)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `empresa_instituicao_id` deve ser resolvido contra os dados seed já existentes no banco;
- esta aba não deve criar empresas/instituições.

---

## Aba `Setor_Lotacao`

### Colunas
- `usuario_id (int, FK)`
- `setor_id (int, FK)`
- `funcao_id (String, FK)`
- `responsavel (boolean)`
- `monitor (boolean)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `setor_id` deve ser resolvido contra os dados seed já existentes no banco;
- `funcao_id` deve ser resolvido contra os dados seed já existentes no banco;
- esta aba não deve criar setores nem funções.

## Regras de validação estrutural

A importação deve validar:

- presença do arquivo;
- extensão suportada;
- existência das abas operacionais mínimas;
- presença das colunas obrigatórias de cada aba;
- coerência entre dependências de abas.

## Regras de dependência entre abas

- `Contato` depende de `Usuario`
- `Endereco` depende de `Usuario`
- `Matricula` depende de `Usuario`
- `Aluno` depende de `Usuario`
- `Aluno_Curso` depende de `Aluno`
- `Servidor` depende de `Usuario`
- `Terceirizado` depende de `Usuario`
- `Setor_Lotacao` depende de `Usuario`

## Regras de persistência

- a importação deve usar transação por linha lógica;
- falhas em uma linha não devem impedir o processamento das demais;
- a importação pode permitir sucesso parcial;
- os dados raízes devem ser resolvidos no banco e nunca criados automaticamente pela rotina de importação.

## Resultado esperado

Ao final do processamento, a rotina deve ser capaz de:

- mapear IDs temporários da planilha para objetos reais do banco;
- criar ou atualizar usuários;
- criar ou atualizar entidades relacionadas;
- registrar erros estruturados por aba, linha e campo;
- retornar um resumo consolidado da execução.