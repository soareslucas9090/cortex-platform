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
- `Aluno`
- `Curso`
- `Aluno_Curso`
- `Servidor`
- `Terceirizado`
- `Setor_Lotacao`

### Abas de catálogo (referência na planilha)
Estas abas descrevem entidades institucionais usadas como referência pelos `*_id` das abas operacionais. Na **fase de catálogo** (antes da aba `Usuario`), a importação **cria** cada registro no banco se ele ainda **não** existir, casando pela chave natural com normalização de comparação; registro já existente **não** é alterado nem renomeado.

Abas de catálogo:

- `Setor`
- `Funcao`
- `Cargo`
- `Empresa_Instituicao`

Os seeds de migração continuam sendo a carga inicial típica; a planilha pode complementar o catálogo quando traz setores, funções, cargos ou empresas novas.

### Normalização de chaves (catálogo e `Curso`)
Para comparação de existência: `normalizar_chave_texto` (NFKD sem acento, espaços colapsados, casefold). CNPJ de empresa: apenas dígitos, `zfill` 14, tratando `.0` de planilha. Setor: sigla após aliases (`SIGLA_SETOR_ALIASES`, ex.: `NAPNE/FLO` → `NAPNE`).

Registro **novo** grava o texto da planilha com `strip` e espaços colapsados e o `ativo` da planilha.

## Regra geral de correlação interna

Os campos `usuario_id`, `aluno_id`, `curso_id`, `cargo_id`, `empresa_instituicao_id` e `setor_id` existentes na planilha **não devem ser tratados como chaves primárias reais do banco**.

Eles devem ser usados apenas como **identificadores temporários internos do arquivo**, para correlacionar registros entre abas durante o processamento da importação.

### Exemplo
- a aba `Usuario` cria um mapa entre `usuario_id` da planilha e o `Usuario` real criado/localizado no banco;
- a aba `Aluno` cria um mapa entre `aluno_id` da planilha e o `Aluno` real do banco;
- a aba `Aluno_Curso` consome esse mapa.

## Ordem recomendada de processamento

1. `Setor`
2. `Funcao`
3. `Cargo`
4. `Empresa_Instituicao`
5. `Usuario`
6. `Contato`
7. `Endereco`
8. `Aluno`
9. `Servidor`
10. `Terceirizado`
11. `Setor_Lotacao`
12. `Curso`
13. `Aluno_Curso`

As quatro primeiras abas correspondem à fase de catálogo executada antes de `Usuario`.

## Abas e colunas esperadas

---

## Aba `Setor`

### Colunas
- `setor_id (int, PK)` — identificador interno da planilha
- `nome (String)`
- `sigla (String)` — chave natural no banco (com `SIGLA_SETOR_ALIASES` na comparação)
- `ativo (boolean)`

### Regras
- `sigla` e `nome` são obrigatórios em linhas válidas de catálogo;
- se já existir setor com a mesma sigla normalizada, a linha não altera o registro existente;
- se não existir, o setor é criado com os valores da planilha;
- linha sem dado obrigatório ou inválida gera erro de linha; a importação continua nas demais.

---

## Aba `Funcao`

### Colunas
- `funcao_id (String, PK)` — identificador interno da planilha
- `papel_funcao (String)` — chave natural no banco; o cabeçalho `funcao` também é aceito
- `descricao (String)` — se vazia na criação, usa o valor de `papel_funcao`
- `ativo (boolean)`
- `categoria (String)` — opcional: `diretor`, `coordenador` ou `chefe`; vazio assume `coordenador`; valor inválido = erro de linha

### Regras
- casamento por `papel_funcao` normalizado;
- cria função ausente; não atualiza função já existente;
- linha inválida gera erro de linha; a importação continua.

---

## Aba `Cargo`

### Colunas
- `cargo_id (int, PK)` — identificador interno da planilha
- `nome (String)` — chave natural (nome normalizado)
- `ativo (boolean)`

### Regras
- cria cargo ausente; não atualiza cargo já existente;
- linha sem `nome` ou inválida gera erro de linha; a importação continua.

---

## Aba `Empresa_Instituicao`

### Colunas
- `empresa_instituicao_id (int, PK)` — identificador interno da planilha
- `nome (String)`
- `cnpj (String)` — opcional; se informado (14 dígitos após normalização), é a chave natural; senão usa o nome normalizado
- `ativo (boolean)`

### Regras
- cria empresa ausente; não atualiza empresa já existente;
- linha inválida gera erro de linha; a importação continua.

---

## Aba `Usuario`

### Colunas
- `usuario_id (int, PK)`
- `cpf (String)`
- `nome (String)`
- `foto (String)`
- `ativo (boolean)`
- `ultimo_login (Date)`
- `colaborador_externo (boolean)`

### Regras
- `usuario_id` é obrigatório para correlação interna;
- `cpf` é obrigatório;
- `nome` é obrigatório;
- `ativo` deve ser interpretável como booleano;
- `colaborador_externo` deve ser interpretável como booleano; se ausente ou nulo, assume `false`;
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
- `cidade (String)`
- `estado (String)`

