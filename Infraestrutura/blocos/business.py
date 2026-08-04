import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class BlocoBusiness(ModelInstanceBusiness):

    def criar_bloco(self, nome: str, **kwargs):
        """Cria um novo bloco."""
        try:
            from .models import Bloco
            return Bloco.objects.create(nome=nome, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o bloco.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do bloco."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o bloco.', logger)

    def desativar(self):
        """Desativa o bloco."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o bloco.', logger)

    def reativar(self):
        """Reativa o bloco."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o bloco.', logger)
