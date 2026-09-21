from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0004_conferencia_finalizada_por'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='primeira_chamada_concluida',
            field=models.BooleanField(
                default=False,
                verbose_name='Primeira chamada concluída',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='primeira_chamada_concluida_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Primeira chamada concluída em',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='segunda_chamada_pulada',
            field=models.BooleanField(
                default=False,
                verbose_name='Segunda chamada pulada',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='primeira_chamada_concluida',
            field=models.BooleanField(
                default=False,
                verbose_name='Primeira chamada concluída',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='primeira_chamada_concluida_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Primeira chamada concluída em',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='segunda_chamada_pulada',
            field=models.BooleanField(
                default=False,
                verbose_name='Segunda chamada pulada',
            ),
        ),
    ]
