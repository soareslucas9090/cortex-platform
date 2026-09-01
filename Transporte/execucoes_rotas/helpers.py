from datetime import timedelta

from django.utils.timezone import localdate, now

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import StatusExecucaoRota


class ExecucaoRotaHelpers(ModelInstanceHelpers):

    def existe_para_rota_na_data(self, rota_id, data_execucao) -> bool:
        from .models import ExecucaoRota

        return ExecucaoRota.objects.filter(
            rota_id=rota_id,
            data_execucao=data_execucao,
        ).exists()

    def listar_disponiveis_para_aluno(self):
        from .models import ExecucaoRota

        agora = now()
        data_local = localdate(agora)
        queryset = ExecucaoRota.objects.filter(
            status=StatusExecucaoRota.ABERTA,
            data_execucao=data_local,
            data_hora_saida__gte=agora + timedelta(minutes=30),
        ).select_related('rota', 'rota__percurso')
        if data_local.weekday() >= 5:
            return queryset.none()
        return queryset

    def contar_vagas_ocupadas(self):
        from Transporte.tickets.choices import StatusTicket

        return self.object_instance.tickets.filter(
            status__in=(StatusTicket.RESERVADO, StatusTicket.EMBARCADO),
        ).count()

    def quantidade_vagas_disponiveis(self):
        return max(
            self.object_instance.quantidade_vagas - self.contar_vagas_ocupadas(),
            0,
        )
