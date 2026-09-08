from django.db.models import Count, DateField, Prefetch, Q, Value

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import DiaSemana, anotacao_ordem_dia_semana, dia_semana_da_data


class RotaHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todas as rotas ativas."""
        from .models import Rota
        return Rota.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todas as rotas inativas."""
        from .models import Rota
        return Rota.objects.filter(ativo=False)

    def listar_para_gestao(
        self,
        ativo=None,
        percurso_id=None,
        dia_semana=None,
        busca=None,
    ):
        """Retorna rotas para a gestão, aplicando apenas filtros válidos."""
        from .models import Rota

        queryset = (
            Rota.objects.select_related('percurso')
            .annotate(_ordem_dia=anotacao_ordem_dia_semana())
            .order_by('_ordem_dia', 'horario_saida', 'percurso__apelido')
        )

        if ativo is not None and str(ativo).lower() in ('true', 'false'):
            queryset = queryset.filter(ativo=str(ativo).lower() == 'true')

        if percurso_id is not None and str(percurso_id).isdigit():
            queryset = queryset.filter(percurso_id=percurso_id)

        if dia_semana in DiaSemana.values:
            queryset = queryset.filter(dia_semana=dia_semana)

        if busca:
            queryset = queryset.filter(Q(percurso__apelido__unaccent__icontains=busca))

        return queryset

    def obter_com_percurso(self, rota_id):
        """Obtém uma rota com o percurso carregado para serialização."""
        from .models import Rota

        return Rota.objects.select_related('percurso').get(pk=rota_id)

    def listar_do_dia(self, data):
        """Retorna as rotas do dia com a execução e a ocupação reais, quando existirem."""
        from Transporte.execucoes_rotas.models import ExecucaoRota
        from Transporte.tickets.choices import StatusTicket

        from .models import Rota

        execucoes_do_dia = (
            ExecucaoRota.objects.filter(data_execucao=data)
            .annotate(
                tickets_solicitados=Count(
                    'tickets',
                    filter=Q(
                        tickets__status__in=(
                            StatusTicket.RESERVADO,
                            StatusTicket.EMBARCADO,
                        ),
                    ),
                    distinct=True,
                ),
                tickets_embarcados=Count(
                    'tickets',
                    filter=Q(tickets__status=StatusTicket.EMBARCADO),
                    distinct=True,
                ),
                entradas_sem_ticket_count=Count(
                    'entradas_sem_ticket',
                    distinct=True,
                ),
            )
            .order_by('data_hora_saida', 'rota_id')
        )

        return (
            Rota.objects.select_related('percurso')
            .filter(
                ativo=True,
                percurso__ativo=True,
                dia_semana=dia_semana_da_data(data),
            )
            .annotate(
                data_operacao=Value(data, output_field=DateField()),
            )
            .prefetch_related(
                Prefetch(
                    'execucoes',
                    queryset=execucoes_do_dia,
                    to_attr='execucoes_do_dia',
                ),
            )
            .order_by('horario_saida', 'percurso__apelido')
        )
