from django.apps import apps

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import CAPACIDADES_INFRAESTRUTURA, capacidades_infraestrutura_vazias


def _mesclar_capacidades(destino: dict, origem: dict) -> dict:
    for capacidade in CAPACIDADES_INFRAESTRUTURA:
        destino[capacidade] = destino[capacidade] or bool(origem.get(capacidade))
    return destino


class PermissaoFuncaoInfraestruturaHelpers(ModelInstanceHelpers):

    def obter_capacidades(self) -> dict:
        """Retorna as capacidades configuradas para a função."""
        permissao = self.object_instance
        return {
            capacidade: getattr(permissao, capacidade)
            for capacidade in CAPACIDADES_INFRAESTRUTURA
        }

    def compilar_do_usuario(self, usuario) -> dict:
        """
        União (OR) das capacidades das funções dos vínculos ativos do usuário
        e das capacidades configuradas diretamente em PermissaoUsuarioInfraestrutura.
        Considera apenas setor e função ativos.
        """
        from .models import PermissaoFuncaoInfraestrutura, PermissaoUsuarioInfraestrutura

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
            _mesclar_capacidades(resultado, permissao)

        permissao_usuario = (
            PermissaoUsuarioInfraestrutura.objects
            .filter(usuario=usuario)
            .values(*CAPACIDADES_INFRAESTRUTURA)
            .first()
        )
        if permissao_usuario:
            _mesclar_capacidades(resultado, permissao_usuario)

        return resultado


class PermissaoUsuarioInfraestruturaHelpers(ModelInstanceHelpers):

    def obter_capacidades(self) -> dict:
        """Retorna as capacidades configuradas para o usuário."""
        permissao = self.object_instance
        return {
            capacidade: getattr(permissao, capacidade)
            for capacidade in CAPACIDADES_INFRAESTRUTURA
        }
