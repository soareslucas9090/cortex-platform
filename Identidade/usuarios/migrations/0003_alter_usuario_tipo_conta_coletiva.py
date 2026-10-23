from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_usuario_tipo_conta_coletiva'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalusuario',
            name='tipo_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita'), ('codis', 'CODIS')],
                help_text='Finalidade da conta compartilhada. Ex.: guarita ou CODIS.',
                max_length=30,
                null=True,
                verbose_name='Tipo de conta coletiva',
            ),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='tipo_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita'), ('codis', 'CODIS')],
                help_text='Finalidade da conta compartilhada. Ex.: guarita ou CODIS.',
                max_length=30,
                null=True,
                verbose_name='Tipo de conta coletiva',
            ),
        ),
    ]
