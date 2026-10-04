from django.db import migrations, models


def identificar_guaritas_existentes(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(
        usuario_coletivo=True,
        cargos_coletivo__nome__iexact='VIGILANTE',
    ).update(tipo_conta_coletiva='guarita')


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalusuario',
            name='tipo_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita')],
                help_text='Finalidade da conta compartilhada. Ex.: guarita.',
                max_length=30,
                null=True,
                verbose_name='Tipo de conta coletiva',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='tipo_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita')],
                help_text='Finalidade da conta compartilhada. Ex.: guarita.',
                max_length=30,
                null=True,
                verbose_name='Tipo de conta coletiva',
            ),
        ),
        migrations.RunPython(identificar_guaritas_existentes, migrations.RunPython.noop),
    ]
