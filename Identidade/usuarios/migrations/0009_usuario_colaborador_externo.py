from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0008_alterar_fotos_usuario_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalusuario',
            name='colaborador_externo',
            field=models.BooleanField(
                default=False,
                help_text='Indica se o usuário é colaborador externo à instituição.',
                verbose_name='Colaborador externo',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='colaborador_externo',
            field=models.BooleanField(
                default=False,
                help_text='Indica se o usuário é colaborador externo à instituição.',
                verbose_name='Colaborador externo',
            ),
        ),
    ]
