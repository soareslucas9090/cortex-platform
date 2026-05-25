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
    
-   Matrículas e lotações
    
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

## Matricula

Informações de matrícula institucional.

### Campos

Campo

Tipo

Descrição

usuario_id

int (FK)

Referência para Usuario

matricula

String

Código da matrícula

situacao

String

Situação da matrícula

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

ativo

boolean

Indica se o curso está ativo

### Dados raízes
  
|curso_id (int, PK)|nome (String)|codigo_curso (String)|ativo (boolean)|

|---|---|---|---|

|1|Formação Inicial em Agente de Inclusão Digital em Centros Públicos de Acesso à Internet - Campus Floriano|14FAID|true|

|2|Formação Inicial em Língua Brasileira de Sinais (Libras) - Básico - Campus Floriano|14FLIB|true|

|3|Formação Inicial em Inglês Básico - Campus Floriano|14FINB|true|

|4|Formação Inicial em Eletricista de Sistemas de Energias Renováveis - Campus Floriano|14FSER|true|

|5|Especialização em Desenvolvimento para Web|S.52|true|

|6|Especialização em Desporto Escolar e Desempenho Humano|S.53|true|

|7|Especialização em Ensino de Matemática no Ensino Médio|S.55|true|

|8|Especialização em Matemática|S.54|true|

|9|Especialização no Ensino de Ciências Biológicas|14EECB|true|

|10|Licenciatura em Ciências Biológicas / PARFOR - 2ª Licenciatura|S.04|true|

|11|Licenciatura em Ciências Biológicas - Floriano|14LBIO|true|

|12|Licenciatura em Ciências Biológicas / PARFOR - 1ª Licenciatura|S.03|true|

|13|Licenciatura em Matemática - Floriano|14LMAT|true|

|14|Licenciatura em Matemática / PARFOR - 2ª Licenciatura|S.05|true|

|15|Mestrado Profissional em Matemática / PROFMAT - Floriano|14PMAT|true|

|16|Técnico de Informática - Concomitante/Subsequente - Floriano|14MINF|true|

|17|Técnico de Segurança do Trabalho - EaD|B.61|true|

|18|Técnico de Serviços Jurídicos Subsequente - EaD|B.62|true|

|19|Técnico em Administração - EaD|TEAD|true|

|20|Técnico em Desenvolvimento de Sistemas - Concomitante/Subsequente - Floriano|14MTDS|true|

|21|Técnico em Edificações - Concomitante/Subsequente - Floriano|14MEDF|true|

|22|Técnico em Edificações - Integrado - Floriano|14IEDF|true|

|23|Técnico em Eletromecânica - Concomitante/Subsequente - Floriano|14MELM|true|

|24|Técnico em Eletromecânica - Integrado - Floriano|14IELM|true|

|25|Técnico em Informática - Integrado - Floriano|14IINF|true|

|26|Técnico em Informática para Internet - EaD|IPINT|true|

|27|Técnico em Logística - EaD|LOGI|true|

|28|Técnico em Meio Ambiente - EaD|MEAB|true|

|29|Técnico em Meio Ambiente - Integrado - Floriano|14IAMB|true|

|30|Técnico em Redes de Computadores|B.67|true|

|31|Técnico em Secretariado - EaD|SECR|true|

|32|Técnico em Serviços Públicos - EAD|TPF|true|

|33|Tecnologia em Análise e Desenvolvimento de Sistemas - Floriano|14TADS|true|

|34|Técnico em Meio Ambiente Integrado ao Ensino Médio - PROEJA|14JAMB|true|

|35|Formação Inicial em Músico de Banda|14FMB|true|

|36|Curso de Qualificação Profissional em Operador de Computador na Modalidade de Educação de Jovens e Adultos PROEJA-FIC-EPT|14JOPC|true|

|37|Técnico em Administração- Integrado - Floriano|14IADM|true|

|38|Bacharelado em Engenharia Civil - CAFLO|14BECV|true|

|39|Eletricista de Sistema de Energias Renováveis|14ASER|true|

