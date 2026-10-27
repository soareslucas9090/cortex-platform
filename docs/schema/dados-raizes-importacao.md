# Dados Raízes da Importação de Usuários

## Objetivo
Garantir que as entidades institucionais de referência existam no banco antes da importação em lote. Os seeds de migração são a carga inicial; a importação de usuários **complementa** o catálogo quando a planilha traz setores, funções, cargos ou empresas ainda ausentes.

## Entidades semeadas
- Setor
- Curso (depende de `Setor` já semeado; cada curso referencia setor pela **sigla** do setor)
- Cargo
- Empresa_Instituicao
- Funcao

## Chaves naturais recomendadas
- Curso: `codigo_curso`
- Cargo: `nome`
- Empresa_Instituicao: `nome` (ou CNPJ com 14 dígitos, quando informado na importação)
- Setor: `sigla`
- Funcao: `papel_funcao` (na planilha pode vir como coluna `funcao`)

## Campos adicionais de referência
- Funcao: `categoria` (`diretor`, `coordenador` ou `chefe`), usada para regras de negócio em outros módulos

## Regras
- migrações devem ser idempotentes;
- não duplicar registros;
- dados devem ser implantados via seed;
- a ordem de seed deve garantir `Setor` antes de `Curso` (FK por sigla);
- na importação de usuários, `Cargo`, `Empresa_Instituicao`, `Setor` e `Funcao` são **criados apenas se ausentes**, sem duplicar (chave natural + normalização de comparação); registro já existente não é alterado pela fase de catálogo. Empresa: chave por CNPJ (14 dígitos) quando informado, senão por nome normalizado. Cursos adicionais ou atualizações podem ocorrer pela aba operacional `Curso` (ver `importacao-usuarios.md`).

## Resultado esperado
Ao subir um banco novo, os dados raízes necessários à importação devem existir uma única vez via seed; importações subsequentes podem acrescentar catálogo novo presente na planilha, sem duplicar o que já existe.
