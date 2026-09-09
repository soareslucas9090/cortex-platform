import logging

from django.db import IntegrityError

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)


class DiaCalendarioTransporteBusiness(ModelInstanceBusiness):

    def criar_dia(self, data, descricao, tipo, ativo=True):
        try:
            from .models import DiaCalendarioTransporte

            self.object_instance.rules.validar_dados(descricao, tipo)
            return DiaCalendarioTransporte.objects.create(
                data=data,
                descricao=str(descricao).strip(),
                tipo=tipo,
                ativo=ativo,
            )
        except IntegrityError:
            raise BusinessRuleException('Já existe uma configuração para esta data.')
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível cadastrar o dia no calendário de transporte.',
                logger,
            )

    def atualizar_dados(self, dados):
        try:
            descricao = dados.get('descricao', self.object_instance.descricao)
            tipo = dados.get('tipo', self.object_instance.tipo)
            self.object_instance.rules.validar_dados(descricao, tipo)
            for campo in ('data', 'descricao', 'tipo'):
                if campo in dados:
                    valor = dados[campo]
                    if campo == 'descricao':
                        valor = str(valor).strip()
                    setattr(self.object_instance, campo, valor)
            self.object_instance.save()
            return self.object_instance
        except IntegrityError:
            raise BusinessRuleException('Já existe uma configuração para esta data.')
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível atualizar o dia do calendário de transporte.',
                logger,
            )

    def desativar(self):
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
            return self.object_instance
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível desativar o dia do calendário de transporte.',
                logger,
            )

    def reativar(self):
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
            return self.object_instance
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível reativar o dia do calendário de transporte.',
                logger,
            )
