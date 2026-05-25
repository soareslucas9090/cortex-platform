# Especificação da Planilha de Importação de Usuários

## Aba principal
Nome da aba: `usuarios`

## Formato esperado
Arquivo de planilha com uma linha por usuário.

## Colunas sugeridas
- cpf
- nome
- foto
- deficiencia
- ativo
- ultimo_login
- email_academico
- email_pessoal
- telefone
- logradouro
- numero
- complemento
- bairro
- cep
- cidade
- estado
- matricula
- situacao
- tipo_perfil
- ira
- curso
- ano_conclusao
- cargo
- categoria_servidor
- empresa_instituicao
- setor
- funcao
- responsavel_setor
- monitor

## Regras de preenchimento
- `cpf` é obrigatório
- `nome` é obrigatório
- `tipo_perfil` pode conter múltiplos valores separados por `;`
- campos relacionais devem usar identificadores naturais:
  - curso: `codigo_curso`
  - cargo: `nome`
  - empresa_instituicao: `nome`
  - setor: `sigla`
  - funcao: `sigla`

## Observações
- A importação não deve criar automaticamente dados raízes ausentes.
- Se uma referência não existir, a linha deve falhar.
- O layout final deve acompanhar os models reais do repositório.