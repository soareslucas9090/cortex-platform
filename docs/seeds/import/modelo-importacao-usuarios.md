# Modelo de Importação de Usuários

> Conversão integral do arquivo `modelo-importacao-usuarios.ods` para Markdown.
> Cada aba foi preservada como uma seção, e as células vazias foram mantidas.

## Aba: Usuario

<table>
  <tr>
    <td>usuario_id(int, PK)</td>
    <td>cpf(String)</td>
    <td>nome(String)</td>
    <td>foto(String)</td>
    <td>ativo(boolean)</td>
    <td>ultimo_login(Date)</td>
    <td>colaborador_externo(booleano)</td>
  </tr>
</table>

## Aba: Contato

<table>
  <tr>
    <td>usuario_id(int, FK)</td>
    <td>email_academico(String)</td>
    <td>email_pessoal(String)</td>
    <td>telefone(String)</td>
  </tr>
</table>

## Aba: Endereco

<table>
  <tr>
    <td>usuario_id(int, FK)</td>
    <td>endereco(String)</td>
    <td>bairro(String)</td>
    <td>cidade(String)</td>
    <td>estado(String)</td>
  </tr>
</table>

## Aba: Aluno

<table>
  <tr>
    <td>aluno_id(int, PK)</td>
    <td>usuario_id(int, FK)</td>
    <td>ira(double)</td>
    <td>deficiencia(String)</td>
  </tr>
</table>

## Aba: Curso

<table>
  <tr>
    <td>curso_id(int, PK)</td>
    <td>nome(String)</td>
    <td>codigo_curso(String)</td>
    <td>ativo(boolean)</td>
    <td>modalidade(string)</td>
  </tr>
</table>

## Aba: Aluno_Curso

<table>
  <tr>
    <td>aluno_id(int, FK)</td>
    <td>curso_id(int, FK)</td>
    <td>ano_conclusao(int)</td>
    <td>matricula(String)</td>
    <td>ira(double)</td>
    <td>turma(String)</td>
    <td>turno(String)</td>
    <td>situacao_curso(String)</td>
  </tr>
</table>

## Aba: Servidor

<table>
  <tr>
    <td>servidor_id(int, PK)</td>
    <td>usuario_id(int, FK)</td>
    <td>cargo_id(int, FK)</td>
    <td>categoria(String)</td>
    <td>ativo(boolean)</td>
    <td>matricula(String)</td>
  </tr>
</table>

## Aba: Cargo

<table>
  <tr>
    <td>cargo_id(int, PK)</td>
    <td>nome(String)</td>
    <td>ativo(boolean)</td>
  </tr>
  <tr>
    <td>1</td>
    <td>PROF ENS BAS TEC TECNOLOGICO-SUBSTITUTO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>2</td>
    <td>ASSISTENTE EM ADMINISTRACAO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>3</td>
    <td>ASSISTENTE DE ALUNO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>4</td>
    <td>ADMINISTRADOR</td>
    <td>true</td>
  </tr>
  <tr>
    <td>5</td>
    <td>TEC DE TECNOLOGIA DA INFORMACAO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>6</td>
    <td>PROFESSOR ENS BASICO TECN TECNOLOGICO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>7</td>
    <td>ENGENHEIRO-AREA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>8</td>
    <td>BIBLIOTECARIO-DOCUMENTALISTA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>9</td>
    <td>VIGILANTE</td>
    <td>true</td>
  </tr>
  <tr>
    <td>10</td>
    <td>TECNICO EM AUDIOVISUAL</td>
    <td>true</td>
  </tr>
  <tr>
    <td>11</td>
    <td>CONTADOR</td>
    <td>true</td>
  </tr>
  <tr>
    <td>12</td>
    <td>AUXILIAR DE BIBLIOTECA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>13</td>
    <td>AUX EM ADMINISTRACAO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>14</td>
    <td>ENFERMEIRO-AREA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>15</td>
    <td>TECNICO EM ELETROTECNICA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>16</td>
    <td>TECNICO DE LABORATORIO AREA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>17</td>
    <td>PSICOLOGO-AREA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>18</td>
    <td>TECNICO EM ARQUIVO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>19</td>
    <td>ASSISTENTE SOCIAL</td>
    <td>true</td>
  </tr>
  <tr>
    <td>20</td>
    <td>TECNICO EM ASSUNTOS EDUCACIONAIS</td>
    <td>true</td>
  </tr>
  <tr>
    <td>21</td>
    <td>ODONTOLOGO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>22</td>
    <td>SECRETARIO EXECUTIVO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>23</td>
    <td>PEDAGOGO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>24</td>
    <td>ASSISTENTE DE LABORATORIO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>25</td>
    <td>NUTRICIONISTA-HABILITACAO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>26</td>
    <td>MEDICO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>27</td>
    <td>TECNICO EM ENFERMAGEM</td>
    <td>true</td>
  </tr>
  <tr>
    <td>28</td>
    <td>TECNICO EM SECRETARIADO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>29</td>
    <td>ANALISTA DE TEC DA INFORMACAO</td>
    <td>true</td>
  </tr>
