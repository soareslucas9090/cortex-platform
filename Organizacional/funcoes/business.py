import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import FuncaoRules

logger = logging.getLogger(__name__)


class FuncaoBusiness(ModelInstanceBusiness):

    def criar_funcao(
        self,
        papel_funcao: str,
        descricao: str,
        categoria: str,
        e_gratificada: bool = False,
        exige_aluno: bool = False,
        **kwargs,
    ):
        """Cria uma nova função validando unicidade de papel/função."""
        from .models import Funcao
        regras = FuncaoRules()
        regras.papel_funcao_unico(papel_funcao)
        try:
            return Funcao.objects.create(
                papel_funcao=papel_funcao,
                categoria=categoria,
                descricao=descricao,
                e_gratificada=e_gratificada,
                exige_aluno=exige_aluno,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar função: %s', e)
            raise SystemErrorException('Não foi possível criar a função.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da função. Revalida papel_função se estiver nos dados."""
        if 'papel_funcao' in dados:
            regras = FuncaoRules(object_instance=self.object_instance)
            regras.papel_funcao_unico(dados['papel_funcao'], excluir_id=self.object_instance.pk)
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar função: %s', e)
            raise SystemErrorException('Não foi possível atualizar a função.')

    def desativar(self):
        """Desativa a função. Bloqueado se estiver em uso em vínculos."""
        regras = FuncaoRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar função: %s', e)
            raise SystemErrorException('Não foi possível desativar a função.')

    def reativar(self):
        """Reativa a função."""
        regras = FuncaoRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar função: %s', e)
            raise SystemErrorException('Não foi possível reativar a função.')
