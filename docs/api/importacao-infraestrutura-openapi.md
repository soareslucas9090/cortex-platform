# API — Importação em Lote de Infraestrutura

## GET /infraestrutura/importacao/modelo/

Retorna o arquivo modelo da planilha de importação.

### Respostas

- 200: arquivo retornado
- 403: sem permissão (`cadastrar`)

## POST /infraestrutura/importacao/pre-visualizar/

Recebe arquivo da planilha e retorna validação sem persistência.

### Request

- multipart/form-data
- campo `file`

### Resposta esperada

- total de linhas
- linhas válidas
- linhas inválidas
- criação estimada
- atualização estimada
- lista de erros por linha

## POST /infraestrutura/importacao/

Inicia o processo assíncrono de importação e persiste os dados do arquivo em background (Celery).

### Request

- multipart/form-data
- campo `file`

### Respostas

- 202: Importação enviada para fila (retorna `importacao_id`)
- 400: Já existe uma importação em andamento ou arquivo inválido
- 403: sem permissão (`cadastrar`)

## GET /infraestrutura/importacao/status/

Consulta o status da importação atual ou da última realizada.

### Respostas

- 200: Retorna o status (`EM_ANDAMENTO`, `CONCLUIDA`, `ERRO`) e a `porcentagem` de conclusão. Caso concluída, retorna os resultados no campo `resultado_json`.
- 404: Nenhuma importação encontrada
- 403: sem permissão (`cadastrar`)

## POST /infraestrutura/importacao/cancelar/

Cancela uma importação que tenha ficado travada em `EM_ANDAMENTO`. Ela será atualizada para o status de `ERRO` com a mensagem de que foi cancelada manualmente.

### Request

Nenhum corpo obrigatório.

### Respostas

- 200: Importação cancelada com sucesso.
- 400: Não há importação em andamento para cancelar.
- 403: sem permissão (`cadastrar`)

## GET /infraestrutura/importacao/historico/

Retorna a lista paginada do histórico de importações.

### Query params

- `status` (opcional): `EM_ANDAMENTO`, `CONCLUIDA`, `ERRO`
- `paginacao` (opcional): tamanho da página (1–100, padrão 10)

### Respostas

- 200: lista paginada
- 403: sem permissão (`cadastrar`)
