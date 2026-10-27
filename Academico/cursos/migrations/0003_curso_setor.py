import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0002_initial'),
        ('setores', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='setor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos',
                to='setores.setor',
                verbose_name='Setor',
            ),
        ),
        migrations.AddField(
            model_name='historicalcurso',
            name='setor',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='setores.setor',
                verbose_name='Setor',
            ),
        ),
    ]
