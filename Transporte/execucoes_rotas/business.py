import logging
from datetime import datetime

from django.db import IntegrityError
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from .rules import MENSAGEM_EXECUCAO_DUPLICADA

logger = logging.getLogger(__name__)


class ExecucaoRotaBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario, status_param=None, data_param=None):
        try:
            return self.object_instance.helper.listar_para_usuario(
                usuario,
                status_param,
                data_param,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as execuções de rota.', logger)

    def obter_resumo_vagas(self):
        try:
            ocupadas = self.object_instance.helper.contar_vagas_ocupadas()
            return {
                'vagas_ocupadas': ocupadas,
                'vagas_disponiveis': max(self.object_instance.quantidade_vagas - ocupadas, 0),
            }
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível calcular as vagas da execução.', logger)

    def criar_execucao(self, rota_id, data_execucao):
        try:
            from Transporte.rotas.models import Rota

            from .models import ExecucaoRota

            rota = Rota.objects.select_related('percurso').get(pk=rota_id)
            rules = self.object_instance.rules
            rules.validar_rota_ativa(rota)
            rules.validar_dia_da_rota(rota, data_execucao)
            rules.validar_execucao_unica(
                self.object_instance.helper.existe_para_rota_na_data(rota_id, data_execucao),
            )
            data_hora_saida = timezone.make_aware(
                datetime.combine(data_execucao, rota.horario_saida),
                timezone.get_current_timezone(),
            )
            return ExecucaoRota.objects.create(
                rota=rota,
                data_execucao=data_execucao,
                data_hora_saida=data_hora_saida,
                quantidade_vagas=rota.quantidade_vagas,
            )
        except IntegrityError:
            raise BusinessRuleException(MENSAGEM_EXECUCAO_DUPLICADA)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a execução da rota.', logger)

    def obter_por_id(self, execucao_id, bloquear=False):
        try:
            return self.object_instance.helper.obter_por_id(execucao_id, bloquear)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a execução da rota.', logger)

    def alterar_status(self, novo_status):
        try:
            execucao = self.object_instance.helper.obter_por_id(
                self.object_instance.pk,
                bloquear=True,
            )
            return execucao.state.atualizar_status(novo_status)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível alterar o status da execução.', logger)
