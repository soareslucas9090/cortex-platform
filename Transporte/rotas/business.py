import logging

from django.db import IntegrityError

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from .rules import MENSAGEM_ROTA_DUPLICADA

logger = logging.getLogger(__name__)


class RotaBusiness(ModelInstanceBusiness):

    def criar_rota(
        self,
        percurso_id: int,
        horario_saida,
        dia_semana: str,
        quantidade_vagas: int,
        **kwargs,
    ):
        """Cria uma nova rota vinculada a um percurso."""
        try:
            from .models import Rota
            rules = self.object_instance.rules
            rules.validar_percurso_ativo(percurso_id)
            rules.validar_dia_semana(dia_semana)
            rules.validar_quantidade_vagas(quantidade_vagas)
            rules.validar_rota_unica(percurso_id, dia_semana, horario_saida)
            return Rota.objects.create(
                percurso_id=percurso_id,
                horario_saida=horario_saida,
                dia_semana=dia_semana,
                quantidade_vagas=quantidade_vagas,
                **kwargs,
            )
        except IntegrityError:
            raise BusinessRuleException(MENSAGEM_ROTA_DUPLICADA)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a rota.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da rota e revalida regras quando necessário."""
        try:
            rota = self.object_instance
            percurso_id = dados.get('percurso_id', rota.percurso_id)
            dia_semana = dados.get('dia_semana', rota.dia_semana)
            horario_saida = dados.get('horario_saida', rota.horario_saida)
            quantidade_vagas = dados.get('quantidade_vagas', rota.quantidade_vagas)

            if 'percurso_id' in dados:
                rota.rules.validar_percurso_ativo(percurso_id)
            if 'dia_semana' in dados:
                rota.rules.validar_dia_semana(dia_semana)
            if 'quantidade_vagas' in dados:
                rota.rules.validar_quantidade_vagas(quantidade_vagas)
            if any(chave in dados for chave in ('percurso_id', 'dia_semana', 'horario_saida')):
                rota.rules.validar_rota_unica(
                    percurso_id,
                    dia_semana,
                    horario_saida,
                    excluir_id=rota.pk,
                )

            for attr, value in dados.items():
                setattr(rota, attr, value)
            rota.save()
        except IntegrityError:
            raise BusinessRuleException(MENSAGEM_ROTA_DUPLICADA)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a rota.', logger)

    def desativar(self):
        """Desativa a rota."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar a rota.', logger)

    def reativar(self):
        """Reativa a rota."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar a rota.', logger)
