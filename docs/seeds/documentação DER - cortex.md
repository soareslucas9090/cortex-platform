# Dados Cortex — Descrição em Markdown

> **Importante:** o arquivo original deste modelo está em formato `.ods` (OpenDocument Spreadsheet).
> 
> Este `.md` foi criado especificamente para uso no GitHub Copilot e outras IAs/code assistants que não interpretam arquivos `.ods` diretamente.
> 
> Arquivo original: `dados_cortex.ods`

----------

# Visão Geral

Este documento descreve a estrutura de dados do projeto Cortex a partir de uma planilha `.ods`.

A modelagem representa um sistema institucional/acadêmico contendo:

-   Usuários
    
-   Alunos
    
-   Servidores
    
-   Terceirizados
    
-   Cursos
    
-   Setores institucionais
    
-   Funções administrativas
    
-   Matrículas (em perfis/vínculos) e lotações
    
-   Contatos e endereços
    

O objetivo deste documento é permitir que ferramentas de IA (como GitHub Copilot) compreendam a estrutura do banco de dados sem precisar interpretar diretamente o arquivo `.ods`.

----------

# Estrutura das Entidades

## Usuario

Representa a entidade base de pessoas no sistema.

### Campos

Campo

Tipo

Descrição

usuario_id

int (PK)

Identificador único do usuário

cpf

String

CPF do usuário

nome

String

Nome completo

foto

String

URL/caminho da foto

deficiencia

String

Informação de deficiência

ativo

boolean

Indica se o usuário está ativo

ultimo_login

Date

Data do último login

----------

## Contato

Informações de contato vinculadas ao usuário.

### Campos

Campo

Tipo

Descrição

usuario_id

int (FK)

Referência para Usuario

email_academico

String

E-mail institucional

email_pessoal

String

E-mail pessoal

telefone

String

Número de telefone

----------

## Endereco

Endereço associado ao usuário.

### Campos

Campo

Tipo

Descrição

usuario_id

int (FK)

Referência para Usuario

endereco

String

Logradouro

bairro

String

Bairro

cep

String

CEP

complemento

String

Complemento

numero

int

Número

cidade

String

Cidade

estado

String

Estado

----------

## Aluno

Representa usuários do tipo aluno.

### Campos

Campo

Tipo

Descrição

aluno_id

int (PK)

Identificador do aluno

usuario_id

int (FK)

Referência para Usuario

ira

double

Índice de rendimento acadêmico

----------

## Curso

Tabela de cursos disponíveis.

### Campos

Campo

Tipo

Descrição

curso_id

int (PK)

Identificador do curso

nome

String

Nome do curso

codigo_curso

String

Código institucional

setor_id

int (FK)

Referência para `Setor` (coordenação ou unidade responsável pelo curso)

ativo

boolean

Indica se o curso está ativo

modalidade

String

Modalidade do curso (informativa na planilha; não persistida no model `Curso`)

### Dados raízes

