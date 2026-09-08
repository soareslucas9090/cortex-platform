from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0004_chamada_ausentes'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='entradas_cpf_concluidas',
            field=models.BooleanField(
                default=False,
                verbose_name='Entrada por CPF concluída',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='entradas_cpf_concluidas',
            field=models.BooleanField(
                default=False,
                verbose_name='Entrada por CPF concluída',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='entradas_cpf_concluidas_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Entrada por CPF concluída em',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='entradas_cpf_concluidas_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Entrada por CPF concluída em',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='entradas_cpf_codigos',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='CPFs do lote da conferência',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='entradas_cpf_codigos',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='CPFs do lote da conferência',
            ),
        ),
    ]
