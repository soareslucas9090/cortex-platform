from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0002_conferencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='monitoramento_iniciado_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Monitoramento iniciado em',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='monitoramento_iniciado_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Monitoramento iniciado em',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='chamada_concluida_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Chamada concluída em',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='chamada_concluida_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Chamada concluída em',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='finalizada_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Finalizada em',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='finalizada_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Finalizada em',
            ),
        ),
    ]
