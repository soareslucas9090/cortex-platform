from datetime import date, datetime, timedelta

from django.db.models import Count, Prefetch, Q

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

    def listar_historico(self, filtros=None):
        from Transporte.tickets.choices import StatusTicket
        from .models import ExecucaoRota

        filtros = filtros or {}
        queryset = (
            ExecucaoRota.objects.select_related('rota__percurso', 'rota_iniciada_por')
            .filter(status=StatusExecucaoRota.FINALIZADA, rota_finalizada_em__isnull=False)
            .annotate(
                presentes=Count('tickets', filter=Q(tickets__status=StatusTicket.EMBARCADO), distinct=True),
                ausentes=Count('tickets', filter=Q(tickets__status=StatusTicket.AUSENTE), distinct=True),
                sem_ticket=Count('entradas_sem_ticket', distinct=True),
            )
        )
        percurso_id = str(filtros.get('percurso_id', ''))
        if percurso_id.isascii() and percurso_id.isdigit() and len(percurso_id) <= 18:
            queryset = queryset.filter(rota__percurso_id=int(percurso_id))
        data_filtro = filtros.get('data')
        if data_filtro:
            try:
                data_valida = date.fromisoformat(data_filtro)
            except (TypeError, ValueError):
                pass
            else:
                queryset = queryset.filter(data_execucao=data_valida)
        busca = str(filtros.get('busca') or '').strip()
        if busca:
            condicao = Q(rota__percurso__apelido__unaccent__icontains=busca) | Q(
                rota__percurso__descricao__unaccent__icontains=busca,
            )
            for formato in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    data_busca = datetime.strptime(busca, formato).date()
                except ValueError:
                    continue
                condicao |= Q(data_execucao=data_busca)
                break
            queryset = queryset.filter(condicao)
        ordenacao = filtros.get('ordenacao', '-data')
        campos = {
            'data': ('data_execucao', 'data_hora_saida', 'pk'),
            '-data': ('-data_execucao', '-data_hora_saida', '-pk'),
            'horario': ('data_hora_saida__time', '-data_execucao', 'pk'),
            '-horario': ('-data_hora_saida__time', '-data_execucao', '-pk'),
            'percurso': ('rota__percurso__apelido', '-data_execucao', 'pk'),
            '-percurso': ('-rota__percurso__apelido', '-data_execucao', '-pk'),
        }
        return queryset.order_by(*campos.get(ordenacao, campos['-data']))

    def listar_percursos_historico(self):
        from Transporte.percursos.models import Percurso
        from .models import ExecucaoRota

        percursos = ExecucaoRota.objects.filter(
            status=StatusExecucaoRota.FINALIZADA, rota_finalizada_em__isnull=False,
        ).values('rota__percurso_id')
        # Inclui cadastros desativados que possuem viagens concluídas.
        return Percurso.objects.all().filter(pk__in=percursos).order_by('apelido', 'pk')

    def detalhar_historico(self, execucao_id):
        from Transporte.entradas_sem_ticket.models import EntradaSemTicket
        from Transporte.tickets.choices import StatusTicket
        from Transporte.tickets.models import Ticket

        tickets = Ticket.objects.select_related('aluno__usuario').order_by('aluno__usuario__nome', 'pk')
        entradas = EntradaSemTicket.objects.select_related('aluno__usuario').order_by('aluno__usuario__nome', 'pk')
        return self.listar_historico().prefetch_related(
            Prefetch('tickets', queryset=tickets.filter(status=StatusTicket.EMBARCADO), to_attr='tickets_presentes'),
            Prefetch('tickets', queryset=tickets.filter(status=StatusTicket.AUSENTE), to_attr='tickets_ausentes'),
            Prefetch('entradas_sem_ticket', queryset=entradas, to_attr='passageiros_sem_ticket'),
        ).get(pk=execucao_id)

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
