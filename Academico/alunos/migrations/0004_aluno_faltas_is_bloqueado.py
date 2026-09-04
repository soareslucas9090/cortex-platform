from django.db import migrations, models


def sincronizar_faltas_transporte(apps, schema_editor):
    Aluno = apps.get_model('alunos', 'Aluno')
    Strike = apps.get_model('strikes', 'Strike')
    status_ativo = 1

    for aluno in Aluno.objects.all().iterator():
        faltas = Strike.objects.filter(
            ticket__aluno_id=aluno.usuario_id,
            status=status_ativo,
        ).count()
        aluno.faltas = faltas
        aluno.is_bloqueado = faltas >= 3
        aluno.save(update_fields=['faltas', 'is_bloqueado'])


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0003_alter_aluno_ira_alter_historicalaluno_ira'),
        ('strikes', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='faltas',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Quantidade de strikes ativos no transporte universitário.',
                verbose_name='Faltas de transporte',
            ),
        ),
        migrations.AddField(
            model_name='aluno',
            name='is_bloqueado',
            field=models.BooleanField(
                default=False,
                help_text='Indica bloqueio por três ou mais faltas ativas no transporte.',
                verbose_name='Bloqueado no transporte',
            ),
        ),
        migrations.AddField(
            model_name='historicalaluno',
            name='faltas',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Quantidade de strikes ativos no transporte universitário.',
                verbose_name='Faltas de transporte',
            ),
        ),
        migrations.AddField(
            model_name='historicalaluno',
            name='is_bloqueado',
            field=models.BooleanField(
                default=False,
                help_text='Indica bloqueio por três ou mais faltas ativas no transporte.',
                verbose_name='Bloqueado no transporte',
            ),
        ),
        migrations.RunPython(sincronizar_faltas_transporte, migrations.RunPython.noop),
    ]
