import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import SetorRules

logger = logging.getLogger(__name__)


class SetorBusiness(ModelInstanceBusiness):

    def criar_setor(self, nome: str, sigla: str, **kwargs):
        """Cria um novo setor validando unicidade de sigla."""
        from .models import Setor
        regras = SetorRules()
        regras.sigla_unica(sigla)
        try:
            return Setor.objects.create(nome=nome, sigla=sigla, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar setor: %s', e)
            raise SystemErrorException('Não foi possível criar o setor.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do setor. Revalida sigla se estiver nos dados."""
        if 'sigla' in dados:
            regras = SetorRules(object_instance=self.object_instance)
            regras.sigla_unica(dados['sigla'], excluir_id=self.object_instance.pk)
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar setor: %s', e)
            raise SystemErrorException('Não foi possível atualizar o setor.')

    def desativar(self):
        """Desativa o setor. Bloqueado se houver vínculos ativos."""
        regras = SetorRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar setor: %s', e)
            raise SystemErrorException('Não foi possível desativar o setor.')

    def reativar(self):
        """Reativa o setor."""
        regras = SetorRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar setor: %s', e)
            raise SystemErrorException('Não foi possível reativar o setor.')