|40|Preparatório para o Ensino Médio - PARTIU IF|14PIFPI|true|

|41|Formação Inicial em Redator de Textos Técnicos|14FRT|true|

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

|cargo_id (int, PK)|nome (String)|ativo (boolean)|

|---|---|---|

|1|PROF ENS BAS TEC TECNOLOGICO-SUBSTITUTO|true|

|2|ASSISTENTE EM ADMINISTRACAO|true|

|3|ASSISTENTE DE ALUNO|true|

|4|ADMINISTRADOR|true|

|5|TEC DE TECNOLOGIA DA INFORMACAO|true|

|6|PROFESSOR ENS BASICO TECN TECNOLOGICO|true|

|7|ENGENHEIRO|true|

|8|BIBLIOTECARIO-DOCUMENTALISTA|true|

|9|VIGILANTE|true|

|10|TECNICO EM AUDIOVISUAL|true|

|11|CONTADOR|true|

|12|AUXILIAR DE BIBLIOTECA|true|

|13|AUX EM ADMINISTRACAO|true|

|14|ENFERMEIRO|true|

|15|TECNICO EM ELETROTECNICA|true|

|16|TECNICO DE LABORATORIO|true|

|17|PSICOLOGO|true|

|18|TECNICO EM ARQUIVO|true|

|19|ASSISTENTE SOCIAL|true|

|20|TECNICO EM ASSUNTOS EDUCACIONAIS|true|

|21|ODONTOLOGO - 40 HORAS|true|

|22|SECRETARIO EXECUTIVO|true|

|23|PEDAGOGO|true|

|24|ASSISTENTE DE LABORATORIO|true|

|25|NUTRICIONISTA-HABILITACAO|true|

|26|MEDICO - PCCTAE|true|

|27|TECNICO EM ENFERMAGEM|true|

|28|TECNICO EM SECRETARIADO|true|

|29|ANALISTA DE TEC DA INFORMACAO|true|
    

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

|setor_id (int, PK)|nome (String)|sigla (String)|ativo (boolean)|

|---|---|---|---|

|1|DENS|DENS|true|

|2|DIAP-IFPI|DIAP|true|

|3|CODIS-IFPI|CODIS|true|

|4|COCACAD|COCACAD|true|

|5|NAPNE/FLO|NAPNE|true|

|6|DLMC|DLMC|true|

|7|DAENS|DAENS|true|

|8|COBIB|COBIB|true|

|9|DEPENTE|DEPENTE|true|

|10|CTEMEAM|CTEMEAM|true|

|11|DCOPAT|DCOPAT|true|

|12|CANHL|CANHL|true|

|13|DEPENSU|DEPENSU|true|

|14|CGP|CGP|true|

|15|DG-FLORIAN|DG|true|

|16|CEICOM|CEICOM|true|

|17|COCTECEL|COCTECEL|true|

|18|GDG|GDG|true|

|19|CCEDI|CCEDI|true|

|20|CGAE|CGAE|true|

|21|CCTDS/FLO|CCTDS|true|

|22|CPA|CPA|true|

|23|CCLM|CCLM|true|

|24|PROFMAT|PROFMAT|true|

|25|CCL|CCL|true|

|26|CCADS|CCADS|true|

|27|COCURADM/FLO|COCURADM|true|

|28|COCENGCIV/FLO|COCENGCIV|true|

|29|CEXT|CEXT|true|

|30|COTMEAMBPRO/FLO|COTMEAMBPR|true|

|31|ECIENCBIO/CAFLO|ECIENCBIO|true|

|32|CCLCB|CCLCB|true|

|33|CPI|CPI|true|

|34|CCTI|CCTI|true|

|35|CTI|CTI|true|

----------

## Funcao

Funções exercidas dentro dos setores.

### Campos

Campo

Tipo

Descrição

sigla

String (PK)

Identificador da função

funcao

String

Nome da função

descricao

String

Descrição funcional

ativo

boolean

Status

### Dados raízes


