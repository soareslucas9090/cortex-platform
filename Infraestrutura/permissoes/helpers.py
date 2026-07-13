from django.apps import apps

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import CAPACIDADES_INFRAESTRUTURA, capacidades_infraestrutura_vazias


class PermissaoFuncaoInfraestruturaHelpers(ModelInstanceHelpers):

    def obter_capacidades(self) -> dict:
        """Retorna as capacidades configuradas para a função."""
        permissao = self.object_instance
        return {
            capacidade: getattr(permissao, capacidade)
            for capacidade in CAPACIDADES_INFRAESTRUTURA
        }


class PermissaoInfraestruturaUsuarioHelpers(ModelInstanceHelpers):
    """Compilação de capacidades do usuário a partir dos vínculos ativos."""

    def compilar_do_usuario(self, usuario) -> dict:
        """
        União (OR) das capacidades das funções dos vínculos ativos do usuário.
        Considera apenas setor e função ativos.
        """
        from .models import PermissaoFuncaoInfraestrutura

        SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')

        resultado = capacidades_infraestrutura_vazias()
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

        permissoes = PermissaoFuncaoInfraestrutura.objects.filter(funcao_id__in=funcao_ids).values(
            *CAPACIDADES_INFRAESTRUTURA,
        )
        for permissao in permissoes:
            for capacidade in CAPACIDADES_INFRAESTRUTURA:
                resultado[capacidade] = resultado[capacidade] or permissao[capacidade]

        return resultado
