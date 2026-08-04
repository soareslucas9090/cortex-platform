import logging

from AppCore.core.business.business import ModelInstanceBusiness
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
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o contato.', logger)