| curso_id (int, PK) | setor_id (int, FK) | nome (String) | codigo_curso (String) | ativo (boolean) | modalidade (String) |
|---|---|---|---|---|---|
| 1 | 9 | Formação Inicial em Agente de Inclusão Digital em Centros Públicos de Acesso à Internet - Campus Floriano | 14FAID | true | FIC |
| 2 | 9 | Formação Inicial em Língua Brasileira de Sinais (Libras) - Básico - Campus Floriano | 14FLIB | true | FIC |
| 3 | 9 | Formação Inicial em Inglês Básico - Campus Floriano | 14FINB | true | FIC |
| 4 | 9 | Formação Inicial em Eletricista de Sistemas de Energias Renováveis - Campus Floriano | 14FSER | true | FIC |
| 5 | 26 | Especialização em Desenvolvimento para Web | S.52 | true | Especialização |
| 6 | 12 | Especialização em Desporto Escolar e Desempenho Humano | S.53 | true | Especialização |
| 7 | 23 | Especialização em Ensino de Matemática no Ensino Médio | S.55 | true | Especialização |
| 8 | 23 | Especialização em Matemática | S.54 | true | Especialização |
| 9 | 31 | Especialização no Ensino de Ciências Biológicas | 14EECB | true | Especialização |
| 10 | 32 | Licenciatura em  Ciências Biológicas / PARFOR - 2ª Licenciatura | S.04 | true | Licenciatura |
| 11 | 32 | Licenciatura em Ciências Biológicas - Floriano | 14LBIO | true | Licenciatura |
| 12 | 32 | Licenciatura em Ciências Biológicas / PARFOR - 1ª Licenciatura | S.03 | true | Licenciatura |
| 13 | 23 | Licenciatura em Matemática - Floriano | 14LMAT | true | Licenciatura |
| 14 | 23 | Licenciatura em Matemática / PARFOR - 2ª Licenciatura | S.05 | true | Licenciatura |
| 15 | 24 | Mestrado Profissional em Matemática / PROFMAT - Floriano | 14PMAT | true | Mestrado |
| 16 | 34 | Técnico de Informática - Concomitante/Subsequente - Floriano | 14MINF | true | Técnico Subsequente\Concomitante |
| 17 | 9 | Técnico de Segurança do Trabalho - EaD | B.61 | true | Técnico Subsequente\Concomitante/Ead |
| 18 | 9 | Técnico de Serviços Jurídicos Subsequente - EaD | B.62 | true | Técnico Subsequente |
| 19 | 9 | Técnico em Administração - EaD | TEAD | true | Técnico Subsequente\Concomitante/Ead |
| 20 | 21 | Técnico em Desenvolvimento de Sistemas - Concomitante/Subsequente - Floriano | 14MTDS | true | Técnico Subsequente\Concomitante |
| 21 | 19 | Técnico em Edificações - Concomitante/Subsequente - Floriano | 14MEDF | true | Técnico Subsequente\Concomitante |
| 22 | 19 | Técnico em Edificações - Integrado - Floriano | 14IEDF | true | Técnico Subsequente\Concomitante |
| 23 | 17 | Técnico em Eletromecânica - Concomitante/Subsequente - Floriano | 14MELM | true | Técnico Subsequente\Concomitante |
| 24 | 17 | Técnico em Eletromecânica - Integrado - Floriano | 14IELM | true | Técnico Integrado |
| 25 | 34 | Técnico em Informática - Integrado - Floriano | 14IINF | true | Técnico Integrado |
| 26 | 34 | Técnico em Informática para Internet - EaD | IPINT | true | Técnico Subsequente\Concomitante/Ead |
| 27 | 27 | Técnico em Logística - EaD | LOGI | true | Técnico Subsequente\Concomitante/Ead |
| 28 | 12 | Técnico em Meio Ambiente - EaD | MEAB | true | Técnico Subsequente\Concomitante/Ead |
| 29 | 10 | Técnico em Meio Ambiente - Integrado - Floriano | 14IAMB | true | Técnico Integrado |
| 30 | 35 | Técnico em Redes de Computadores | B.67 | true | Técnico Subsequente\Concomitante |
| 31 | 27 | Técnico em Secretariado - EaD | SECR | true | Técnico Subsequente\Concomitante/Ead |
| 32 | 27 | Técnico em Serviços Públicos - EAD | TPF | true | Técnico Subsequente\Concomitante/Ead |
| 33 | 26 | Tecnologia em Análise e Desenvolvimento de Sistemas - Floriano | 14TADS | true | Tecnologia |
| 34 | 30 | Técnico em Meio Ambiente Integrado ao Ensino Médio - PROEJA | 14JAMB | true | Técnico Integrado EJA |
| 35 | 29 | Formação Inicial em Músico de Banda | 14FMB | true | FIC |
| 37 | 27 | Técnico em Administração- Integrado - Floriano | 14IADM | true | Técnico Integrado |
| 38 | 28 | Bacharelado em Engenharia Civil - CAFLO | 14BECV | true | Bacharelado |
| 39 | 17 | Eletricista de Sistema de Energias Renováveis | 14ASER | true | Qualificação Profissional |
| 40 | 9 | Preparatório para o Ensino Médio - PARTIU IF | 14PIFPI | true |  |
| 41 | 9 | Formação Inicial em Redator de Textos Técnicos | 14FRT | true | FIC |

