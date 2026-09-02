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
