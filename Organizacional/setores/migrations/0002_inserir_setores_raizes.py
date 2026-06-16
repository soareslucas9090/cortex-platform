from django.db import migrations


def inserir_setores_raizes(apps, schema_editor):
    Setor = apps.get_model('setores', 'Setor')

    setores = [
        {"nome": "Diretoria de Ensino", "sigla": "DENS", "ativo": True},
        {"nome": "Diretoria de Administração e Planejamento", "sigla": "DIAP", "ativo": True},
        {"nome": "Coordenação de Disciplina", "sigla": "CODIS", "ativo": True},
        {"nome": "Coordenação de Controle Acadêmico", "sigla": "COCACAD", "ativo": True},
        {"nome": "Núcleo de Atendimento às Pessoas com Necessidades Específicas", "sigla": "NAPNE", "ativo": True},
        {"nome": "Coordenação de Logística e Manutenção", "sigla": "DLMC", "ativo": True},
        {"nome": "Departamento de Apoio ao Ensino", "sigla": "DAENS", "ativo": True},
        {"nome": "Coordenação de Biblioteca", "sigla": "COBIB", "ativo": True},
        {"nome": "Departamento de Ensino Técnico", "sigla": "DEPENTE", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Meio Ambiente", "sigla": "CTEMEAM", "ativo": True},
        {"nome": "Coordenação de Patrimônio e Almoxarifado", "sigla": "DCOPAT", "ativo": True},
        {"nome": "Coordenação das Áreas de Ciências da Natureza, Ciências Humanas e Linguagens", "sigla": "CANHL", "ativo": True},
        {"nome": "Departamento de Ensino Superior", "sigla": "DEPENSU", "ativo": True},
        {"nome": "Coordenação de Gestão de Pessoas", "sigla": "CGP", "ativo": True},
        {"nome": "Diretoria-Geral", "sigla": "DG", "ativo": True},
        {"nome": "Coordenação de Integração, Estágios, Egressos e Emprego", "sigla": "CEICOM", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Eletromecânica", "sigla": "COCTECEL", "ativo": True},
        {"nome": "Gabinete da Diretoria-Geral", "sigla": "GDG", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Edificações", "sigla": "CCEDI", "ativo": True},
        {"nome": "Coordenação-Geral de Assistência Estudantil", "sigla": "CGAE", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Desenvolvimento de Sistemas", "sigla": "CCTDS", "ativo": True},
        {"nome": "Coordenação de Patrimônio e Almoxarifado", "sigla": "CPA", "ativo": True},
        {"nome": "Coordenação do Curso de Licenciatura em Matemática", "sigla": "CCLM", "ativo": True},
        {"nome": "Coordenação do Mestrado Profissional em Matemática", "sigla": "PROFMAT", "ativo": True},
        {"nome": "Coordenação do Curso de Licenciatura em Matemática", "sigla": "CCL", "ativo": True},
        {"nome": "Coordenação do Curso de Análise e Desenvolvimento de Sistemas", "sigla": "CCADS", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Administração", "sigla": "COCURADM", "ativo": True},
        {"nome": "Coordenação do Curso de Bacharelado em Engenharia Civil", "sigla": "COCENGCIV", "ativo": True},
        {"nome": "Coordenação de Extensão", "sigla": "CEXT", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Meio Ambiente PROEJA", "sigla": "COTMEAMBPR", "ativo": True},
        {"nome": "Coordenação da Especialização em Ensino de Ciências Biológicas", "sigla": "ECIENCBIO", "ativo": True},
        {"nome": "Coordenação do Curso de Licenciatura em Ciências Biológicas", "sigla": "CCLCB", "ativo": True},
        {"nome": "Coordenação de Pesquisa e Inovação", "sigla": "CPI", "ativo": True},
        {"nome": "Coordenação do Curso Técnico em Informática", "sigla": "CCTI", "ativo": True},
        {"nome": "Coordenação de Tecnologia da Informação", "sigla": "CTI", "ativo": True},
    ]

    for setor_data in setores:
        # Usa get_or_create com base na sigla para garantir a idempotência.
        Setor.objects.get_or_create(
            sigla=setor_data['sigla'],
            defaults={
                'nome': setor_data['nome'],
                'ativo': setor_data['ativo'],
            }
        )


def remover_setores_raizes(apps, schema_editor):
    Setor = apps.get_model('setores', 'Setor')
    siglas = [
        "DENS", "DIAP", "CODIS", "COCACAD", "NAPNE", "DLMC", "DAENS", "COBIB",
        "DEPENTE", "CTEMEAM", "DCOPAT", "CANHL", "DEPENSU", "CGP", "DG", "CEICOM",
        "COCTECEL", "GDG", "CCEDI", "CGAE", "CCTDS", "CPA", "CCLM", "PROFMAT",
        "CCL", "CCADS", "COCURADM", "COCENGCIV", "CEXT", "COTMEAMBPR", "ECIENCBIO",
        "CCLCB", "CPI", "CCTI", "CTI"
    ]
    Setor.objects.filter(sigla__in=siglas).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('setores', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_setores_raizes, reverse_code=remover_setores_raizes),
    ]
