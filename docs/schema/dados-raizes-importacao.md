# Dados Raízes da Importação de Usuários

## Objetivo
Garantir que as entidades institucionais de referência existam no banco antes da importação em lote.

## Entidades semeadas
- Setor
- Curso (depende de `Setor` já semeado; cada curso referencia setor pela **sigla** do setor)
- Cargo
- Empresa_Instituicao
- Funcao

## Chaves naturais recomendadas
- Curso: `codigo_curso`
- Cargo: `nome`
- Empresa_Instituicao: `nome`
- Setor: `sigla`
- Funcao: `papel_funcao` (na planilha pode vir como coluna `funcao`)

## Campos adicionais de referência
- Funcao: `categoria` (`diretor`, `coordenador` ou `chefe`), usada para regras de negócio em outros módulos

## Regras
- migrações devem ser idempotentes;
- não duplicar registros;
- dados devem ser implantados via seed;
- a ordem de seed deve garantir `Setor` antes de `Curso` (FK por sigla);
- importação não deve criar `Cargo`, `Empresa_Instituicao`, `Setor` nem `Funcao` automaticamente; cursos adicionais ou atualizações podem ocorrer pela aba operacional `Curso` na importação de usuários (ver `importacao-usuarios.md`).

## Resultado esperado
Ao subir um banco novo, os dados raízes necessários à importação devem existir uma única vez.