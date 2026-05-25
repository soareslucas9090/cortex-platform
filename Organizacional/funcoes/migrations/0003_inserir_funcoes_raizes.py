from django.db import migrations


def inserir_funcoes_raizes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')

    funcoes = [
        {"sigla": "GABDG", "descricao": "Gabinete da Diretoria-Geral", "ativo": True},
        {"sigla": "DIREN / DENS", "descricao": "Diretoria de Ensino", "ativo": True},
        {"sigla": "DEPAP / DIAP", "descricao": "Departamento/Diretoria de Administração e Planejamento", "ativo": True},
        {"sigla": "COTI", "descricao": "Coordenação de Tecnologia da Informação", "ativo": True},
        {"sigla": "COPI", "descricao": "Coordenação de Pesquisa e Inovação", "ativo": True},
        {"sigla": "COEX", "descricao": "Coordenação de Extensão", "ativo": True},
        {"sigla": "COGP", "descricao": "Coordenação de Gestão de Pessoas", "ativo": True},
        {"sigla": "COSA", "descricao": "Coordenação de Saúde", "ativo": True},
        {"sigla": "COPAL / CPA", "descricao": "Coordenação de Patrimônio e Almoxarifado", "ativo": True},
        {"sigla": "COLM / DLMC", "descricao": "Coordenação/Departamento de Logística e Manutenção", "ativo": True},
        {"sigla": "COCL", "descricao": "Coordenação de Compras e Licitação", "ativo": True},
        {"sigla": "COOCF", "descricao": "Coordenação de Orçamento, Contabilidade e Finanças", "ativo": True},
        {"sigla": "DAE", "descricao": "Departamento de Apoio ao Ensino", "ativo": True},
        {"sigla": "CCA", "descricao": "Coordenação de Controle Acadêmico", "ativo": True},
        {"sigla": "CODIS", "descricao": "Coordenação de Disciplina", "ativo": True},
        {"sigla": "NAPNE", "descricao": "Núcleo de Atendimento às Pessoas com Necessidades Específicas", "ativo": True},
        {"sigla": "SIEE", "descricao": "Serviço de Integração, Estágios, Egressos e Emprego", "ativo": True},
        {"sigla": "COBIB", "descricao": "Coordenação de Biblioteca", "ativo": True},
        {"sigla": "DET", "descricao": "Departamento de Ensino Técnico", "ativo": True},
        {"sigla": "DES", "descricao": "Departamento de Ensino Superior", "ativo": True},
        {"sigla": "CTADS", "descricao": "Coordenação do Curso de Tecnologia em ADS", "ativo": True},
        {"sigla": "CCTI", "descricao": "Coordenação do Curso Técnico em Informática", "ativo": True},
        {"sigla": "COEDIF", "descricao": "Coordenação do Curso Técnico em Edificações", "ativo": True},
        {"sigla": "CCTMA", "descricao": "Coordenação do Curso Técnico em Meio Ambiente", "ativo": True},
        {"sigla": "COANHL", "descricao": "Coordenação das Áreas de Natureza, Humanas e Letras", "ativo": True},
        {"sigla": "PROFMAT", "descricao": "Coordenação do Mestrado PROFMAT", "ativo": True},
    ]

    for funcao_data in funcoes:
        # Usa get_or_create com base na sigla para garantir a idempotência.
        Funcao.objects.get_or_create(
            sigla=funcao_data['sigla'],
            defaults={
                'descricao': funcao_data['descricao'],
                'ativo': funcao_data['ativo'],
            }
        )


def remover_funcoes_raizes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')
    siglas = [
        "GABDG", "DIREN / DENS", "DEPAP / DIAP", "COTI", "COPI", "COEX", "COGP",
        "COSA", "COPAL / CPA", "COLM / DLMC", "COCL", "COOCF", "DAE", "CCA",
        "CODIS", "NAPNE", "SIEE", "COBIB", "DET", "DES", "CTADS", "CCTI",
        "COEDIF", "CCTMA", "COANHL", "PROFMAT"
    ]
    Funcao.objects.filter(sigla__in=siglas).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('funcoes', '0002_funcao_exige_aluno_historicalfuncao_exige_aluno'),
    ]

    operations = [
        migrations.RunPython(inserir_funcoes_raizes, reverse_code=remover_funcoes_raizes),
    ]
