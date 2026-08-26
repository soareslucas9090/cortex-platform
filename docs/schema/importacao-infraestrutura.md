# Especificação da Planilha de Importação em Lote de Infraestrutura

## Objetivo

Definir o contrato funcional e estrutural da planilha `.ods` utilizada para importação em lote de blocos, salas e recursos no módulo Infraestrutura do Cortex.

## Formato do arquivo

- Formato-alvo: `.ods`
- Estrutura: três abas operacionais
- Cada aba representa uma entidade do cadastro estrutural

## Abas operacionais

- `bloco`
- `sala`
- `recurso`

## Regra geral de correlação interna

Os campos `bloco_id` e `sala_id` existentes na planilha **não devem ser tratados como chaves primárias reais do banco**.

Eles devem ser usados apenas como **identificadores temporários internos do arquivo**, para correlacionar registros entre abas durante o processamento da importação.

### Exemplo

- a aba `bloco` cria um mapa entre `bloco_id` da planilha e o `Bloco` real criado/localizado no banco;
- a aba `sala` consome esse mapa via `bloco_id` e cria o mapa `sala_id` → `Sala`;
- a aba `recurso` consome o mapa de salas via `sala_id`.

## Ordem recomendada de processamento

1. `bloco`
2. `sala`
3. `recurso`

## Abas e colunas esperadas

---

## Aba `bloco`

### Colunas

- `bloco_id (int, PK)`
- `nome (String)`

### Regras

- `bloco_id` é obrigatório para correlação interna;
- `nome` é obrigatório;
- upsert por `nome` (cria ou atualiza o bloco existente com o mesmo nome).

---

## Aba `sala`

### Colunas

- `sala_id (int, PK)`
- `bloco_id (int, FK)`
- `nome (String)`

### Regras

- `sala_id` é obrigatório para correlação interna;
- `bloco_id` deve existir previamente na aba `bloco`;
- `nome` é obrigatório;
- upsert por `(bloco, nome)` (unicidade no banco).

---

## Aba `recurso`

### Colunas

- `sala_id (int, FK)`
- `descricao (String)`
- `codigo (String)`
- `avaria (boolean)` — valores `sim` / `não` (ou equivalentes booleanos)
- `tipo (String)` — `chave`, `midia` ou `material_didatico`
- `foto (String)` — URL HTTP/HTTPS da imagem do recurso

### Regras

- `codigo` é obrigatório e único na instância (case-insensitive);
- `tipo` deve ser um dos valores aceitos pelo domínio;
- `sala_id` pode ser nulo/`NULL`/`-` apenas se `tipo` não for `chave`;
- recursos do tipo `chave` exigem `sala_id` válido na planilha;
- upsert por `codigo`;
- `ativo` assume `true` na importação;
- `foto`, quando informada, é baixada, recortada em retrato 3:4, enviada ao S3 e servida via proxy da API;
- **falha no processamento ou upload da foto não impede a persistência do recurso** — o registro é salvo sem imagem e um aviso é incluído no resultado final (`codigo`: `erro_foto`).

## Regras de validação estrutural

A importação deve validar:

- presença do arquivo;
- extensão suportada (`.ods`);
- existência da aba operacional mínima (`bloco`);
- presença das colunas obrigatórias de cada aba;
- coerência entre dependências de abas.

## Regras de dependência entre abas

- `sala` depende de `bloco`
- `recurso` depende de `sala` (quando `sala_id` for informado)

## Regras de persistência

- a importação usa transação por linha lógica;
- falhas em uma linha não impedem o processamento das demais;
- a importação permite sucesso parcial;
- o processamento definitivo ocorre em background (Celery).

## Resultado esperado

Ao final do processamento, a rotina deve ser capaz de:

- mapear IDs temporários da planilha para objetos reais do banco;
- criar ou atualizar blocos, salas e recursos;
- registrar erros estruturados por aba, linha e campo;
- retornar um resumo consolidado da execução (contadores + lista de erros).
