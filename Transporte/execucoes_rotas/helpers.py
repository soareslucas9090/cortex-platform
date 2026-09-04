from datetime import date, timedelta

from django.utils.timezone import localdate, now

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import StatusExecucaoRota
from .rules import execucao_elegivel_para_iniciar_monitoramento

STATUSES_LISTAGEM_CONFERENCIA = (
    StatusExecucaoRota.ABERTA,
    StatusExecucaoRota.FECHADA,
    StatusExecucaoRota.EM_EMBARQUE,
    StatusExecucaoRota.FINALIZADA,
)


class ExecucaoRotaHelpers(ModelInstanceHelpers):

    def listar_para_usuario(self, usuario, status_param=None, data_param=None):
        from .models import ExecucaoRota

        if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            queryset = ExecucaoRota.objects.select_related('rota', 'rota__percurso')
        else:
            queryset = self._listar_disponiveis_para_aluno()

        if (
            status_param
            and status_param.isdigit()
            and int(status_param) in StatusExecucaoRota.values
        ):
            queryset = queryset.filter(status=int(status_param))
        if data_param:
            try:
                data_valida = date.fromisoformat(data_param)
            except ValueError:
                data_valida = None
            if data_valida:
                queryset = queryset.filter(data_execucao=data_valida)
        return queryset

    def obter_por_id(self, execucao_id, bloquear=False):
        from .models import ExecucaoRota

        queryset = ExecucaoRota.objects.select_related('rota', 'rota__percurso')
        if bloquear:
            queryset = queryset.select_for_update()
        return queryset.get(pk=execucao_id)

    def existe_para_rota_na_data(self, rota_id, data_execucao) -> bool:
        from .models import ExecucaoRota

        return ExecucaoRota.objects.filter(
            rota_id=rota_id,
            data_execucao=data_execucao,
        ).exists()

    def _listar_disponiveis_para_aluno(self):
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

        execucao = self.object_instance
        if execucao.chamada_tickets_concluida:
            ocupadas = execucao.tickets.filter(status=StatusTicket.EMBARCADO).count()
            ocupadas += execucao.entradas_sem_ticket.count()
            return ocupadas
        return execucao.tickets.filter(
            status__in=(StatusTicket.RESERVADO, StatusTicket.EMBARCADO),
        ).count()

    def quantidade_vagas_disponiveis(self):
        return max(
            self.object_instance.quantidade_vagas - self.contar_vagas_ocupadas(),
            0,
        )

    def pode_monitorar(self) -> bool:
        return execucao_elegivel_para_iniciar_monitoramento(self.object_instance)

    def listar_para_conferencia(self, data_param=None):
        from .models import ExecucaoRota

        data_hoje = localdate()
        queryset = ExecucaoRota.objects.select_related('rota', 'rota__percurso').filter(
            data_execucao=data_hoje,
            status__in=STATUSES_LISTAGEM_CONFERENCIA,
        )
        if data_param:
            try:
                data_valida = date.fromisoformat(data_param)
            except ValueError:
                data_valida = None
            if data_valida and data_valida != data_hoje:
                return queryset.none()
        return queryset
