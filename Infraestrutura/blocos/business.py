import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class BlocoBusiness(ModelInstanceBusiness):

    def criar_bloco(self, nome: str, **kwargs):
        """Cria um novo bloco."""
        from .models import Bloco
        try:
            return Bloco.objects.create(nome=nome, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar bloco: %s', e)
            raise SystemErrorException('Não foi possível criar o bloco.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do bloco."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar bloco: %s', e)
            raise SystemErrorException('Não foi possível atualizar o bloco.')

    def desativar(self):
        """Desativa o bloco."""
        self.object_instance.rules.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar bloco: %s', e)
            raise SystemErrorException('Não foi possível desativar o bloco.')

    def reativar(self):
        """Reativa o bloco."""
        self.object_instance.rules.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar bloco: %s', e)
            raise SystemErrorException('Não foi possível reativar o bloco.')