> Nota: o curso `14JOPC` (seed legado da migração `cursos.0001`) não consta no modelo atual, mas já existe em bancos implantados e é preservado (associado ao setor `DEPENTE` pela migração `cursos.0004`). A coluna `modalidade` é apenas informativa na planilha e não é persistida no model `Curso`.

----------

## Aluno_Curso

Tabela relacional entre alunos e cursos.

### Campos

Campo

Tipo

Descrição

aluno_id

int (FK)

Referência para Aluno

curso_id

int (FK)

Referência para Curso

ano_conclusao

int

Ano de conclusão

matricula

String

Código de matrícula acadêmica (opcional; único no sistema)

ira

double

Índice de rendimento acadêmico

turma

String

Turma

turno

String

Turno

situacao_curso

String

Situação do vínculo com o curso

----------

## Servidor

Representa servidores institucionais.

### Campos

Campo

Tipo

Descrição

servidor_id

int (PK)

Identificador do servidor

usuario_id

int (FK)

Referência para Usuario

cargo_id

int (FK)

Referência para Cargo

categoria

String

Professor ou Técnico Administrativo

ativo

boolean

Indica se o servidor está ativo

matricula

String

Código de matrícula institucional (opcional; único no sistema)

----------

## Cargo

Lista de cargos institucionais.

### Campos

Campo

Tipo

Descrição

cargo_id

int (PK)

Identificador do cargo

nome

String

Nome do cargo

ativo

boolean

Status do cargo

### Dados raízes

| cargo_id (int, PK) | nome (String) | ativo (boolean) |
|---|---|---|
| 1 | PROF ENS BAS TEC TECNOLOGICO-SUBSTITUTO | true |
| 2 | ASSISTENTE EM ADMINISTRACAO | true |
| 3 | ASSISTENTE DE ALUNO | true |
| 4 | ADMINISTRADOR | true |
| 5 | TEC DE TECNOLOGIA DA INFORMACAO | true |
| 6 | PROFESSOR ENS BASICO TECN TECNOLOGICO | true |
| 7 | ENGENHEIRO | true |
| 8 | BIBLIOTECARIO-DOCUMENTALISTA | true |
| 9 | VIGILANTE | true |
| 10 | TECNICO EM AUDIOVISUAL | true |
| 11 | CONTADOR | true |
| 12 | AUXILIAR DE BIBLIOTECA | true |
| 13 | AUX EM ADMINISTRACAO | true |
| 14 | ENFERMEIRO | true |
| 15 | TECNICO EM ELETROTECNICA | true |
| 16 | TECNICO DE LABORATORIO AREA | true |
| 17 | PSICOLOGO | true |
| 18 | TECNICO EM ARQUIVO | true |
| 19 | ASSISTENTE SOCIAL | true |
| 20 | TECNICO EM ASSUNTOS EDUCACIONAIS | true |
| 21 | ODONTOLOGO | true |
| 22 | SECRETARIO EXECUTIVO | true |
| 23 | PEDAGOGO | true |
| 24 | ASSISTENTE DE LABORATORIO | true |
| 25 | NUTRICIONISTA | true |
| 26 | MEDICO | true |
| 27 | TECNICO EM ENFERMAGEM | true |
| 28 | TECNICO EM SECRETARIADO | true |
| 29 | ANALISTA DE TEC DA INFORMACAO | true |

----------

## Terceirizado

Representa profissionais terceirizados.

### Campos

Campo

Tipo

Descrição

terceirizado_id

int (PK)

Identificador do terceirizado

usuario_id

int (FK)

Referência para Usuario

empresa_instituicao_id

int (FK)

Empresa vinculada

