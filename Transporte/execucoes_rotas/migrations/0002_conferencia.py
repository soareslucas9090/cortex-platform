from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execucoes_rotas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='execucaorota',
            name='chamada_tickets_concluida',
            field=models.BooleanField(default=False, verbose_name='Chamada de tickets concluída'),
        ),
        migrations.AddField(
            model_name='historicalexecucaorota',
            name='chamada_tickets_concluida',
            field=models.BooleanField(default=False, verbose_name='Chamada de tickets concluída'),
        ),
    ]
