from django.db import migrations, models
from django.db.models import Count


def verificar_matriculas_duplicadas(apps, schema_editor):
    Matricula = apps.get_model('matriculas', 'Matricula')
    duplicatas = (
        Matricula.objects.values('matricula')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
    )
    if duplicatas.exists():
        numeros = sorted({item['matricula'] for item in duplicatas})
        raise RuntimeError(
            'Migration abortada: existem matrículas duplicadas no banco. '
            f'Números repetidos: {", ".join(numeros)}. '
            'Resolva as duplicatas antes de aplicar esta migration.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('matriculas', '0003_alter_matricula_options'),
    ]

    operations = [
        migrations.RunPython(
            verificar_matriculas_duplicadas,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunSQL(
            sql="SET LOCAL lock_timeout = '2s';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name='matricula',
            constraint=models.UniqueConstraint(
                fields=['matricula'],
                name='matriculas_matricula_unica',
            ),
        ),
    ]
