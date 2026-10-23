from django.db import migrations, models


STATUS_PARA_INTEIRO = {
    'PENDENTE': '1',
    'ACEITA': '2',
    'RECUSADA': '3',
    'CANCELADA': '4',
}


def converter_status_para_inteiro(apps, schema_editor):
    for nome_modelo in (
        'SolicitacaoTrocaTitular',
        'HistoricalSolicitacaoTrocaTitular',
    ):
        modelo = apps.get_model('emprestimos', nome_modelo)
        for status_textual, status_numerico in STATUS_PARA_INTEIRO.items():
            modelo.objects.filter(status=status_textual).update(status=status_numerico)


def converter_status_para_texto(apps, schema_editor):
    for nome_modelo in (
        'SolicitacaoTrocaTitular',
        'HistoricalSolicitacaoTrocaTitular',
    ):
        modelo = apps.get_model('emprestimos', nome_modelo)
        for status_textual, status_numerico in STATUS_PARA_INTEIRO.items():
            modelo.objects.filter(status=status_numerico).update(status=status_textual)


class Migration(migrations.Migration):

    dependencies = [
        ('emprestimos', '0003_historicalsolicitacaotrocatitular_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='solicitacaotrocatitular',
            name='soltroca_pendente_unica_emprestimo',
        ),
        migrations.RunPython(
            converter_status_para_inteiro,
            converter_status_para_texto,
        ),
        migrations.AlterField(
            model_name='historicalsolicitacaotrocatitular',
            name='status',
            field=models.IntegerField(
                choices=[
                    (1, 'Pendente'),
                    (2, 'Aceita'),
                    (3, 'Recusada'),
                    (4, 'Cancelada'),
                ],
                default=1,
                verbose_name='Status',
            ),
        ),
        migrations.AlterField(
            model_name='solicitacaotrocatitular',
            name='status',
            field=models.IntegerField(
                choices=[
                    (1, 'Pendente'),
                    (2, 'Aceita'),
                    (3, 'Recusada'),
                    (4, 'Cancelada'),
                ],
                default=1,
                verbose_name='Status',
            ),
        ),
        migrations.AddConstraint(
            model_name='solicitacaotrocatitular',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 1)),
                fields=('emprestimo',),
                name='soltroca_pendente_unica_emprestimo',
            ),
        ),
    ]
