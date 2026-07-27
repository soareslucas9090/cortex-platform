from django.db import migrations


def inserir_funcoes_raizes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')

    funcoes = [
        {"papel_funcao": "Diretor(a) Geral", "descricao": "Apoio administrativo e institucional à Direção-Geral do campus.", "ativo": True},
        {"papel_funcao": "Diretor(a) de Ensino", "descricao": "Gerencia as atividades acadêmicas e pedagógicas do campus.", "ativo": True},
        {"papel_funcao": "Diretor(a) de Administração e Planejamento", "descricao": "Coordena planejamento administrativo, orçamento e gestão institucional.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Tecnologia da Informação", "descricao": "Responsável pela infraestrutura e suporte de TI.", "ativo": True},
        {"papel_funcao": "Diretor(a) de Pesquisa, Extensão e Inovação", "descricao": "Gerencia ações de pesquisa, inovação e pós-graduação.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Extensão", "descricao": "Coordena projetos e ações de extensão junto à comunidade.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Gestão de Pessoas", "descricao": "Atua na gestão de servidores e processos de RH.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Saúde", "descricao": "Desenvolve ações de saúde e assistência institucional.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Patrimônio e Almoxarifado", "descricao": "Controle patrimonial e gestão de materiais e estoque.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Logística e Manutenção", "descricao": "Responsável por manutenção predial e logística institucional.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Compras e Licitação", "descricao": "Gerencia compras públicas e processos licitatórios.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Orçamento, Contabilidade e Finanças", "descricao": "Executa orçamento, contabilidade e finanças do campus.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Apoio ao Ensino", "descricao": "Apoia atividades pedagógicas e assistência acadêmica.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Controle Acadêmico", "descricao": "Gerencia registros acadêmicos e documentação estudantil.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Disciplina", "descricao": "Atua em acompanhamento disciplinar e convivência escolar.", "ativo": True},
        {"papel_funcao": "Coordenador(a) NAPNE", "descricao": "Promove inclusão e acessibilidade educacional.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Integração, Estágios, Egressos e Emprego", "descricao": "Coordena estágios e acompanhamento de egressos.", "ativo": True},
        {"papel_funcao": "Coordenador(a) da Biblioteca", "descricao": "Gerencia serviços bibliográficos e acervo.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Ensino Técnico", "descricao": "Coordena cursos técnicos do campus.", "ativo": True},
        {"papel_funcao": "Coordenador(a) de Ensino Superior", "descricao": "Coordena os cursos superiores do campus.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso de Tecnologia em ADS", "descricao": "Coordenação do curso técnico de Análise e Desenvolvimento de Sistemas.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso Técnico em Informática", "descricao": "Coordenação do curso técnico em Informática.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso Técnico em Edificações", "descricao": "Coordenação do curso técnico em Edificações.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso Técnico em Meio Ambiente", "descricao": "Coordenação do curso técnico em Meio Ambiente.", "ativo": True},
        {"papel_funcao": "Coordenador(a) das Áreas de Natureza, Humanas e Letras", "descricao": "Integração pedagógica das áreas básicas.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Mestrado PROFMAT", "descricao": "Coordena o programa de mestrado profissional em Matemática.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Ensino Superior", "descricao": "Coordena e acompanha as atividades acadêmicas dos cursos superiores.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Ensino Técnico", "descricao": "Coordena e acompanha as atividades acadêmicas dos cursos técnicos.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Apoio ao Ensino", "descricao": "Coordena os serviços de apoio às atividades de ensino.", "ativo": True},
        {"papel_funcao": "Chefe de Gabinete da Diretoria Geral", "descricao": "Assessora a Diretoria-Geral na coordenação das atividades administrativas e institucionais.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Compras e Licitação", "descricao": "Coordena os processos de compras, contratações e licitações da instituição.", "ativo": True},
        {"papel_funcao": "Coodernador(a) do Curso de Tecnologia em Análise e Desenvolvimento de Sistemas", "descricao": "Coordenação do curso superior deTecnologia em Análise e Desenvolvimento de Sistemas.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso de Licenciatura em Matemática", "descricao": "Coordenação do curso de Licenciatura em Matemática.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso de Licenciatura em Ciências Biológicas", "descricao": "Coordenação do curso de Licenciatura em Ciências Biológicas.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso Técnico em Eletromecânica", "descricao": "Coordenação do curso técnico em Eletromecânica.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso de Bacharelado em Engenharia Civil", "descricao": "Coordenação do curso de Bacharelado em Engenharia Civil.", "ativo": True},
        {"papel_funcao": "Coordenador(a) do Curso Técnico em Administração", "descricao": "Coordenação do curso técnico em Administração.", "ativo": True},
        {"papel_funcao": "Coordenador(a) da Especialização em Ensino de Ciências Biológicas", "descricao": "Coordenação da pós-graduação/especialização em Ensino de Ciências Biológicas.", "ativo": True},
        {"papel_funcao": "Coodernador(a) do Departamento de Contabilidade e Patrimônio", "descricao": "Coordenação do departamento de Contabilidade e Patrimônio", "ativo": True},
        {"papel_funcao": "Coordenador(a ) do Curso Técnico em Meio Ambiente (PROEJA)", "descricao": "Coordernação do Curso Técnico em Meio Ambiente (PROEJA)", "ativo": True},
    ]

    for funcao_data in funcoes:
        Funcao.objects.get_or_create(
            papel_funcao=funcao_data['papel_funcao'],
            defaults={
                'descricao': funcao_data['descricao'],
                'ativo': funcao_data['ativo'],
            }
        )