ativo

boolean

Status do vínculo

matricula

String

Código de matrícula institucional (opcional; único no sistema)

----------

## Empresa_Instituicao

Empresas ou instituições terceirizadas.

### Campos

Campo

Tipo

Descrição

empresa_instituicao_id

int (PK)

Identificador

nome

String

Nome da empresa

cnpj

String

CNPJ

ativo

boolean

Status

### Dados raízes

|empresa_instituicao_id (int, PK)|nome (String)|cnpj (String)|ativo (boolean)|

|---|---|---|---|

|1|CASTELO SERVIÇOS DE SEGURANÇA LTDA.|NULL|true|

|2|SERVFAZ SERVIÇOS DE MÃO DE OBRA LTDA.|NULL|true|

|3|SERVIRE AGENCIAMENTO DE MÃO DE OBRA LTDA.|NULL|true|
    

----------

## Setor

Setores institucionais.

### Campos

Campo

Tipo

Descrição

setor_id

int (PK)

Identificador do setor

nome

String

Nome do setor

sigla

String

Sigla institucional

ativo

boolean

Status

### Dados raízes

| setor_id (int, PK) | nome (String) | sigla (String) | ativo (boolean) |
|---|---|---|---|
| 1 | Diretoria de Ensino | DENS | true |
| 2 | Diretoria de Administração e Planejamento | DIAP | true |
| 3 | Coordenação de Disciplina | CODIS | true |
| 4 | Coordenação de Controle Acadêmico | COCACAD | true |
| 5 | Núcleo de Atendimento às Pessoas com Necessidades Específicas | NAPNE | true |
| 6 | Coordenação de Logística e Manutenção | DLMC | true |
| 7 | Departamento de Apoio ao Ensino | DAENS | true |
| 8 | Coordenação de Biblioteca | COBIB | true |
| 9 | Departamento de Ensino Técnico | DEPENTE | true |
| 10 | Coordenação do Curso Técnico em Meio Ambiente | CTEMEAM | true |
| 11 | Coordenação de Patrimônio e Almoxarifado | DCOPAT | true |
| 12 | Coordenação das Áreas de Ciências da Natureza, Ciências Humanas e Linguagens | CANHL | true |
| 13 | Departamento de Ensino Superior | DEPENSU | true |
| 14 | Coordenação de Gestão de Pessoas | CGP | true |
| 15 | Diretoria-Geral | DG | true |
| 16 | Coordenação de Integração, Estágios, Egressos e Emprego | CEICOM | true |
| 17 | Coordenação do Curso Técnico em Eletromecânica | COCTECEL | true |
| 18 | Gabinete da Diretoria-Geral | GDG | true |
| 19 | Coordenação do Curso Técnico em Edificações | CCEDI | true |
| 20 | Coordenação-Geral de Assistência Estudantil | CGAE | true |
| 21 | Coordenação do Curso Técnico em Desenvolvimento de Sistemas | CCTDS | true |
| 22 | Coodernação da Comissão Própria de Avaliação | CPA | true |
| 23 | Coordenação do Curso de Licenciatura em Matemática | CCLM | true |
| 24 | Coordenação do Mestrado Profissional em Matemática | PROFMAT | true |
| 25 | Coordenação do Curso de Licenciatura em Matemática | CCL | true |
| 26 | Coordenação do Curso de Análise e Desenvolvimento de Sistemas | CCADS | true |
| 27 | Coordenação do Curso Técnico em Administração | COCURADM | true |
| 28 | Coordenação do Curso de Bacharelado em Engenharia Civil | COCENGCIV | true |
| 29 | Coordenação de Extensão | CEXT | true |
| 30 | Coordenação do Curso Técnico em Meio Ambiente PROEJA | COTMEAMBPR | true |
| 31 | Coordenação da Especialização em Ensino de Ciências Biológicas | ECIENCBIO | true |
| 32 | Coordenação do Curso de Licenciatura em Ciências Biológicas | CCLCB | true |
| 33 | Coordenação de Pesquisa e Inovação | CPI | true |
| 34 | Coordenação do Curso Técnico em Informática | CCTI | true |
| 35 | Coordenação de Tecnologia da Informação | CTI | true |

