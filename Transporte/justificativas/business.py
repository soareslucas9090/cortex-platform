import logging

from django.db import IntegrityError
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import AuthorizationException, BusinessRuleException
from Transporte.strikes.choices import StatusStrike
from Transporte.strikes.helpers import sincronizar_faltas_transporte

from .choices import StatusJustificativa

logger = logging.getLogger(__name__)


class JustificativaBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario):
        try:
            return self.object_instance.helper.listar_para_usuario(usuario)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as justificativas.', logger)

    def obter_por_id(self, justificativa_id):
        try:
            return self.object_instance.helper.obter_por_id(justificativa_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a justificativa.', logger)

    def criar_justificativa(self, usuario, texto):
        try:
            from Transporte.strikes.models import Strike

            from .models import Justificativa

            aluno = getattr(usuario, 'aluno', None)
            if aluno is None:
                raise AuthorizationException('Somente um aluno pode enviar justificativa.')

            self.object_instance.rules.validar_aluno_bloqueado(aluno)
            self.object_instance.rules.validar_sem_pendente(aluno)
            self.object_instance.rules.validar_texto(texto)

            strikes_ativos = list(
                Strike.objects.select_for_update().filter(
                    ticket__aluno=aluno,
                    status=StatusStrike.ATIVO,
                ),
            )
            if not strikes_ativos:
                raise BusinessRuleException('Não há strikes ativos para justificar.')

            justificativa = Justificativa.objects.create(
                aluno=aluno,
                texto=texto.strip(),
            )
            justificativa.strikes_cobertos.set(strikes_ativos)
            return justificativa
        except IntegrityError:
            raise BusinessRuleException('Já existe uma justificativa pendente de análise.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível enviar a justificativa.', logger)

    def analisar(self, aprovar, usuario, observacao_analise=''):
        try:
            from Transporte.strikes.models import Strike

            from .models import Justificativa

            justificativa = Justificativa.objects.select_for_update().select_related(
                'aluno',
                'aluno__usuario',
            ).prefetch_related('strikes_cobertos').get(pk=self.object_instance.pk)
            justificativa.rules.validar_pendente()
            justificativa.status = (
                StatusJustificativa.APROVADA
                if aprovar
                else StatusJustificativa.REJEITADA
            )
            justificativa.observacao_analise = observacao_analise.strip()
            justificativa.analisada_por = usuario
            justificativa.analisada_em = timezone.now()
            justificativa.save(update_fields=[
                'status',
                'observacao_analise',
                'analisada_por',
                'analisada_em',
                'updated_at',
            ])
            if aprovar:
                strikes = Strike.objects.select_for_update().filter(
                    pk__in=justificativa.strikes_cobertos.values_list('pk', flat=True),
                )
                for strike in strikes:
                    strike.status = StatusStrike.JUSTIFICADO
                    strike.save(update_fields=['status', 'updated_at'])
                sincronizar_faltas_transporte(justificativa.aluno)
            return justificativa
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível analisar a justificativa.', logger)
