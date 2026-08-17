from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0012_alter_foto_s3_charfield'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SET LOCAL lock_timeout = '2s';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name='importacaolote',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'EM_ANDAMENTO')),
                fields=('status',),
                name='usuarios_importacao_lote_unico_em_andamento',
            ),
        ),
    ]
