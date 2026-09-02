from django.apps import apps

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class PermissaoFuncaoTransporteHelpers(ModelInstanceHelpers):

    def funcao_confere(self, usuario) -> bool:
        from .models import PermissaoFuncaoTransporte

        SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
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
        return PermissaoFuncaoTransporte.objects.filter(
            funcao_id__in=funcao_ids,
            conferir=True,
        ).exists()

    def existe_para_funcao(self, funcao_id) -> bool:
        from .models import PermissaoFuncaoTransporte

        return PermissaoFuncaoTransporte.objects.filter(funcao_id=funcao_id).exists()

    def usuario_confere(self, usuario) -> bool:
        from .models import PermissaoUsuarioTransporte

        if PermissaoUsuarioTransporte.objects.filter(usuario=usuario, conferir=True).exists():
            return True
        return self.funcao_confere(usuario)


class PermissaoUsuarioTransporteHelpers(ModelInstanceHelpers):

    def existe_para_usuario(self, usuario_id) -> bool:
        from .models import PermissaoUsuarioTransporte

        return PermissaoUsuarioTransporte.objects.filter(usuario_id=usuario_id).exists()

    def obter_capacidades(self) -> dict:
        permissao = self.object_instance
        return {'conferir': bool(permissao.conferir)}
