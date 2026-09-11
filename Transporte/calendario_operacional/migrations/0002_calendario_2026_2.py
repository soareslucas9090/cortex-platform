from datetime import date, timedelta

from django.db import migrations


DIAS_FIXOS = (
    (date(2026, 9, 5), 'Sábado de reposição', 'reposicao'),
    (date(2026, 9, 7), 'Independência do Brasil', 'feriado'),
    (date(2026, 9, 12), 'Sábado de reposição', 'reposicao'),
    (date(2026, 9, 19), 'Sábado letivo', 'letivo'),
    (date(2026, 9, 26), 'Sábado letivo', 'letivo'),
    (date(2026, 10, 12), 'Nossa Senhora Aparecida', 'feriado'),
    (date(2026, 10, 15), 'Dia do Professor e do Técnico Administrativo em Educação', 'ponto_facultativo'),
    (date(2026, 10, 19), 'Dia do Piauí', 'feriado'),
    (date(2026, 10, 24), 'Sábado letivo — Lançamento da SNCT 2026', 'letivo'),
    (date(2026, 10, 28), 'Dia do Servidor Público', 'ponto_facultativo'),
    (date(2026, 11, 2), 'Dia de Finados', 'feriado'),
    (date(2026, 11, 7), 'Sábado letivo', 'letivo'),
    (date(2026, 11, 14), 'Sábado letivo', 'letivo'),
    (date(2026, 11, 20), 'Dia Nacional de Zumbi e da Consciência Negra', 'feriado'),
    (date(2026, 11, 28), 'Sábado letivo — Jogos Interclasse e Intercursos', 'letivo'),
    (date(2026, 12, 5), 'Sábado letivo — Jogos Interclasse e Intercursos', 'letivo'),
    (date(2027, 1, 1), 'Confraternização Universal', 'feriado'),
)


def intervalo(inicio, fim, descricao, tipo):
    quantidade_dias = (fim - inicio).days
    return [
        (inicio + timedelta(days=indice), descricao, tipo)
        for indice in range(quantidade_dias + 1)
    ]


DIAS_CALENDARIO = (
    *DIAS_FIXOS,
    *intervalo(
        date(2026, 12, 24),
        date(2026, 12, 31),
        'Recesso de fim de ano',
        'recesso',
    ),
    *intervalo(
        date(2027, 1, 14),
        date(2027, 1, 31),
        'Férias coletivas',
        'ferias',
    ),
)


def carregar_calendario(apps, schema_editor):
    DiaCalendarioTransporte = apps.get_model(
        'calendario_operacional',
        'DiaCalendarioTransporte',
    )
    DiaCalendarioTransporte.objects.bulk_create([
        DiaCalendarioTransporte(data=data, descricao=descricao, tipo=tipo, ativo=True)
        for data, descricao, tipo in DIAS_CALENDARIO
    ])


def remover_calendario(apps, schema_editor):
    DiaCalendarioTransporte = apps.get_model(
        'calendario_operacional',
        'DiaCalendarioTransporte',
    )
    DiaCalendarioTransporte.objects.filter(
        data__in=[data for data, _descricao, _tipo in DIAS_CALENDARIO],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('calendario_operacional', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(carregar_calendario, remover_calendario),
    ]
