import logging

from AppCore.core.business.business import ModelInstanceBusiness

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
        try:
            from .models import Recurso
            self.object_instance.rules.codigo_unico(codigo)
            self.object_instance.rules.validar_sala_por_tipo(tipo, sala_id)
            self.object_instance.rules.validar_sala_ativa(sala_id)
            return Recurso.objects.create(
                codigo=codigo,
                tipo=tipo,
                sala_id=sala_id,
                descricao=descricao,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o recurso.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do recurso. Revalida código e sala por tipo."""
        try:
            tipo = dados.get('tipo', self.object_instance.tipo)
            sala = dados.get('sala', self.object_instance.sala_id)
            sala_id = sala.pk if hasattr(sala, 'pk') else sala
            if 'codigo' in dados:
                self.object_instance.rules.codigo_unico(
                    dados['codigo'],
                    excluir_id=self.object_instance.pk,
                )
            self.object_instance.rules.validar_sala_por_tipo(tipo, sala_id)
            self.object_instance.rules.validar_sala_ativa(sala_id)
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o recurso.', logger)

    def desativar(self):
        """Desativa o recurso (sem exclusão física de negócio)."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o recurso.', logger)

    def reativar(self):
        """Reativa o recurso."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o recurso.', logger)
