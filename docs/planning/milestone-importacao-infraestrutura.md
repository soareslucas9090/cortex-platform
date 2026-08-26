# Milestone — Importação em Lote de Infraestrutura

## Objetivo

Implementar no Cortex a importação em lote de blocos, salas e recursos via planilha `.ods`, com processamento assíncrono (Celery) e tratamento de fotos de recurso via download de URL, recorte retrato 3:4 e upload ao S3.

## Escopo

Inclui:

- download de modelo de planilha;
- pré-validação do arquivo;
- importação definitiva assíncrona;
- criação/atualização de bloco, sala e recurso;
- download e processamento de foto de recurso (não bloqueante);
- status, histórico e cancelamento de importação.

Não inclui:

- `SalaSetor`, autorizações ou empréstimos;
- interface frontend;
- campo `ativo` na planilha (assume `true`).

## Dependências

- módulo Infraestrutura v1 (blocos, salas, recursos);
- Celery configurado;
- bucket S3 do projeto;
- modelo ODS em `docs/seeds/import/modelo-importacao-infraestrutura.ods`.

## Critérios de aceite

- modelo de planilha disponível via API;
- importação aceita arquivo válido e retorna 202;
- erros por linha retornam de forma estruturada;
- falha de foto não impede persistência do recurso;
- apenas um lote `EM_ANDAMENTO` por vez;
- permissão `cadastrar` exigida nos endpoints de escrita.

## Ordem de implementação

1. documentação do contrato
2. app `Infraestrutura.importacoes` + model `ImportacaoLote`
3. parser e DTOs
4. business de importação + foto
5. Celery task + views/serializers/urls
6. testes
