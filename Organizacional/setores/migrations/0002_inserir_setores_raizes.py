from django.db import migrations


def inserir_setores_raizes(apps, schema_editor):
    Setor = apps.get_model('setores', 'Setor')

    setores = [
        {"nome": "DENS", "sigla": "DENS", "ativo": True},
        {"nome": "DIAP-IFPI", "sigla": "DIAP", "ativo": True},
        {"nome": "CODIS-IFPI", "sigla": "CODIS", "ativo": True},
        {"nome": "COCACAD", "sigla": "COCACAD", "ativo": True},
        {"nome": "NAPNE/FLO", "sigla": "NAPNE", "ativo": True},
        {"nome": "DLMC", "sigla": "DLMC", "ativo": True},
        {"nome": "DAENS", "sigla": "DAENS", "ativo": True},
        {"nome": "COBIB", "sigla": "COBIB", "ativo": True},
        {"nome": "DEPENTE", "sigla": "DEPENTE", "ativo": True},
        {"nome": "CTEMEAM", "sigla": "CTEMEAM", "ativo": True},
        {"nome": "DCOPAT", "sigla": "DCOPAT", "ativo": True},
        {"nome": "CANHL", "sigla": "CANHL", "ativo": True},
        {"nome": "DEPENSU", "sigla": "DEPENSU", "ativo": True},
        {"nome": "CGP", "sigla": "CGP", "ativo": True},
        {"nome": "DG-FLORIAN", "sigla": "DG", "ativo": True},
        {"nome": "CEICOM", "sigla": "CEICOM", "ativo": True},
        {"nome": "COCTECEL", "sigla": "COCTECEL", "ativo": True},
        {"nome": "GDG", "sigla": "GDG", "ativo": True},
        {"nome": "CCEDI", "sigla": "CCEDI", "ativo": True},
        {"nome": "CGAE", "sigla": "CGAE", "ativo": True},
        {"nome": "CCTDS/FLO", "sigla": "CCTDS", "ativo": True},
        {"nome": "CPA", "sigla": "CPA", "ativo": True},
        {"nome": "CCLM", "sigla": "CCLM", "ativo": True},
        {"nome": "PROFMAT", "sigla": "PROFMAT", "ativo": True},
        {"nome": "CCL", "sigla": "CCL", "ativo": True},
        {"nome": "CCADS", "sigla": "CCADS", "ativo": True},
        {"nome": "COCURADM/FLO", "sigla": "COCURADM", "ativo": True},
        {"nome": "COCENGCIV/FLO", "sigla": "COCENGCIV", "ativo": True},
        {"nome": "CEXT", "sigla": "CEXT", "ativo": True},
        {"nome": "COTMEAMBPRO/FLO", "sigla": "COTMEAMBPR", "ativo": True},
        {"nome": "ECIENCBIO/CAFLO", "sigla": "ECIENCBIO", "ativo": True},
        {"nome": "CCLCB", "sigla": "CCLCB", "ativo": True},
        {"nome": "CPI", "sigla": "CPI", "ativo": True},
        {"nome": "CCTI", "sigla": "CCTI", "ativo": True},
        {"nome": "CTI", "sigla": "CTI", "ativo": True},
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