Campos opcionais, se presentes no arquivo, também são lidos: `cep`, `complemento`, `numero`.

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`.

---

## Aba `Aluno`

### Colunas
- `aluno_id (int, PK)`
- `usuario_id (int, FK)`
- `ira (float)`
- `deficiencia (String)`

### Regras
- `aluno_id` é obrigatório para correlação interna com `Aluno_Curso`;
- `usuario_id` deve existir previamente na aba `Usuario`;
- `deficiencia`, quando informada, é persistida no `Usuario` vinculado ao aluno.

---

## Aba `Curso`

### Colunas
- `curso_id (int, PK)` — identificador interno da planilha (correlação com `Aluno_Curso`)
- `setor_id (int, FK)` — **obrigatório**; resolvido contra a aba `Setor`, setores criados na fase de catálogo da mesma importação e setores já existentes no banco (seed)
- `nome (String)`
- `codigo_curso (String)` — chave natural para criar ou atualizar o registro no banco (`codigo_curso` normalizado)
- `ativo (boolean)`

A coluna `modalidade` pode existir no arquivo por compatibilidade com o layout legado, mas **não** é lida nem persistida (não faz parte do model `Curso`).

### Regras
- `setor_id` é obrigatório em cada linha; o setor deve existir na aba `Setor`, ter sido criado na fase de catálogo da mesma importação ou no seed;
- a importação **cria** ou **atualiza** `Curso` pelo `codigo_curso` normalizado (única aba de catálogo/acadêmica que atualiza registro existente: nome, setor e ativo);
- não é permitido deixar curso sem setor (linhas sem `setor_id` válido falham);
- `curso_id` da planilha alimenta o mapa interno usado pela aba `Aluno_Curso`.

---

## Aba `Aluno_Curso`

### Colunas
- `aluno_id (int, FK)`
- `curso_id (int, FK)`
- `ano_conclusao (int)`
- `matricula (String)`
- `ira (double)`
- `turma (String)`
- `turno (String)`
- `situacao_curso (String)`

### Regras
- `aluno_id` deve existir previamente na aba `Aluno`;
- `curso_id` deve ser resolvido contra cursos já no banco **ou** criados/atualizados na mesma importação (aba `Curso` processada antes);
- `matricula`, quando informada, deve ser única no sistema;
- esta aba **não** cria cursos — apenas vincula aluno a curso existente no mapa de resolução.

---

## Aba `Servidor`

### Colunas
- `servidor_id (int, PK)`
- `usuario_id (int, FK)`
- `cargo_id (int, FK)`
- `categoria (String)`
- `ativo (boolean)`
- `matricula (String)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `cargo_id` deve ser resolvido contra cargos no banco **ou** criados na fase de catálogo (`Cargo`) da mesma importação;
- `matricula`, quando informada, deve ser única no sistema;
- linha operacional cujo `cargo_id` não está na aba `Cargo` **nem** no banco continua falhando (não há dado para criar o cargo).

---

## Aba `Terceirizado`

### Colunas
- `terceirizado_id (int, PK)`
- `usuario_id (int, FK)`
- `empresa_instituicao_id (int, FK)`
- `ativo (boolean)`
- `matricula (String)`

### Regras
- `usuario_id` deve existir previamente na aba `Usuario`;
- `empresa_instituicao_id` deve ser resolvido contra empresas no banco **ou** criadas na fase de catálogo (`Empresa_Instituicao`) da mesma importação;
- `matricula`, quando informada, deve ser única no sistema;
- linha operacional cujo `empresa_instituicao_id` não está na aba de referência **nem** no banco continua falhando.

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
- `setor_id` e `funcao_id`, quando informados, são resolvidos contra o banco **ou** contra registros criados na fase de catálogo (`Setor` / `Funcao`) da mesma importação;
- `funcao_id` pode ser nulo/`NULL`: o vínculo é criado só com usuário + setor;
- linha cujo `setor_id` ou `funcao_id` não está na planilha de catálogo **nem** no banco continua falhando;
- a coluna `monitor` pode existir na planilha por compatibilidade com o layout legado, mas **não** grava booleano em `SetorVinculo`. Monitoria é representada pela **função** (`funcao_id` / `Funcao` com papel de monitor). A camada de business da importação **ignora** o valor de `monitor`.

## Fluxo operacional da API (importação definitiva)

Alinhado ao módulo de importação de infraestrutura:

- a importação definitiva (`POST .../importacao/`) enfileira processamento **Celery**;
- cada execução é registrada em `ImportacaoLote` (`Identidade.usuarios`);
- apenas **um** lote com status `EM_ANDAMENTO` é permitido por vez;
- `GET .../importacao/status/` consulta o lote em andamento ou o último;
- `POST .../importacao/cancelar/` interrompe lote travado em `EM_ANDAMENTO`;
- `GET .../importacao/historico/` lista lotes anteriores (filtro opcional por `status`, paginação).

Contrato HTTP: `docs/api/importacao-usuarios-openapi.md`.

