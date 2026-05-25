from django.db import migrations


def inserir_empresas_raizes(apps, schema_editor):
    EmpresaInstituicao = apps.get_model('empresas_instituicoes', 'EmpresaInstituicao')

    empresas = [
        {"nome": "CASTELO SERVIÇOS DE SEGURANÇA LTDA.", "cnpj": None, "ativo": True},
        {"nome": "SERVFAZ SERVIÇOS DE MÃO DE OBRA LTDA.", "cnpj": None, "ativo": True},
        {"nome": "SERVIRE AGENCIAMENTO DE MÃO DE OBRA LTDA.", "cnpj": None, "ativo": True},
    ]

    for empresa_data in empresas:
        # Usa get_or_create com base no nome para garantir a idempotência.
        EmpresaInstituicao.objects.get_or_create(
            nome=empresa_data['nome'],
            defaults={
                'cnpj': empresa_data['cnpj'],
                'ativo': empresa_data['ativo'],
            }
        )


def remover_empresas_raizes(apps, schema_editor):
    EmpresaInstituicao = apps.get_model('empresas_instituicoes', 'EmpresaInstituicao')
    nomes = [
        "CASTELO SERVIÇOS DE SEGURANÇA LTDA.",
        "SERVFAZ SERVIÇOS DE MÃO DE OBRA LTDA.",
        "SERVIRE AGENCIAMENTO DE MÃO DE OBRA LTDA.",
    ]
    EmpresaInstituicao.objects.filter(nome__in=nomes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('empresas_instituicoes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_empresas_raizes, reverse_code=remover_empresas_raizes),
    ]
