import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException
from Transporte.strikes.choices import StatusStrike

from .choices import StatusJustificativa

logger = logging.getLogger(__name__)


class JustificativaBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario):
        try:
            queryset = self.object_instance.helper.listar_com_relacionamentos()
            if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
                return queryset
            aluno = getattr(usuario, 'aluno', None)
            return queryset.filter(strike__ticket__aluno=aluno) if aluno is not None else queryset.none()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as justificativas.', logger)

    def obter_por_id(self, justificativa_id):
        try:
            from .models import Justificativa

            return Justificativa.objects.select_related(
                'strike',
                'strike__ticket',
                'strike__ticket__execucao_rota',
                'strike__ticket__execucao_rota__rota',
                'strike__ticket__execucao_rota__rota__percurso',
                'strike__ticket__aluno',
                'strike__ticket__aluno__usuario',
                'analisada_por',
            ).get(pk=justificativa_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a justificativa.', logger)

    def criar_justificativa(self, strike_id, texto, usuario):
        try:
            from Transporte.strikes.models import Strike

            from .models import Justificativa

            with transaction.atomic():
                strike = Strike.objects.select_for_update().select_related(
                    'ticket',
                    'ticket__aluno',
                    'ticket__aluno__usuario',
                ).get(pk=strike_id)
                strike.rules.validar_dono(usuario)
                strike.rules.validar_ativo()
                self.object_instance.rules.validar_texto(texto)
                return Justificativa.objects.create(strike=strike, texto=texto.strip())
        except IntegrityError:
            raise BusinessRuleException('Este strike já possui uma justificativa.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível enviar a justificativa.', logger)

    def analisar(self, aprovar, usuario, observacao_analise=''):
        try:
            from Transporte.strikes.models import Strike

            from .models import Justificativa

            with transaction.atomic():
                justificativa = Justificativa.objects.select_for_update().select_related(
                    'strike',
                    'strike__ticket',
                    'strike__ticket__aluno',
                    'strike__ticket__aluno__usuario',
                ).get(pk=self.object_instance.pk)
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
                    strike = Strike.objects.select_for_update().get(pk=justificativa.strike_id)
                    strike.status = StatusStrike.JUSTIFICADO
                    strike.save(update_fields=['status', 'updated_at'])
                return justificativa
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível analisar a justificativa.', logger)
