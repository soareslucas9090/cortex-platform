import logging
import unicodedata

from django.db import migrations

logger = logging.getLogger(__name__)


def _normalizar_chave(valor):
    """Normaliza texto para comparação: sem acento, espaços colapsados, casefold.

    Cópia local de AppCore.common.util.util.normalizar_chave_texto: migrations não devem
    depender de código de aplicação que pode mudar depois.
    """
    texto = ' '.join(str(valor or '').split())
    sem_acento = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return sem_acento.casefold()


# Fonte: abas Curso (setor_id) e Setor (sigla) de docs/seeds/import/modelo-importacao-usuarios.ods.
MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR = {
    '14FAID': 'DEPENTE',
    '14FLIB': 'DEPENTE',
    '14FINB': 'DEPENTE',
    '14FSER': 'DEPENTE',
    'S.52': 'CCADS',
    'S.53': 'CANHL',
    'S.55': 'CCLM',
    'S.54': 'CCLM',
    '14EECB': 'ECIENCBIO',
    'S.04': 'CCLCB',
    '14LBIO': 'CCLCB',
    'S.03': 'CCLCB',
    '14LMAT': 'CCLM',
    'S.05': 'CCLM',
    '14PMAT': 'PROFMAT',
    '14MINF': 'CCTI',
    'B.61': 'DEPENTE',
    'B.62': 'DEPENTE',
    'TEAD': 'DEPENTE',
    '14MTDS': 'CCTDS',
    '14MEDF': 'CCEDI',
    '14IEDF': 'CCEDI',
    '14MELM': 'COCTECEL',
    '14IELM': 'COCTECEL',
    '14IINF': 'CCTI',
    'IPINT': 'CCTI',
    'LOGI': 'COCURADM',
    'MEAB': 'CANHL',
    '14IAMB': 'CTEMEAM',
    'B.67': 'CTI',
    'SECR': 'COCURADM',
    'TPF': 'COCURADM',
    '14TADS': 'CCADS',
    '14JAMB': 'COTMEAMBPR',
    '14FMB': 'CEXT',
    '14IADM': 'COCURADM',
    '14BECV': 'COCENGCIV',
    '14ASER': 'COCTECEL',
    '14PIFPI': 'DEPENTE',
    '14FRT': 'DEPENTE',
    # Fora do modelo atual (.ods), mas já existe em bancos implantados (seed 0001 de cursos).
    # Mantido no setor de origem para não ficar sem setor nem perder vínculos com alunos.
    '14JOPC': 'DEPENTE',
}


def associar_setores_aos_cursos(apps, schema_editor):
    """Associa setores aos cursos legados sem nunca abortar o deploy.

    Em produção os setores podem ter sido renomeados/removidos desde o seed inicial.
    Por isso, siglas ausentes são apenas registradas em log e os cursos correspondentes
    permanecem com setor NULL (o campo é nullable no banco). A regra de negócio exige o
    setor ao criar/editar o curso, então eles podem ser regularizados pela API/admin.
    A atualização só afeta cursos ainda sem setor, preservando associações já existentes.
    """
    Curso = apps.get_model('cursos', 'Curso')
    Setor = apps.get_model('setores', 'Setor')

    siglas = set(MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR.values())
    setores_por_sigla = {setor.sigla: setor for setor in Setor.objects.filter(sigla__in=siglas)}

    siglas_ausentes = sorted(siglas - set(setores_por_sigla.keys()))
    if siglas_ausentes:
        logger.warning(
            'Migration cursos.0004: siglas de setor ausentes no banco (cursos correspondentes '
            'ficam sem setor): %s',
            ', '.join(siglas_ausentes),
        )

    # Mesma chave normalizada usada pela importação de usuários (caixa, acentos e espaços).
    sigla_por_codigo_normalizado = {
        _normalizar_chave(codigo): sigla for codigo, sigla in MAPA_CODIGO_CURSO_PARA_SIGLA_SETOR.items()
    }

    for curso in Curso.objects.filter(setor__isnull=True):
        sigla = sigla_por_codigo_normalizado.get(_normalizar_chave(curso.codigo_curso))
        setor = setores_por_sigla.get(sigla) if sigla else None
        if setor is None:
            continue
        Curso.objects.filter(pk=curso.pk, setor__isnull=True).update(setor=setor)

    sem_setor = sorted(Curso.objects.filter(setor__isnull=True).values_list('codigo_curso', flat=True))
    if sem_setor:
        logger.warning(
            'Migration cursos.0004: %d curso(s) permanecem sem setor e precisam ser regularizados '
            'antes de serem editados: %s',
            len(sem_setor),
            ', '.join(sem_setor),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0003_curso_setor'),
        ('setores', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(associar_setores_aos_cursos, reverse_code=migrations.RunPython.noop),
    ]
