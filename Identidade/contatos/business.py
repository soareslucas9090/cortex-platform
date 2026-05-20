import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class ContatoBusiness(ModelInstanceBusiness):
    """
    Camada de negócio do domínio Contatos.
    Orquestra operações sobre o model Contato.
    """

    def atualizar_contato(self, dados: dict):
        """Atualiza os dados de um contato existente."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar contato: %s', e)
            raise SystemErrorException('Não foi possível atualizar o contato.')
