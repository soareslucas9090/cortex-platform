from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funcoes', '0002_inserir_funcoes_raizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcao',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('diretor', 'Diretor'),
                    ('coordenador', 'Coordenador'),
                    ('chefe', 'Chefe'),
                ],
                default='coordenador',
                max_length=20,
                verbose_name='Categoria',
            ),
        ),
        migrations.AddField(
            model_name='historicalfuncao',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('diretor', 'Diretor'),
                    ('coordenador', 'Coordenador'),
                    ('chefe', 'Chefe'),
                ],
                default='coordenador',
                max_length=20,
                verbose_name='Categoria',
            ),
        ),
    ]
