from Academico.alunos.choices import SituacaoAluno
from Academico.cursos.choices import NivelEnsino

PAPEIS_ESCOPO_GLOBAL = (
    'Diretor(a) de Ensino',
    'Chefe de Departamento de Ensino Técnico',
    'Chefe de Departamento de Apoio ao Ensino',
    'Coordenador(a) de Disciplina',
    'Coordenador(a) das Áreas de Natureza, Humanas e Letras',
)


def usuario_e_l3(usuario) -> bool:
    if not usuario or not getattr(usuario, 'is_authenticated', False):
        return False
    return bool(usuario.is_staff or usuario.is_admin or usuario.is_superuser)


def usuario_tem_escopo_global(usuario) -> bool:
    from Organizacional.vinculos.models import SetorVinculo

    if usuario_e_l3(usuario):
        return True
    return SetorVinculo.objects.filter(
        usuario=usuario,
        responsavel=True,
        setor__ativo=True,
        funcao__ativo=True,
        funcao__papel_funcao__in=PAPEIS_ESCOPO_GLOBAL,
    ).exists()


def curso_ids_sob_coordenacao(usuario):
    """Cursos cujo setor tem o usuário como responsável."""
    from Academico.cursos.models import Curso
    from Organizacional.vinculos.models import SetorVinculo

    if not usuario or not getattr(usuario, 'is_authenticated', False):
        return Curso.objects.none()
    setor_ids = SetorVinculo.objects.filter(
        usuario=usuario,
        responsavel=True,
        setor__ativo=True,
        funcao__ativo=True,
    ).values_list('setor_id', flat=True)
    return Curso.objects.filter(setor_id__in=setor_ids)


def vinculos_elegiveis():
    from Academico.aluno_cursos.models import AlunoCurso

    return AlunoCurso.objects.filter(
        ativo=True,
        aluno__ativo=True,
        aluno__usuario__ativo=True,
        aluno__situacao=SituacaoAluno.MATRICULADO,
        curso__ativo=True,
        curso__nivel_ensino=NivelEnsino.ENSINO_MEDIO,
    )


def vinculos_no_escopo(usuario):
    qs = vinculos_elegiveis()
    if usuario_tem_escopo_global(usuario):
        return qs
    return qs.filter(curso_id__in=curso_ids_sob_coordenacao(usuario))
