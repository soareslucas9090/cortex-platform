# Milestone — Importação em Lote de Usuários

> **Histórico de implementação.** Não usar como backlog. Fonte canônica: [docs/domains/](../domains/) e [docs/project/django-project-tree.md](../project/django-project-tree.md).

## Estado

**Concluída** no código (`Identidade.usuarios`, model `ImportacaoLote`, Celery).

## Objetivo
Implementar no Cortex uma funcionalidade de importação em lote de usuários via planilha, com suporte à criação e atualização de dados principais, relacionamento com entidades institucionais e retorno estruturado de validação.

## Escopo
Inclui:
- download de modelo de planilha;
- pré-validação do arquivo;
- importação definitiva;
- criação/atualização de usuário;
- criação/atualização de contato, endereço e matrículas em `Servidor` / `Terceirizado` / `AlunoCurso` (não há app `matriculas`);
- criação de perfis acadêmicos e institucionais;
- vinculação com cursos, setores, funções, cargos e empresas;
- seeds para dados raízes.

Não inclui (ainda):
- interface frontend;
- edição manual em massa via admin.

**Superado pelo código (não tratar como lacuna):** processamento assíncrono (Celery), model `ImportacaoLote`, endpoints de status/cancelar/histórico e regra de um único lote `EM_ANDAMENTO` por vez — ver `docs/api/importacao-usuarios-openapi.md`.

## Dependências
- models centrais já existentes;
- seeds de dados raízes;
- definição final do layout da planilha.

## Critérios de aceite
- modelo de planilha disponível;
- importação aceita arquivo válido;
- erros por linha retornam de forma estruturada;
- usuários válidos são persistidos;
- dados raízes são usados como referência;
- migrações seed são idempotentes.

## Ordem recomendada
1. seeds
2. contrato da planilha
3. parser e validações
4. business de importação
5. views e serializers
6. OpenAPI
7. testes