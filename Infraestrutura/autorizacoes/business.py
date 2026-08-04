import logging

from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class AutorizacaoBusiness(ModelInstanceBusiness):

    def conceder_autorizacao(
        self,
        beneficiario_id: int,
        concedente,
        sala_id=None,
        recurso_id=None,
        data_inicio=None,
        data_fim=None,
        observacao: str = '',
        **kwargs,
    ):
        """Concede autorização temporária ou permanente para sala ou recurso."""
        try:
            from .models import Autorizacao
            self.object_instance.rules.pode_conceder(concedente)
            self.object_instance.rules.validar_alvo_xor(sala_id=sala_id, recurso_id=recurso_id)
            self.object_instance.rules.validar_vigencia(data_inicio, data_fim)
            self.object_instance.rules.validar_beneficiario(beneficiario_id)
            self.object_instance.rules.validar_alvo_ativo(sala_id=sala_id, recurso_id=recurso_id)
            self.object_instance.rules.validar_sem_sobreposicao(
                beneficiario_id=beneficiario_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                sala_id=sala_id,
                recurso_id=recurso_id,
            )
            return Autorizacao.objects.create(
                beneficiario_id=beneficiario_id,
                concedente=concedente,
                sala_id=sala_id,
                recurso_id=recurso_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                observacao=observacao,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível conceder a autorização.', logger)

    def revogar(self, revogador):
        """Revoga a autorização registrando data e responsável."""
        try:
            self.object_instance.rules.pode_revogar(revogador)
            self.object_instance.revogado_em = timezone.now()
            self.object_instance.revogador = revogador
            self.object_instance.save(update_fields=['revogado_em', 'revogador'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível revogar a autorização.', logger)

    def reativar(self, concedente):
        """Reativa autorização previamente revogada."""
        try:
            autorizacao = self.object_instance
            self.object_instance.rules.pode_reativar(concedente)
            self.object_instance.rules.validar_beneficiario(autorizacao.beneficiario_id)
            self.object_instance.rules.validar_alvo_ativo(
                sala_id=autorizacao.sala_id,
                recurso_id=autorizacao.recurso_id,
            )
            self.object_instance.rules.validar_sem_sobreposicao(
                beneficiario_id=autorizacao.beneficiario_id,
                data_inicio=autorizacao.data_inicio,
                data_fim=autorizacao.data_fim,
                sala_id=autorizacao.sala_id,
                recurso_id=autorizacao.recurso_id,
                excluir_id=autorizacao.pk,
            )
            self.object_instance.revogado_em = None
            self.object_instance.revogador = None
            self.object_instance.save(update_fields=['revogado_em', 'revogador'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar a autorização.', logger)
