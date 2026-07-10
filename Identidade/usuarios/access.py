from .choices import (
    NIVEL_CORTEX,
    PERMISSAO_CORTEX_EDITAR_EU,
    PERMISSAO_CORTEX_LER_TUDO,
)


def nivel_cortex(user) -> str:
    if not user or not getattr(user, 'is_authenticated', False):
        return PERMISSAO_CORTEX_EDITAR_EU
    return user.permissoes.get('cortex', PERMISSAO_CORTEX_EDITAR_EU)


def tem_nivel_cortex_minimo(user, minimo: str) -> bool:
    return NIVEL_CORTEX.get(nivel_cortex(user), 1) >= NIVEL_CORTEX.get(minimo, 1)


def escopar_queryset_cortex(user, qs, *, campo_dono, leitura_ampla_minimo=PERMISSAO_CORTEX_LER_TUDO):
    """
    Restringe queryset conforme nível Cortex.
    - L2+ (leitura_ampla_minimo): retorna qs sem filtro por dono.
    - L1: filtra por campo_dono=request.user; se campo_dono é None, retorna vazio.
    """
    if tem_nivel_cortex_minimo(user, leitura_ampla_minimo):
        return qs
    if campo_dono is None:
        return qs.none()
    valor = user.pk if campo_dono == 'id' else user
    return qs.filter(**{campo_dono: valor})
