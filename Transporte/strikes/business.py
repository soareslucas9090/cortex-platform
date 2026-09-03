import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class StrikeBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario):
        try:
            return self.object_instance.helper.listar_para_usuario(usuario)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os strikes.', logger)

    def criar_para_ticket(self, ticket):
        try:
            from .helpers import sincronizar_faltas_transporte
            from .models import Strike

            strike, _ = Strike.objects.get_or_create(ticket=ticket)
            sincronizar_faltas_transporte(ticket.aluno)
            return strike
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o strike.', logger)
