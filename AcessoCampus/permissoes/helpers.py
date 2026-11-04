from django.apps import apps

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import CAPACIDADES_ACESSO_CAMPUS, capacidades_acesso_campus_vazias


def _mesclar_capacidades(destino: dict, origem: dict) -> dict:
    for capacidade in CAPACIDADES_ACESSO_CAMPUS:
        destino[capacidade] = destino[capacidade] or bool(origem.get(capacidade))
    return destino


class PermissaoFuncaoAcessoCampusHelpers(ModelInstanceHelpers):

    def compilar_do_usuario(self, usuario) -> dict:
        from .models import PermissaoFuncaoAcessoCampus, PermissaoUsuarioAcessoCampus

        SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
        resultado = capacidades_acesso_campus_vazias()
        funcao_ids = (
            SetorVinculo.objects.filter(
                usuario=usuario,
                setor__ativo=True,
                funcao__isnull=False,
                funcao__ativo=True,
            )
            .values_list('funcao_id', flat=True)
            .distinct()
        )
        permissoes = PermissaoFuncaoAcessoCampus.objects.filter(funcao_id__in=funcao_ids).values(
            *CAPACIDADES_ACESSO_CAMPUS,
        )
        for permissao in permissoes:
            _mesclar_capacidades(resultado, permissao)

        permissao_usuario = (
            PermissaoUsuarioAcessoCampus.objects.filter(usuario=usuario)
            .values(*CAPACIDADES_ACESSO_CAMPUS)
            .first()
        )
        if permissao_usuario:
            _mesclar_capacidades(resultado, permissao_usuario)
        return resultado

    def existe_para_funcao(self, funcao_id) -> bool:
        from .models import PermissaoFuncaoAcessoCampus

        return PermissaoFuncaoAcessoCampus.objects.filter(funcao_id=funcao_id).exists()


class PermissaoUsuarioAcessoCampusHelpers(ModelInstanceHelpers):

    def existe_para_usuario(self, usuario_id) -> bool:
        from .models import PermissaoUsuarioAcessoCampus

        return PermissaoUsuarioAcessoCampus.objects.filter(usuario_id=usuario_id).exists()
