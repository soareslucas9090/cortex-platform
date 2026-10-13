from django.db import migrations


def derivar_dia_abertura(apps, schema_editor):
    Rota = apps.get_model('rotas', 'Rota')
    for rota in Rota.objects.all().iterator():
        rota.dias_antecedencia_abertura = int(
            rota.horario_abertura_solicitacoes > rota.horario_saida
        )
        rota.save(update_fields=['dias_antecedencia_abertura'])


class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0003_abertura_solicitacoes_personalizada'),
    ]

    operations = [
        migrations.RunPython(derivar_dia_abertura, migrations.RunPython.noop),
    ]
