import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import RecursoRules

logger = logging.getLogger(__name__)


class RecursoBusiness(ModelInstanceBusiness):

    def criar_recurso(
        self,
        codigo: str,
        tipo: str,
        sala_id=None,
        descricao: str = '',
        **kwargs,
    ):
        """Cria um novo recurso validando código e regras por tipo."""
        from .models import Recurso
        regras = RecursoRules()
        regras.codigo_unico(codigo)
        regras.validar_sala_por_tipo(tipo, sala_id)
        regras.validar_sala_ativa(sala_id)
        try:
            return Recurso.objects.create(
                codigo=codigo,
                tipo=tipo,
                sala_id=sala_id,
                descricao=descricao,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar recurso: %s', e)
            raise SystemErrorException('Não foi possível criar o recurso.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do recurso. Revalida código e sala por tipo."""
        tipo = dados.get('tipo', self.object_instance.tipo)
        sala = dados.get('sala', self.object_instance.sala_id)
        sala_id = sala.pk if hasattr(sala, 'pk') else sala

        regras = RecursoRules(object_instance=self.object_instance)
        if 'codigo' in dados:
            regras.codigo_unico(dados['codigo'], excluir_id=self.object_instance.pk)
        regras.validar_sala_por_tipo(tipo, sala_id)
        regras.validar_sala_ativa(sala_id)

        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar recurso: %s', e)
            raise SystemErrorException('Não foi possível atualizar o recurso.')

    def desativar(self):
        """Desativa o recurso (sem exclusão física de negócio)."""
        regras = RecursoRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar recurso: %s', e)
            raise SystemErrorException('Não foi possível desativar o recurso.')

    def reativar(self):
        """Reativa o recurso."""
        regras = RecursoRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar recurso: %s', e)
            raise SystemErrorException('Não foi possível reativar o recurso.')