## Matrícula

- Um mesmo usuário pode ter **mais de uma matrícula**: números distintos em `Aluno_Curso` (um por curso), `Servidor` e `Terceirizado`.
- Cada número, quando informado, permanece **único no sistema**: não pode se repetir entre usuários nem entre as três fontes.
- Células vazias, `-` ou o texto `NULL`/`null` são tratadas como matrícula ausente.

## Regras de validação estrutural

A importação deve validar:

- presença do arquivo;
- extensão suportada;
- existência das abas operacionais mínimas;
- presença das colunas obrigatórias de cada aba;
- coerência entre dependências de abas.

## Regras de dependência entre abas

- `Setor`, `Funcao`, `Cargo` e `Empresa_Instituicao` são processadas na fase de catálogo (antes de `Usuario`)
- `Contato` depende de `Usuario`
- `Endereco` depende de `Usuario`
- `Aluno` depende de `Usuario`
- `Curso` depende de `Setor` (aba `Setor`, setor criado na fase de catálogo da mesma importação e/ou seed)
- `Aluno_Curso` depende de `Aluno` e de `Curso` (resolução de `curso_id`)
- `Servidor` depende de `Usuario` e da resolução de `cargo_id` (catálogo e/ou banco)
- `Terceirizado` depende de `Usuario` e da resolução de `empresa_instituicao_id` (catálogo e/ou banco)
- `Setor_Lotacao` depende de `Usuario` e da resolução de `setor_id` / `funcao_id` (catálogo e/ou banco)

## Regras de persistência

- a importação deve usar transação por linha lógica;
- falhas em uma linha não devem impedir o processamento das demais;
- a importação pode permitir sucesso parcial;
- na fase de catálogo, `Setor`, `Funcao`, `Cargo` e `Empresa_Instituicao` são criados apenas se ausentes (chave natural + normalização), sem duplicar e sem alterar existentes; a aba `Curso` cria ou atualiza cursos conforme as regras acima;
- o processamento definitivo ocorre em background (Celery), com progresso e resultado consolidados no `ImportacaoLote`.

## Resultado esperado

Ao final do processamento, a rotina deve ser capaz de:

- mapear IDs temporários da planilha para objetos reais do banco;
- criar registros de catálogo ausentes (`Setor`, `Funcao`, `Cargo`, `Empresa_Instituicao`) e refletir isso nos contadores `setores_criados`, `funcoes_criadas`, `cargos_criados` e `empresas_criadas`;
- criar ou atualizar usuários;
- criar ou atualizar cursos (aba `Curso`, contadores `cursos_criados` e `cursos_atualizados`) e demais entidades relacionadas;
- registrar erros estruturados por aba, linha e campo;
- agrupar erros em cascata pela causa raiz (`grupos_erro`);
- retornar um resumo consolidado da execução.

## Agrupamento de erros

A lista plana `erros` continua com **uma entrada por linha com falha**. Cada entrada ganha `grupo_id` e `papel` (`causa` ou `impacto`) e é ordenada com as causas primeiro.

`resumo.total_linhas_com_erro` continua sendo `len(erros)`. `resumo.total_grupos_erro` conta os problemas distintos a resolver.

Dependentes de um pai que já falhou **não são tentados**: o erro da linha vira impacto do grupo do pai. A cadeia é transitiva (`Usuario` → `Aluno` → `Aluno_Curso` aponta para a raiz `Usuario`).

### Tipos de grupo

- `falha_entidade` — a própria linha da entidade falhou (`Usuario:12`, `Cargo:8`, `Curso:10`).
- `referencia_inexistente` — o `*_id` não está no catálogo da planilha nem no sistema (`ref:Cargo:5`). Não há linha-causa; as linhas que referenciam o id são os impactos.
- `linha` — erro isolado de aba sem id próprio (`linha:Contato:7`).

### Mapa de dependências

- `Contato`, `Endereco` e `Aluno` dependem de `usuario_id` (`Usuario`)
- `Servidor` depende de `usuario_id` e `cargo_id`
- `Terceirizado` depende de `usuario_id` e `empresa_instituicao_id`
- `Setor_Lotacao` depende de `usuario_id`, `setor_id` e `funcao_id` (opcional)
- `Curso` depende de `setor_id`
- `Aluno_Curso` depende de `aluno_id` e `curso_id`

Quando mais de um pai falhou, a linha entra no grupo do **primeiro** pai da lista acima.

Lotes antigos em `resultado_json` podem não ter `grupos_erro`; o consumidor deve tratar o campo como ausente. A API de status trunca em no máximo 50 grupos (impactos limitados por grupo, com `total_impactos` sempre exato) e 50 erros planos.

### Exemplo

Quatro usuários com CPF inválido geram **quatro** grupos, mesmo que cada um tenha contato, aluno, vínculo e lotação. Cada grupo tem a causa na aba `Usuario` e os impactos nas abas dependentes, com mensagem no formato:

`Não importado: depende de Usuario 12 (linha 7), que falhou: CPF inválido.`
