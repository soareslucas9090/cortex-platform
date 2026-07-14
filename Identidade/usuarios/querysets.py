from .models import Usuario


def queryset_usuario_com_perfis():
    """
    Queryset base para serialização de perfis relacionados sem N+1.
    Integração Identidade ↔ PessoasInstitucionais/Acadêmico/Organizacional via reverse relations.
    """
    return Usuario.objects.select_related(
        'servidor__cargo',
        'terceirizado__cargo',
        'terceirizado__empresa_instituicao',
        'aluno',
    ).prefetch_related(
        'setor_vinculos__setor',
        'setor_vinculos__funcao',
    )
