import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class SalaBusiness(ModelInstanceBusiness):

    def criar_sala(self, bloco_id: int, nome: str, **kwargs):
        """Cria uma nova sala vinculada a um bloco."""
        try:
            from .models import Sala
            return Sala.objects.create(bloco_id=bloco_id, nome=nome, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a sala.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da sala."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a sala.', logger)

    def desativar(self):
        """Desativa a sala."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar a sala.', logger)

    def reativar(self):
        """Reativa a sala."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar a sala.', logger)


class SalaSetorBusiness(ModelInstanceBusiness):

    def criar_vinculo(self, sala_id: int, setor_id: int):
        """Cria vínculo entre sala e setor."""
        try:
            from .models import SalaSetor
            self.object_instance.rules.validar_vinculo_unico(sala_id, setor_id)
            return SalaSetor.objects.create(sala_id=sala_id, setor_id=setor_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o vínculo sala–setor.', logger)

    def remover_vinculo(self):
        """Remove o vínculo sala–setor."""
        try:
            self.object_instance.delete()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível remover o vínculo sala–setor.', logger)