</table>

## Aba: Terceirizado

<table>
  <tr>
    <td>terceirizado_id(int, PK)</td>
    <td>usuario_id(int, FK)</td>
    <td>empresa_instituicao_id(int, FK)</td>
    <td>ativo(boolean)</td>
    <td>matricula(String)</td>
  </tr>
</table>

## Aba: Empresa_Instituicao

<table>
  <tr>
    <td>empresa_instituicao_id(int, PK)</td>
    <td>nome(String)</td>
    <td>cnpj(String)</td>
    <td>ativo(boolean)</td>
  </tr>
  <tr>
    <td>1</td>
    <td>CASTELO SERVIÇOS DE SEGURANÇA LTDA.</td>
    <td></td>
    <td>true</td>
  </tr>
  <tr>
    <td>2</td>
    <td>SERVFAZ SERVIÇOS DE MÃO DE OBRA LTDA.</td>
    <td></td>
    <td>true</td>
  </tr>
  <tr>
    <td>3</td>
    <td>SERVIRE AGENCIAMENTO DE MÃO DE OBRA LTDA.</td>
    <td></td>
    <td>true</td>
  </tr>
</table>

## Aba: Setor

<table>
  <tr>
    <td>setor_id(int, PK)</td>
    <td>nome(String)</td>
    <td>sigla(String)</td>
    <td>ativo(boolean)</td>
  </tr>
  <tr>
    <td>1</td>
    <td>Diretoria de Ensino</td>
    <td>DENS</td>
    <td>true</td>
  </tr>
  <tr>
    <td>2</td>
    <td>Diretoria de Administração e Planejamento</td>
    <td>DIAP</td>
    <td>true</td>
  </tr>
  <tr>
    <td>3</td>
    <td>Coordenação de Disciplina</td>
    <td>CODIS</td>
    <td>true</td>
  </tr>
  <tr>
    <td>4</td>
    <td>Coordenação de Controle Acadêmico</td>
    <td>COCACAD</td>
    <td>true</td>
  </tr>
  <tr>
    <td>5</td>
    <td>Núcleo de Atendimento às Pessoas com Necessidades Específicas</td>
    <td>NAPNE/FLO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>6</td>
    <td>Coordenação de Logística e Manutenção</td>
    <td>DLMC</td>
    <td>true</td>
  </tr>
  <tr>
    <td>7</td>
    <td>Departamento de Apoio ao Ensino</td>
    <td>DAENS</td>
    <td>true</td>
  </tr>
  <tr>
    <td>8</td>
    <td>Coordenação de Biblioteca</td>
    <td>COBIB</td>
    <td>true</td>
  </tr>
  <tr>
    <td>9</td>
    <td>Departamento de Ensino Técnico</td>
    <td>DEPENTE</td>
    <td>true</td>
  </tr>
  <tr>
    <td>10</td>
    <td>Coordenação do Curso Técnico em Meio Ambiente</td>
    <td>CTEMEAM</td>
    <td>true</td>
  </tr>
  <tr>
    <td>11</td>
    <td>Coordenação de Patrimônio e Almoxarifado</td>
    <td>DCOPAT</td>
    <td>true</td>
  </tr>
  <tr>
    <td>12</td>
    <td>Coordenação das Áreas de Ciências da Natureza, Ciências Humanas e Linguagens</td>
    <td>CANHL</td>
    <td>true</td>
  </tr>
  <tr>
    <td>13</td>
    <td>Departamento de Ensino Superior</td>
    <td>DEPENSU</td>
    <td>true</td>
  </tr>
  <tr>
    <td>14</td>
    <td>Coordenação de Gestão de Pessoas</td>
    <td>CGP</td>
    <td>true</td>
  </tr>
  <tr>
    <td>15</td>
    <td>Diretoria-Geral</td>
    <td>DG</td>
    <td>true</td>
  </tr>
  <tr>
    <td>16</td>
    <td>Coordenação de Integração, Estágios, Egressos e Emprego</td>
    <td>CEICOM</td>
    <td>true</td>
  </tr>
  <tr>
    <td>17</td>
    <td>Coordenação do Curso Técnico em Eletromecânica</td>
    <td>COCTECEL</td>
    <td>true</td>
  </tr>
  <tr>
    <td>18</td>
    <td>Gabinete da Diretoria-Geral</td>
    <td>GDG</td>
    <td>true</td>
  </tr>
  <tr>
    <td>19</td>
    <td>Coordenação do Curso Técnico em Edificações</td>
    <td>CCEDI</td>
    <td>true</td>
  </tr>
  <tr>
    <td>20</td>
    <td>Coordenação-Geral de Assistência Estudantil</td>
    <td>CGAE</td>
    <td>true</td>
  </tr>
  <tr>
    <td>21</td>
    <td>Coordenação do Curso Técnico em Desenvolvimento de Sistemas</td>
    <td>CCTDS/FLO</td>
    <td>true</td>
  </tr>
  <tr>
    <td>22</td>
    <td>Coodernação da Comissão Própria de Avaliação</td>
    <td>CPA</td>
    <td>true</td>
  </tr>
  <tr>
    <td>23</td>
    <td>Coordenação do Curso de Licenciatura em Matemática</td>
    <td>CCLM</td>
    <td>true</td>
  </tr>
  <tr>
    <td>24</td>
    <td>Coordenação do Mestrado Profissional em Matemática</td>
    <td>PROFMAT</td>
    <td>true</td>
  </tr>
  <tr>
    <td>25</td>
    <td>Coordenação do Curso de Licenciatura em Matemática</td>
    <td>CCL</td>
    <td>true</td>
  </tr>
  <tr>
    <td>26</td>
    <td>Coordenação do Curso de Análise e Desenvolvimento de Sistemas</td>
    <td>CCADS</td>
    <td>true</td>
  </tr>
  <tr>
    <td>27</td>
    <td>Coordenação do Curso Técnico em Administração</td>
    <td>COCURADM/F</td>
    <td>true</td>
  </tr>
  <tr>
    <td>28</td>
    <td>Coordenação do Curso de Bacharelado em Engenharia Civil</td>
    <td>COCENGCIV/</td>
    <td>true</td>
  </tr>
  <tr>
    <td>29</td>
    <td>Coordenação de Extensão</td>
    <td>CEXT</td>
    <td>true</td>
  </tr>
  <tr>
    <td>30</td>
    <td>Coordenação do Curso Técnico em Meio Ambiente PROEJA</td>
    <td>COTMEAMBPR</td>
    <td>true</td>
  </tr>
  <tr>
    <td>31</td>
    <td>Coordenação da Especialização em Ensino de Ciências Biológicas</td>
    <td>ECIENCBIO/</td>
    <td>true</td>
  </tr>
  <tr>
    <td>32</td>
    <td>Coordenação do Curso de Licenciatura em Ciências Biológicas</td>
    <td>CCLCB</td>
    <td>true</td>
  </tr>
  <tr>
    <td>33</td>
    <td>Coordenação de Pesquisa e Inovação</td>
    <td>CPI</td>
    <td>true</td>
  </tr>
  <tr>
    <td>34</td>
    <td>Coordenação do Curso Técnico em Informática</td>
    <td>CCTI</td>
    <td>true</td>
  </tr>
  <tr>
    <td>35</td>
    <td>Coordenação de Tecnologia da Informação</td>
    <td>CTI</td>
    <td>true</td>
  </tr>
