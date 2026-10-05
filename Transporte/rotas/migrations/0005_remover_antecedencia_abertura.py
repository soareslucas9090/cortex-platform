from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rotas', '0004_derivar_dia_abertura'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='rota',
            name='rota_antecedencia_abertura_valida',
        ),
        migrations.RemoveField(
            model_name='historicalrota',
            name='dias_antecedencia_abertura',
        ),
        migrations.RemoveField(
            model_name='rota',
            name='dias_antecedencia_abertura',
        ),
    ]
