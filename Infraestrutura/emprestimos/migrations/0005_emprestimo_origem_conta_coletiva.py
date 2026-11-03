from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('emprestimos', '0004_converter_status_solicitacao_troca_para_inteiro')]

    operations = [
        migrations.AddField(
            model_name='historicalemprestimo',
            name='origem_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita'), ('codis', 'CODIS')],
                db_index=True,
                editable=False,
                help_text=('Tipo da conta coletiva que realizou a operação, congelado na criação.'),
                max_length=30,
                null=True,
                verbose_name='Origem da conta coletiva',
            ),
        ),
        migrations.AddField(
            model_name='emprestimo',
            name='origem_conta_coletiva',
            field=models.CharField(
                blank=True,
                choices=[('guarita', 'Guarita'), ('codis', 'CODIS')],
                db_index=True,
                editable=False,
                help_text=('Tipo da conta coletiva que realizou a operação, congelado na criação.'),
                max_length=30,
                null=True,
                verbose_name='Origem da conta coletiva',
            ),
        ),
    ]