</table>

## Aba: Funcao

<table>
  <tr>
    <td>funcao_id(String, PK)</td>
    <td>funcao (String)</td>
    <td>descricao(String)</td>
    <td>ativo(boolean)</td>
    <td>Categoria</td>
  </tr>
  <tr>
    <td>1</td>
    <td>Diretor(a) Geral</td>
    <td>Apoio administrativo e institucional à Direção-Geral do campus.</td>
    <td>true</td>
    <td>Diretor</td>
  </tr>
  <tr>
    <td>2</td>
    <td>Diretor(a) de Ensino</td>
    <td>Gerencia as atividades acadêmicas e pedagógicas do campus.</td>
    <td>true</td>
    <td>Diretor</td>
  </tr>
  <tr>
    <td>3</td>
    <td>Diretor(a) de Administração e Planejamento</td>
    <td>Coordena planejamento administrativo, orçamento e gestão institucional.</td>
    <td>true</td>
    <td>Diretor</td>
  </tr>
  <tr>
    <td>4</td>
    <td>Coordenador(a) de Tecnologia da Informação</td>
    <td>Responsável pela infraestrutura e suporte de TI.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>5</td>
    <td>Diretor(a) de Pesquisa, Extensão e Inovação</td>
    <td>Gerencia ações de pesquisa, inovação e pós-graduação.</td>
    <td>true</td>
    <td>Diretor</td>
  </tr>
  <tr>
    <td>6</td>
    <td>Coordenador(a) de Extensão</td>
    <td>Coordena projetos e ações de extensão junto à comunidade.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>7</td>
    <td>Coordenador(a) de Gestão de Pessoas</td>
    <td>Atua na gestão de servidores e processos de RH.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>8</td>
    <td>Coordenador(a) de Saúde</td>
    <td>Desenvolve ações de saúde e assistência institucional.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>9</td>
    <td>Coordenador(a) de Patrimônio e Almoxarifado</td>
    <td>Controle patrimonial e gestão de materiais e estoque.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>10</td>
    <td>Coordenador(a) de Logística e Manutenção</td>
    <td>Responsável por manutenção predial e logística institucional.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>11</td>
    <td>Coordenador(a) de Compras e Licitação</td>
    <td>Gerencia compras públicas e processos licitatórios.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>12</td>
    <td>Coordenador(a) de Orçamento, Contabilidade e Finanças</td>
    <td>Executa orçamento, contabilidade e finanças do campus.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>13</td>
    <td>Coordenador(a) de Apoio ao Ensino</td>
    <td>Apoia atividades pedagógicas e assistência acadêmica.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>14</td>
    <td>Coordenador(a) de Controle Acadêmico</td>
    <td>Gerencia registros acadêmicos e documentação estudantil.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>15</td>
    <td>Coordenador(a) de Disciplina</td>
    <td>Atua em acompanhamento disciplinar e convivência escolar.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>16</td>
    <td>Coordenador(a) NAPNE</td>
    <td>Promove inclusão e acessibilidade educacional.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>17</td>
    <td>Coordenador(a) de Integração, Estágios, Egressos e Emprego</td>
    <td>Coordena estágios e acompanhamento de egressos.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>18</td>
    <td>Coordenador(a) da Biblioteca</td>
    <td>Gerencia serviços bibliográficos e acervo.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>19</td>
    <td>Coordenador(a) de Ensino Técnico</td>
    <td>Coordena cursos técnicos do campus.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>20</td>
    <td>Coordenador(a) de Ensino Superior</td>
    <td>Coordena os cursos superiores do campus.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>21</td>
    <td>Coordenador(a) do Curso de Tecnologia em ADS</td>
    <td>Coordenação do curso técnico de Análise e Desenvolvimento de Sistemas.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>22</td>
    <td>Coordenador(a) do Curso Técnico em Informática</td>
    <td>Coordenação do curso técnico em Informática.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>23</td>
    <td>Coordenador(a) do Curso Técnico em Edificações</td>
    <td>Coordenação do curso técnico em Edificações.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>24</td>
    <td>Coordenador(a) do Curso Técnico em Meio Ambiente</td>
    <td>Coordenação do curso técnico em Meio Ambiente.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>25</td>
    <td>Coordenador(a) das Áreas de Natureza, Humanas e Letras</td>
    <td>Integração pedagógica das áreas básicas.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>26</td>
    <td>Coordenador(a) do Mestrado PROFMAT</td>
    <td>Coordena o programa de mestrado profissional em Matemática.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>27</td>
    <td>Chefe de Departamento de Ensino Superior</td>
    <td>Coordena e acompanha as atividades acadêmicas dos cursos superiores.</td>
    <td>true</td>
    <td>Chefe</td>
  </tr>
  <tr>
    <td>28</td>
    <td>Chefe de Departamento de Ensino Técnico</td>
    <td>Coordena e acompanha as atividades acadêmicas dos cursos técnicos.</td>
    <td>true</td>
    <td>Chefe</td>
  </tr>
  <tr>
    <td>29</td>
    <td>Chefe de Departamento de Apoio ao Ensino</td>
    <td>Coordena os serviços de apoio às atividades de ensino.</td>
    <td>true</td>
    <td>Chefe</td>
  </tr>
  <tr>
    <td>30</td>
    <td>Chefe de Gabinete da Diretoria Geral</td>
    <td>Assessora a Diretoria-Geral na coordenação das atividades administrativas e institucionais.</td>
    <td>true</td>
    <td>Chefe</td>
  </tr>
  <tr>
    <td>31</td>
    <td>Chefe de Departamento de Compras e Licitação</td>
    <td>Coordena os processos de compras, contratações e licitações da instituição.</td>
    <td>true</td>
    <td>Chefe</td>
  </tr>
  <tr>
    <td>32</td>
    <td>Coodernador(a) do Curso de Tecnologia em Análise e Desenvolvimento de Sistemas</td>
    <td>Coordenação do curso superior deTecnologia em Análise e Desenvolvimento de Sistemas.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>36</td>
    <td>Coordenador(a) do Curso de Licenciatura em Matemática</td>
    <td>Coordenação do curso de Licenciatura em Matemática.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>37</td>
    <td>Coordenador(a) do Curso de Licenciatura em Ciências Biológicas</td>
    <td>Coordenação do curso de Licenciatura em Ciências Biológicas.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>38</td>
    <td>Coordenador(a) do Curso Técnico em Eletromecânica</td>
    <td>Coordenação do curso técnico em Eletromecânica.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>39</td>
    <td>Coordenador(a) do Curso de Bacharelado em Engenharia Civil</td>
    <td>Coordenação do curso de Bacharelado em Engenharia Civil.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>40</td>
    <td>Coordenador(a) do Curso Técnico em Administração</td>
    <td>Coordenação do curso técnico em Administração.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>41</td>
    <td>Coordenador(a) da Especialização em Ensino de Ciências Biológicas</td>
    <td>Coordenação da pós-graduação/especialização em Ensino de Ciências Biológicas.</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>42</td>
    <td>Coodernador(a) do Departamento de Contabilidade e Patrimônio</td>
    <td>Coordenação do departamento de Contabilidade e Patrimônio</td>
    <td>true</td>
    <td>Coordenador</td>
  </tr>
  <tr>
    <td>43</td>
    <td>Coordenador(a ) do Curso Técnico em Meio Ambiente (PROEJA)</td>
    <td>Coordernação do Curso Técnico em Meio Ambiente (PROEJA)</td>
    <td></td>
    <td></td>
  </tr>
</table>

## Aba: Setor_Lotacao

<table>
  <tr>
    <td>usuario_id(int, FK)</td>
    <td>setor_id(int, FK)</td>
    <td>funcao_id(String, FK)</td>
    <td>responsavel(boolean)</td>
    <td>monitor(boolean)</td>
  </tr>
</table>
