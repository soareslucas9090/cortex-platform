import logging

from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

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
        from .models import Autorizacao

        self.object_instance.rules.pode_conceder(concedente)
        self.object_instance.rules.validar_alvo_xor(sala_id=sala_id, recurso_id=recurso_id)
        self.object_instance.rules.validar_vigencia(data_inicio, data_fim)
        self.object_instance.rules.validar_beneficiario(beneficiario_id)
        self.object_instance.rules.validar_alvo_ativo(sala_id=sala_id, recurso_id=recurso_id)

        try:
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
            logger.exception('Erro ao conceder autorização: %s', e)
            raise SystemErrorException('Não foi possível conceder a autorização.')

    def revogar(self, revogador):
        """Revoga a autorização registrando data e responsável."""
        self.object_instance.rules.pode_revogar(revogador)
        try:
            self.object_instance.revogado_em = timezone.now()
            self.object_instance.revogador = revogador
            self.object_instance.save(update_fields=['revogado_em', 'revogador'])
        except Exception as e:
            logger.exception('Erro ao revogar autorização: %s', e)
            raise SystemErrorException('Não foi possível revogar a autorização.')
