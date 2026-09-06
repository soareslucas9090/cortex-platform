from django.db import migrations, models
import django.db.models.deletion


def migrar_strike_para_aluno(apps, schema_editor):
    Justificativa = apps.get_model('justificativas', 'Justificativa')
    Strike = apps.get_model('strikes', 'Strike')

    for justificativa in Justificativa.objects.exclude(strike_id=None).iterator():
        strike = Strike.objects.select_related('ticket').get(pk=justificativa.strike_id)
        justificativa.aluno_id = strike.ticket.aluno_id
        justificativa.save(update_fields=['aluno_id'])
        justificativa.strikes_cobertos.add(strike)


class Migration(migrations.Migration):

    dependencies = [
        ('alunos', '0004_aluno_faltas_is_bloqueado'),
        ('justificativas', '0002_initial'),
        ('strikes', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaljustificativa',
            name='aluno',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='alunos.aluno',
                verbose_name='Aluno',
            ),
        ),
        migrations.AddField(
            model_name='justificativa',
            name='aluno',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='justificativas_transporte',
                to='alunos.aluno',
                verbose_name='Aluno',
            ),
        ),
        migrations.AddField(
            model_name='justificativa',
            name='strikes_cobertos',
            field=models.ManyToManyField(
                related_name='justificativas',
                to='strikes.strike',
                verbose_name='Strikes cobertos',
            ),
        ),
        migrations.RunPython(migrar_strike_para_aluno, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='historicaljustificativa',
            name='strike',
        ),
        migrations.RemoveField(
            model_name='justificativa',
            name='strike',
        ),
        migrations.AlterField(
            model_name='justificativa',
            name='aluno',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='justificativas_transporte',
                to='alunos.aluno',
                verbose_name='Aluno',
            ),
        ),
    ]
