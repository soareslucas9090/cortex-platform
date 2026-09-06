from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0003_timestamps_conferencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='chamada_ausentes_codigos',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='Códigos ausentes da chamada',
            ),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='chamada_ausentes_codigos',
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name='Códigos ausentes da chamada',
            ),
        ),
    ]
