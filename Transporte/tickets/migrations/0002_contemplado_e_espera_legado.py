from django.db import migrations

STATUS_NAO_CONTEMPLADO_LEGADO = 6
STATUS_EM_ESPERA = 2


def migrar_nao_contemplado_para_espera(apps, schema_editor):
    Ticket = apps.get_model('tickets', 'Ticket')
    HistoricalTicket = apps.get_model('tickets', 'HistoricalTicket')
    Ticket.objects.filter(status=STATUS_NAO_CONTEMPLADO_LEGADO).update(
        status=STATUS_EM_ESPERA,
    )
    HistoricalTicket.objects.filter(status=STATUS_NAO_CONTEMPLADO_LEGADO).update(
        status=STATUS_EM_ESPERA,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            migrar_nao_contemplado_para_espera,
            migrations.RunPython.noop,
        ),
    ]