def remover_funcoes_raizes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')
    papeis_funcao = [
        "Diretor(a) Geral",
        "Diretor(a) de Ensino",
        "Diretor(a) de Administração e Planejamento",
        "Coordenador(a) de Tecnologia da Informação",
        "Diretor(a) de Pesquisa, Extensão e Inovação",
        "Coordenador(a) de Extensão",
        "Coordenador(a) de Gestão de Pessoas",
        "Coordenador(a) de Saúde",
        "Coordenador(a) de Patrimônio e Almoxarifado",
        "Coordenador(a) de Logística e Manutenção",
        "Coordenador(a) de Compras e Licitação",
        "Coordenador(a) de Orçamento, Contabilidade e Finanças",
        "Coordenador(a) de Apoio ao Ensino",
        "Coordenador(a) de Controle Acadêmico",
        "Coordenador(a) de Disciplina",
        "Coordenador(a) NAPNE",
        "Coordenador(a) de Integração, Estágios, Egressos e Emprego",
        "Coordenador(a) da Biblioteca",
        "Coordenador(a) de Ensino Técnico",
        "Coordenador(a) de Ensino Superior",
        "Coordenador(a) do Curso de Tecnologia em ADS",
        "Coordenador(a) do Curso Técnico em Informática",
        "Coordenador(a) do Curso Técnico em Edificações",
        "Coordenador(a) do Curso Técnico em Meio Ambiente",
        "Coordenador(a) das Áreas de Natureza, Humanas e Letras",
        "Coordenador(a) do Mestrado PROFMAT",
        "Chefe de Departamento de Ensino Superior",
        "Chefe de Departamento de Ensino Técnico",
        "Chefe de Departamento de Apoio ao Ensino",
        "Chefe de Gabinete da Diretoria Geral",
        "Chefe de Departamento de Compras e Licitação",
        "Coodernador(a) do Curso de Tecnologia em Análise e Desenvolvimento de Sistemas",
        "Coordenador(a) do Curso de Licenciatura em Matemática",
        "Coordenador(a) do Curso de Licenciatura em Ciências Biológicas",
        "Coordenador(a) do Curso Técnico em Eletromecânica",
        "Coordenador(a) do Curso de Bacharelado em Engenharia Civil",
        "Coordenador(a) do Curso Técnico em Administração",
        "Coordenador(a) da Especialização em Ensino de Ciências Biológicas",
        "Coodernador(a) do Departamento de Contabilidade e Patrimônio",
        "Coordenador(a ) do Curso Técnico em Meio Ambiente (PROEJA)",
    ]
    Funcao.objects.filter(papel_funcao__in=papeis_funcao).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('funcoes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_funcoes_raizes, reverse_code=remover_funcoes_raizes),
    ]
