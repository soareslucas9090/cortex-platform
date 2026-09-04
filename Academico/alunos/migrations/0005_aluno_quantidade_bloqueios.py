from django.db import migrations, models


def sincronizar_quantidade_bloqueios(apps, schema_editor):
    Aluno = apps.get_model('alunos', 'Aluno')
    Aluno.objects.filter(is_bloqueado=True).update(quantidade_bloqueios=1)
    Aluno.objects.filter(is_bloqueado=False).update(quantidade_bloqueios=0)


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0004_aluno_faltas_is_bloqueado'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='quantidade_bloqueios',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Número de vezes que o aluno entrou em bloqueio no transporte.',
                verbose_name='Quantidade de bloqueios',
            ),
        ),
        migrations.AddField(
            model_name='historicalaluno',
            name='quantidade_bloqueios',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Número de vezes que o aluno entrou em bloqueio no transporte.',
                verbose_name='Quantidade de bloqueios',
            ),
        ),
        migrations.RunPython(sincronizar_quantidade_bloqueios, migrations.RunPython.noop),
    ]
