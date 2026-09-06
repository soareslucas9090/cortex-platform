from django.db import migrations, models
from django.db.models import Count


def sincronizar_quantidade_bloqueios(apps, schema_editor):
    Aluno = apps.get_model('alunos', 'Aluno')
    Strike = apps.get_model('strikes', 'Strike')

    strikes_por_aluno = {
        row['ticket__aluno_id']: row['total']
        for row in Strike.objects.values('ticket__aluno_id').annotate(total=Count('id'))
    }

    for aluno in Aluno.objects.all().iterator():
        total_strikes = strikes_por_aluno.get(aluno.usuario_id, 0)
        if aluno.is_bloqueado or total_strikes >= 3:
            aluno.quantidade_bloqueios = 1
        else:
            aluno.quantidade_bloqueios = 0
        aluno.save(update_fields=['quantidade_bloqueios'])


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
