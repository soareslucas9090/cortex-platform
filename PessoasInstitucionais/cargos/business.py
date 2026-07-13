import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class CargoBusiness(ModelInstanceBusiness):

    def criar_cargo(self, nome: str, **kwargs):
        """Cria um novo cargo validando unicidade do nome."""
        from .models import Cargo
        self.object_instance.rules.nome_unico(nome)
        try:
            return Cargo.objects.create(nome=nome, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar cargo: %s', e)
            raise SystemErrorException('Não foi possível criar o cargo.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do cargo. Revalida nome se estiver nos dados."""
        if 'nome' in dados:
            self.object_instance.rules.nome_unico(
                dados['nome'],
                excluir_id=self.object_instance.pk,
            )
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar cargo: %s', e)
            raise SystemErrorException('Não foi possível atualizar o cargo.')

    def desativar(self):
        """Desativa o cargo."""
        self.object_instance.rules.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar cargo: %s', e)
            raise SystemErrorException('Não foi possível desativar o cargo.')

    def reativar(self):
        """Reativa o cargo."""
        self.object_instance.rules.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar cargo: %s', e)
            raise SystemErrorException('Não foi possível reativar o cargo.')
