from django.db import migrations


MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR = {
    '14LBIO': 'CCLCB',
    'S.03': 'CCLCB',
    'S.04': 'CCLCB',
    '14LMAT': 'CCLM',
    'S.05': 'CCLM',
    '14PMAT': 'PROFMAT',
    '14MTDS': 'CCTDS',
    '14MEDF': 'CCEDI',
    '14IEDF': 'CCEDI',
    '14MELM': 'COCTECEL',
    '14IELM': 'COCTECEL',
    '14IAMB': 'CTEMEAM',
    'MEAB': 'CTEMEAM',
    '14JAMB': 'COTMEAMBPR',
    '14TADS': 'CCADS',
    '14IADM': 'COCURADM',
    'TEAD': 'COCURADM',
    '14BECV': 'COCENGCIV',
    '14EECB': 'ECIENCBIO',
    '14MINF': 'CCTI',
    '14IINF': 'CCTI',
    'IPINT': 'CCTI',
    'B.67': 'CCTI',
    'B.61': 'DEPENTE',
    'B.62': 'DEPENTE',
    'LOGI': 'DEPENTE',
    'SECR': 'DEPENTE',
    'TPF': 'DEPENTE',
    '14FAID': 'DEPENTE',
    '14FLIB': 'DEPENTE',
    '14FINB': 'DEPENTE',
    '14FSER': 'DEPENTE',
    '14ASER': 'DEPENTE',
    '14FMB': 'DEPENTE',
    '14JOPC': 'DEPENTE',
    '14FRT': 'DEPENTE',
    'S.52': 'DEPENSU',
    'S.53': 'DEPENSU',
    'S.54': 'DEPENSU',
    'S.55': 'DEPENSU',
    '14PIFPI': 'DENS',
}


def associar_setores_aos_cursos(apps, schema_editor):
    Curso = apps.get_model('cursos', 'Curso')
    Setor = apps.get_model('setores', 'Setor')

    siglas = set(MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR.values())
    setores_por_sigla = {setor.sigla: setor for setor in Setor.objects.filter(sigla__in=siglas)}

    siglas_ausentes = sorted(siglas - set(setores_por_sigla.keys()))
    if siglas_ausentes:
        raise RuntimeError(
            'Não foi possível associar setores aos cursos: siglas ausentes no banco: '
            + ', '.join(siglas_ausentes)
        )

    for codigo_curso, sigla in MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR.items():
        Curso.objects.filter(codigo_curso=codigo_curso).update(setor=setores_por_sigla[sigla])


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0003_curso_setor'),
        ('setores', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(associar_setores_aos_cursos, reverse_code=migrations.RunPython.noop),
    ]
