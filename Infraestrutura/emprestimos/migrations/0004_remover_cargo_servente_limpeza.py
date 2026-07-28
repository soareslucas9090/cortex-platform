from django.db import migrations


CARGO_SERVENTE_LIMPEZA = 'SERVENTE DE LIMPEZA'


def remover_cargo_servente_limpeza(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')
    Cargo.objects.filter(nome=CARGO_SERVENTE_LIMPEZA).delete()


def reinserir_cargo_servente_limpeza(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')
    Cargo.objects.get_or_create(
        nome=CARGO_SERVENTE_LIMPEZA,
        defaults={'ativo': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('emprestimos', '0003_alter_ordering_alfabetica'),
        ('cargos', '0002_inserir_cargos_raizes'),
    ]

    operations = [
        migrations.RunPython(
            remover_cargo_servente_limpeza,
            reverse_code=reinserir_cargo_servente_limpeza,
        ),
    ]
