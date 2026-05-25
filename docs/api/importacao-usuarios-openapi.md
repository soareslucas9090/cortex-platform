# API — Importação em Lote de Usuários

## GET /identidade/usuarios/importacao/modelo/
Retorna o arquivo modelo da planilha de importação.

### Respostas
- 200: arquivo retornado
- 403: sem permissão

## POST /identidade/usuarios/importacao/pre-visualizar/
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

## POST /identidade/usuarios/importacao/
Processa e persiste os dados válidos do arquivo.

### Request
- multipart/form-data
- campo `file`

### Resposta esperada
- total processado
- criados
- atualizados
- falhas
- erros estruturados por linha