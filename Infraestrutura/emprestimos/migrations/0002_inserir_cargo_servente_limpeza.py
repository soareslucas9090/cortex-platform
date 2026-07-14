from django.db import migrations

from Infraestrutura.emprestimos.choices import CARGO_SERVENTE_LIMPEZA


def inserir_cargo_servente_limpeza(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')
    Cargo.objects.get_or_create(
        nome=CARGO_SERVENTE_LIMPEZA,
        defaults={'ativo': True},
    )


def remover_cargo_servente_limpeza(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')
    Cargo.objects.filter(nome=CARGO_SERVENTE_LIMPEZA).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cargos', '0002_inserir_cargos_raizes'),
        ('emprestimos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_cargo_servente_limpeza, reverse_code=remover_cargo_servente_limpeza),
    ]