----------

## Funcao

Funções exercidas dentro dos setores.

### Campos

Campo

Tipo

Descrição

funcao_id

String (PK)

Identificador da função na planilha

funcao

String

Nome da função (`papel_funcao` no model)

descricao

String

Descrição funcional

ativo

boolean

Status

categoria

String

Categoria da função: `diretor`, `coordenador` ou `chefe`

### Dados raízes

| funcao_id (String, PK) | funcao (String) | descricao (String) | ativo (boolean) | categoria (String) |
|---|---|---|---|---|
| 1 | Diretor(a) Geral | Apoio administrativo e institucional à Direção-Geral do campus. | true | diretor |
| 2 | Diretor(a) de Ensino | Gerencia as atividades acadêmicas e pedagógicas do campus. | true | diretor |
| 3 | Diretor(a) de Administração e Planejamento | Coordena planejamento administrativo, orçamento e gestão institucional. | true | diretor |
| 4 | Coordenador(a) de Tecnologia da Informação | Responsável pela infraestrutura e suporte de TI. | true | coordenador |
| 5 | Diretor(a) de Pesquisa, Extensão e Inovação | Gerencia ações de pesquisa, inovação e pós-graduação. | true | diretor |
| 6 | Coordenador(a) de Extensão | Coordena projetos e ações de extensão junto à comunidade. | true | coordenador |
| 7 | Coordenador(a) de Gestão de Pessoas | Atua na gestão de servidores e processos de RH. | true | coordenador |
| 8 | Coordenador(a) de Saúde | Desenvolve ações de saúde e assistência institucional. | true | coordenador |
| 9 | Coordenador(a) de Patrimônio e Almoxarifado | Controle patrimonial e gestão de materiais e estoque. | true | coordenador |
| 10 | Coordenador(a) de Logística e Manutenção | Responsável por manutenção predial e logística institucional. | true | coordenador |
| 11 | Coordenador(a) de Compras e Licitação | Gerencia compras públicas e processos licitatórios. | true | coordenador |
| 12 | Coordenador(a) de Orçamento, Contabilidade e Finanças | Executa orçamento, contabilidade e finanças do campus. | true | coordenador |
| 13 | Coordenador(a) de Apoio ao Ensino | Apoia atividades pedagógicas e assistência acadêmica. | true | coordenador |
| 14 | Coordenador(a) de Controle Acadêmico | Gerencia registros acadêmicos e documentação estudantil. | true | coordenador |
| 15 | Coordenador(a) de Disciplina | Atua em acompanhamento disciplinar e convivência escolar. | true | coordenador |
| 16 | Coordenador(a) NAPNE | Promove inclusão e acessibilidade educacional. | true | coordenador |
| 17 | Coordenador(a) de Integração, Estágios, Egressos e Emprego | Coordena estágios e acompanhamento de egressos. | true | coordenador |
| 18 | Coordenador(a) da Biblioteca | Gerencia serviços bibliográficos e acervo. | true | coordenador |
| 19 | Coordenador(a) de Ensino Técnico | Coordena cursos técnicos do campus. | true | coordenador |
| 20 | Coordenador(a) de Ensino Superior | Coordena os cursos superiores do campus. | true | coordenador |
| 21 | Coordenador(a) do Curso de Tecnologia em ADS | Coordenação do curso técnico de Análise e Desenvolvimento de Sistemas. | true | coordenador |
| 22 | Coordenador(a) do Curso Técnico em Informática | Coordenação do curso técnico em Informática. | true | coordenador |
| 23 | Coordenador(a) do Curso Técnico em Edificações | Coordenação do curso técnico em Edificações. | true | coordenador |
| 24 | Coordenador(a) do Curso Técnico em Meio Ambiente | Coordenação do curso técnico em Meio Ambiente. | true | coordenador |
| 25 | Coordenador(a) das Áreas de Natureza, Humanas e Letras | Integração pedagógica das áreas básicas. | true | coordenador |
| 26 | Coordenador(a) do Mestrado PROFMAT | Coordena o programa de mestrado profissional em Matemática. | true | coordenador |
| 27 | Chefe de Departamento de Ensino Superior | Coordena e acompanha as atividades acadêmicas dos cursos superiores. | true | chefe |
| 28 | Chefe de Departamento de Ensino Técnico | Coordena e acompanha as atividades acadêmicas dos cursos técnicos. | true | chefe |
| 29 | Chefe de Departamento de Apoio ao Ensino | Coordena os serviços de apoio às atividades de ensino. | true | chefe |
| 30 | Chefe de Gabinete da Diretoria Geral | Assessora a Diretoria-Geral na coordenação das atividades administrativas e institucionais. | true | chefe |
| 31 | Chefe de Departamento de Compras e Licitação | Coordena os processos de compras, contratações e licitações da instituição. | true | chefe |
| 32 | Coodernador(a) do Curso de Tecnologia em Análise e Desenvolvimento de Sistemas | Coordenação do curso superior deTecnologia em Análise e Desenvolvimento de Sistemas. | true | coordenador |
| 36 | Coordenador(a) do Curso de Licenciatura em Matemática | Coordenação do curso de Licenciatura em Matemática. | true | coordenador |
| 37 | Coordenador(a) do Curso de Licenciatura em Ciências Biológicas | Coordenação do curso de Licenciatura em Ciências Biológicas. | true | coordenador |
| 38 | Coordenador(a) do Curso Técnico em Eletromecânica | Coordenação do curso técnico em Eletromecânica. | true | coordenador |
| 39 | Coordenador(a) do Curso de Bacharelado em Engenharia Civil | Coordenação do curso de Bacharelado em Engenharia Civil. | true | coordenador |
| 40 | Coordenador(a) do Curso Técnico em Administração | Coordenação do curso técnico em Administração. | true | coordenador |
| 41 | Coordenador(a) da Especialização em Ensino de Ciências Biológicas | Coordenação da pós-graduação/especialização em Ensino de Ciências Biológicas. | true | coordenador |
| 42 | Coodernador(a) do Departamento de Contabilidade e Patrimônio | Coordenação do departamento de Contabilidade e Patrimônio | true | coordenador |
| 43 | Coordenador(a ) do Curso Técnico em Meio Ambiente (PROEJA) | Coordernação do Curso Técnico em Meio Ambiente (PROEJA) | true | coordenador |

