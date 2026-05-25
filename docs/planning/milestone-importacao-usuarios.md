# Milestone — Importação em Lote de Usuários

## Objetivo
Implementar no Cortex uma funcionalidade de importação em lote de usuários via planilha, com suporte à criação e atualização de dados principais, relacionamento com entidades institucionais e retorno estruturado de validação.

## Escopo
Inclui:
- download de modelo de planilha;
- pré-validação do arquivo;
- importação definitiva;
- criação/atualização de usuário;
- criação/atualização de contato, endereço e matrícula;
- criação de perfis acadêmicos e institucionais;
- vinculação com cursos, setores, funções, cargos e empresas;
- seeds para dados raízes.

Não inclui:
- interface frontend;
- processamento assíncrono;
- histórico persistido de importações;
- edição manual em massa via admin.

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