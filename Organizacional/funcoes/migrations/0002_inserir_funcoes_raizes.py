from django.db import migrations


def inserir_funcoes_raizes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')

    funcoes = [
        {"papel_funcao": "Diretor Geral", "descricao": "Apoio administrativo e institucional à Direção-Geral do campus.", "ativo": True},
        {"papel_funcao": "Diretor de Ensino", "descricao": "Gerencia as atividades acadêmicas e pedagógicas do campus.", "ativo": True},
        {"papel_funcao": "Diretor de Administração e Planejamento", "descricao": "Coordena planejamento administrativo, orçamento e gestão institucional.", "ativo": True},
        {"papel_funcao": "Coordenador de Tecnologia da Informação", "descricao": "Responsável pela infraestrutura e suporte de TI.", "ativo": True},
        {"papel_funcao": "Diretor de Pesquisa, Extensão e Inovação", "descricao": "Gerencia ações de pesquisa, inovação e pós-graduação.", "ativo": True},
        {"papel_funcao": "Coordenador de Extensão", "descricao": "Coordena projetos e ações de extensão junto à comunidade.", "ativo": True},
        {"papel_funcao": "Coordenador de Gestão de Pessoas", "descricao": "Atua na gestão de servidores e processos de RH.", "ativo": True},
        {"papel_funcao": "Coordenador de Saúde", "descricao": "Desenvolve ações de saúde e assistência institucional.", "ativo": True},
        {"papel_funcao": "Coordenador de Patrimônio e Almoxarifado", "descricao": "Controle patrimonial e gestão de materiais e estoque.", "ativo": True},
        {"papel_funcao": "Coordenador de Logística e Manutenção", "descricao": "Responsável por manutenção predial e logística institucional.", "ativo": True},
        {"papel_funcao": "Coordenador de Compras e Licitação", "descricao": "Gerencia compras públicas e processos licitatórios.", "ativo": True},
        {"papel_funcao": "Coordenador de Orçamento, Contabilidade e Finanças", "descricao": "Executa orçamento, contabilidade e finanças do campus.", "ativo": True},
        {"papel_funcao": "Coordenador de Apoio ao Ensino", "descricao": "Apoia atividades pedagógicas e assistência acadêmica.", "ativo": True},
        {"papel_funcao": "Coordenador de Controle Acadêmico", "descricao": "Gerencia registros acadêmicos e documentação estudantil.", "ativo": True},
        {"papel_funcao": "Coordenador de Disciplina", "descricao": "Atua em acompanhamento disciplinar e convivência escolar.", "ativo": True},
        {"papel_funcao": "Coordenador NAPNE", "descricao": "Promove inclusão e acessibilidade educacional.", "ativo": True},
        {"papel_funcao": "Coordenador de Integração, Estágios, Egressos e Emprego", "descricao": "Coordena estágios e acompanhamento de egressos.", "ativo": True},
        {"papel_funcao": "Coordenador da Biblioteca", "descricao": "Gerencia serviços bibliográficos e acervo.", "ativo": True},
        {"papel_funcao": "Coordenador de Ensino Técnico", "descricao": "Coordena cursos técnicos do campus.", "ativo": True},
        {"papel_funcao": "Coordenador de Ensino Superior", "descricao": "Coordena os cursos superiores do campus.", "ativo": True},
        {"papel_funcao": "Coordenador do Curso de Tecnologia em ADS", "descricao": "Coordenação do curso superior de Análise e Desenvolvimento de Sistemas.", "ativo": True},
        {"papel_funcao": "Coordenador do Curso Técnico em Informática", "descricao": "Coordenação do curso técnico em Informática.", "ativo": True},
        {"papel_funcao": "Coordenador do Curso Técnico em Edificações", "descricao": "Coordenação do curso técnico em Edificações.", "ativo": True},
        {"papel_funcao": "Coordenador do Curso Técnico em Meio Ambiente", "descricao": "Coordenação do curso técnico em Meio Ambiente.", "ativo": True},
        {"papel_funcao": "Coordenador das Áreas de Natureza, Humanas e Letras", "descricao": "Integração pedagógica das áreas básicas.", "ativo": True},
        {"papel_funcao": "Coordenador do Mestrado PROFMAT", "descricao": "Coordena o programa de mestrado profissional em Matemática.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Ensino Superior", "descricao": "Chefia o departamento de ensino superior do campus.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Ensino Técnico", "descricao": "Chefia o departamento de ensino técnico do campus.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Apoio ao Ensino", "descricao": "Chefia o departamento de apoio ao ensino do campus.", "ativo": True},
        {"papel_funcao": "Chefe de Gabinete da Diretoria Geral", "descricao": "Chefia o gabinete da diretoria geral do campus.", "ativo": True},
        {"papel_funcao": "Chefe de Departamento de Compras e Licitação", "descricao": "Chefia o departamento de compras e licitação do campus.", "ativo": True},
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
        "Diretor Geral", "Diretor de Ensino", "Diretor de Administração e Planejamento",
        "Coordenador de Tecnologia da Informação", "Diretor de Pesquisa, Extensão e Inovação",
        "Coordenador de Extensão", "Coordenador de Gestão de Pessoas", "Coordenador de Saúde",
        "Coordenador de Patrimônio e Almoxarifado", "Coordenador de Logística e Manutenção",
        "Coordenador de Compras e Licitação", "Coordenador de Orçamento, Contabilidade e Finanças",
        "Coordenador de Apoio ao Ensino", "Coordenador de Controle Acadêmico",
        "Coordenador de Disciplina", "Coordenador NAPNE",
        "Coordenador de Integração, Estágios, Egressos e Emprego", "Coordenador da Biblioteca",
        "Coordenador de Ensino Técnico", "Coordenador de Ensino Superior",
        "Coordenador do Curso de Tecnologia em ADS", "Coordenador do Curso Técnico em Informática",
        "Coordenador do Curso Técnico em Edificações", "Coordenador do Curso Técnico em Meio Ambiente",
        "Coordenador das Áreas de Natureza, Humanas e Letras", "Coordenador do Mestrado PROFMAT",
        "Chefe de Departamento de Ensino Superior", "Chefe de Departamento de Ensino Técnico",
        "Chefe de Departamento de Apoio ao Ensino", "Chefe de Gabinete da Diretoria Geral",
        "Chefe de Departamento de Compras e Licitação",
    ]
    Funcao.objects.filter(papel_funcao__in=papeis_funcao).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('funcoes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_funcoes_raizes, reverse_code=remover_funcoes_raizes),
    ]