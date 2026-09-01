import logging

from django.db import transaction

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class StrikeBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario):
        try:
            queryset = self.object_instance.helper.listar_com_relacionamentos()
            if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
                return queryset
            aluno = getattr(usuario, 'aluno', None)
            return queryset.filter(ticket__aluno=aluno) if aluno is not None else queryset.none()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os strikes.', logger)

    def criar_para_ticket(self, ticket):
        try:
            from .models import Strike

            with transaction.atomic():
                strike, _ = Strike.objects.get_or_create(ticket=ticket)
                return strike
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o strike.', logger)

    def obter_por_id(self, strike_id, bloquear=False):
        try:
            from .models import Strike

            queryset = Strike.objects.select_related(
                'ticket',
                'ticket__aluno',
                'ticket__aluno__usuario',
            )
            if bloquear:
                queryset = queryset.select_for_update()
            return queryset.get(pk=strike_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter o strike.', logger)
