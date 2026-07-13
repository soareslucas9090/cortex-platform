import logging

from django.apps import apps

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import PermissaoFuncaoInfraestruturaRules

logger = logging.getLogger(__name__)


class PermissaoFuncaoInfraestruturaBusiness(ModelInstanceBusiness):

    def criar_permissao(self, funcao_id: int, **capacidades):
        """Cria permissões de Infraestrutura para uma função."""
        from .models import PermissaoFuncaoInfraestrutura

        Funcao = apps.get_model('funcoes', 'Funcao')
        funcao = Funcao.objects.get(pk=funcao_id)
        regras = PermissaoFuncaoInfraestruturaRules()
        regras.funcao_deve_estar_ativa(funcao)
        regras.funcao_sem_permissao_existente(funcao_id)
        try:
            return PermissaoFuncaoInfraestrutura.objects.create(
                funcao=funcao,
                **capacidades,
            )
        except Exception as e:
            logger.exception('Erro ao criar permissão de Infraestrutura: %s', e)
            raise SystemErrorException('Não foi possível criar a permissão de Infraestrutura.')

    def atualizar_capacidades(self, dados: dict):
        """Atualiza as capacidades configuradas para a função."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar permissão de Infraestrutura: %s', e)
            raise SystemErrorException('Não foi possível atualizar a permissão de Infraestrutura.')