----------

## Setor_Lotacao

Relaciona usuários com setores e funções.

### Campos

Campo

Tipo

Descrição

usuario_id

int (FK)

Referência para Usuario

setor_id

int (FK)

Referência para Setor

funcao_id

String (FK)

Referência para Funcao

responsavel

boolean

Indica responsabilidade pelo setor

monitor

boolean

Indica atuação como monitor

----------

# Relacionamentos Principais

## Usuário

O `Usuario` é a entidade central do sistema.

Ela pode possuir:

-   Um contato
    
-   Um endereço
    
-   Um perfil de aluno (com matrícula opcional em `Aluno_Curso`)
    
-   Um perfil de servidor (com `matricula` opcional)
    
-   Um perfil de terceirizado (com `matricula` opcional)
    
-   Uma ou mais lotações institucionais
    

----------

## Acadêmico

-   `Aluno` possui relação N:N com `Curso` através de `Aluno_Curso`
    
-   `Curso` possui relação N:1 com `Setor` (`setor_id`)
    
-   Cursos podem estar ativos ou inativos
    
-   O sistema suporta múltiplos cursos por aluno
    

----------

## Institucional

-   `Servidor` pertence a um `Cargo`
    
-   `Servidor` pode ser professor ou técnico administrativo
    
-   `Usuario` pode ser lotado em setores
    
-   `Funcao` descreve responsabilidades institucionais
    

----------