from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0004_associar_setores_aos_cursos'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='nivel_ensino',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, 'Ensino Médio'),
                    (2, 'Técnico'),
                    (3, 'Superior'),
                    (4, 'Pós-graduação'),
                ],
                null=True,
                verbose_name='Nível de ensino',
            ),
        ),
        migrations.AddField(
            model_name='historicalcurso',
            name='nivel_ensino',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, 'Ensino Médio'),
                    (2, 'Técnico'),
                    (3, 'Superior'),
                    (4, 'Pós-graduação'),
                ],
                null=True,
                verbose_name='Nível de ensino',
            ),
        ),
    ]