|sigla (String, PK)|funcao (String)|descricao (String)|ativo (boolean)|

|---|---|---|---|

|GABDG|Gabinete da Diretoria-Geral|Apoio administrativo e institucional à Direção-Geral do campus.|true|

|DIREN / DENS|Diretoria de Ensino|Gerencia as atividades acadêmicas e pedagógicas do campus.|true|

|DEPAP / DIAP|Departamento/Diretoria de Administração e Planejamento|Coordena planejamento administrativo, orçamento e gestão institucional.|true|

|COTI|Coordenação de Tecnologia da Informação|Responsável pela infraestrutura e suporte de TI.|true|

|COPI|Coordenação de Pesquisa e Inovação|Gerencia ações de pesquisa, inovação e pós-graduação.|true|

|COEX|Coordenação de Extensão|Coordena projetos e ações de extensão junto à comunidade.|true|

|COGP|Coordenação de Gestão de Pessoas|Atua na gestão de servidores e processos de RH.|true|

|COSA|Coordenação de Saúde|Desenvolve ações de saúde e assistência institucional.|true|

|COPAL / CPA|Coordenação de Patrimônio e Almoxarifado|Controle patrimonial e gestão de materiais e estoque.|true|

|COLM / DLMC|Coordenação/Departamento de Logística e Manutenção|Responsável por manutenção predial e logística institucional.|true|

|COCL|Coordenação de Compras e Licitação|Gerencia compras públicas e processos licitatórios.|true|

|COOCF|Coordenação de Orçamento, Contabilidade e Finanças|Executa orçamento, contabilidade e finanças do campus.|true|

|DAE|Departamento de Apoio ao Ensino|Apoia atividades pedagógicas e assistência acadêmica.|true|

|CCA|Coordenação de Controle Acadêmico|Gerencia registros acadêmicos e documentação estudantil.|true|

|CODIS|Coordenação de Disciplina|Atua em acompanhamento disciplinar e convivência escolar.|true|

|NAPNE|Núcleo de Atendimento às Pessoas com Necessidades Específicas|Promove inclusão e acessibilidade educacional.|true|

|SIEE|Serviço de Integração, Estágios, Egressos e Emprego|Coordena estágios e acompanhamento de egressos.|true|

|COBIB|Coordenação de Biblioteca|Gerencia serviços bibliográficos e acervo.|true|

|DET|Departamento de Ensino Técnico|Coordena cursos técnicos do campus.|true|

|DES|Departamento de Ensino Superior|Coordena os cursos superiores do campus.|true|

|CTADS|Coordenação do Curso de Tecnologia em ADS|Coordenação do curso superior de Análise e Desenvolvimento de Sistemas.|true|

|CCTI|Coordenação do Curso Técnico em Informática|Coordenação do curso técnico em Informática.|true|

|COEDIF|Coordenação do Curso Técnico em Edificações|Coordenação do curso técnico em Edificações.|true|

|CCTMA|Coordenação do Curso Técnico em Meio Ambiente|Coordenação do curso técnico em Meio Ambiente.|true|

|COANHL|Coordenação das Áreas de Natureza, Humanas e Letras|Integração pedagógica das áreas básicas.|true|

|PROFMAT|Coordenação do Mestrado PROFMAT|Coordena o programa de mestrado profissional em Matemática.|true|
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
    
-   Uma matrícula
    
-   Um perfil de aluno
    
-   Um perfil de servidor
    
-   Um perfil de terceirizado
    
-   Uma ou mais lotações institucionais
    

----------

## Acadêmico

-   `Aluno` possui relação N:N com `Curso` através de `Aluno_Curso`
    
-   Cursos podem estar ativos ou inativos
    
-   O sistema suporta múltiplos cursos por aluno
    

----------

## Institucional

-   `Servidor` pertence a um `Cargo`
    
-   `Servidor` pode ser professor ou técnico administrativo
    
-   `Usuario` pode ser lotado em setores
    
-   `Funcao` descreve responsabilidades institucionais
    

----------