# Dados Raízes da Importação de Usuários

## Objetivo
Garantir que as entidades institucionais de referência existam no banco antes da importação em lote.

## Entidades semeadas
- Curso
- Cargo
- Empresa_Instituicao
- Setor
- Funcao

## Chaves naturais recomendadas
- Curso: `codigo_curso`
- Cargo: `nome`
- Empresa_Instituicao: `nome`
- Setor: `sigla`
- Funcao: `papel_funcao`

## Campos adicionais de referência
- Funcao: `categoria` (`diretor`, `coordenador` ou `chefe`), usada para regras de negócio em outros módulos

## Regras
- migrações devem ser idempotentes;
- não duplicar registros;
- dados devem ser implantados via seed;
- importação não deve criar esses registros automaticamente.

## Resultado esperado
Ao subir um banco novo, os dados raízes necessários à importação devem existir uma única vez.