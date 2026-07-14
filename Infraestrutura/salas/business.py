import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class SalaBusiness(ModelInstanceBusiness):

    def criar_sala(self, bloco_id: int, nome: str, **kwargs):
        """Cria uma nova sala vinculada a um bloco."""
        from .models import Sala
        try:
            return Sala.objects.create(bloco_id=bloco_id, nome=nome, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar sala: %s', e)
            raise SystemErrorException('Não foi possível criar a sala.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da sala."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar sala: %s', e)
            raise SystemErrorException('Não foi possível atualizar a sala.')

    def desativar(self):
        """Desativa a sala."""
        self.object_instance.rules.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar sala: %s', e)
            raise SystemErrorException('Não foi possível desativar a sala.')

    def reativar(self):
        """Reativa a sala."""
        self.object_instance.rules.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar sala: %s', e)
            raise SystemErrorException('Não foi possível reativar a sala.')


class SalaSetorBusiness(ModelInstanceBusiness):

    def criar_vinculo(self, sala_id: int, setor_id: int):
        """Cria vínculo entre sala e setor."""
        from .models import SalaSetor
        self.object_instance.rules.validar_vinculo_unico(sala_id, setor_id)
        try:
            return SalaSetor.objects.create(sala_id=sala_id, setor_id=setor_id)
        except Exception as e:
            logger.exception('Erro ao criar vínculo sala–setor: %s', e)
            raise SystemErrorException('Não foi possível criar o vínculo sala–setor.')

    def remover_vinculo(self):
        """Remove o vínculo sala–setor."""
        try:
            self.object_instance.delete()
        except Exception as e:
            logger.exception('Erro ao remover vínculo sala–setor: %s', e)
            raise SystemErrorException('Não foi possível remover o vínculo sala–setor.')
