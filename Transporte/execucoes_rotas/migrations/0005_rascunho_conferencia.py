from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0004_conferencia_finalizada_por'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='chamada_rascunho',
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name='Rascunho da chamada',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='chamada_rascunho',
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name='Rascunho da chamada',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='entradas_cpf_rascunho',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='Rascunho de CPFs da conferência',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='entradas_cpf_rascunho',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='Rascunho de CPFs da conferência',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='versao_chamada',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Versão do rascunho da chamada',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='versao_chamada',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Versão do rascunho da chamada',
            ),
        ),
        migrations.AddField(
            model_name='execucaorota',
            name='versao_cpf',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Versão do rascunho de CPF',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='versao_cpf',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Versão do rascunho de CPF',
            ),
        ),
    ]
