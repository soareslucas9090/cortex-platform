import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acesso_campus_solicitacoes', '0002_uniq_acesso_aceito_aluno_data_tipo'),
        ('acesso_campus_tipos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalsolicitacaoacesso',
            name='tipo',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='acesso_campus_tipos.tipoautorizacaoacesso',
                verbose_name='Tipo',
            ),
        ),
        migrations.AlterField(
            model_name='solicitacaoacesso',
            name='tipo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='solicitacoes_acesso',
                to='acesso_campus_tipos.tipoautorizacaoacesso',
                verbose_name='Tipo',
            ),
        ),
    ]
