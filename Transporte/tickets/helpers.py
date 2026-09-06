from django.core import signing
from django.db.models import Case, F, IntegerField, Value, When

from AppCore.core.helpers.helpers import ModelInstanceHelpers
from Transporte.strikes.choices import StatusStrike

from .choices import StatusTicket

SALT_QR_TICKET = 'Transporte.tickets.qr'


class TicketHelpers(ModelInstanceHelpers):

    def _listar_com_relacionamentos(self):
        from .models import Ticket

        return Ticket.objects.select_related(
            'execucao_rota',
            'execucao_rota__rota',
            'execucao_rota__rota__percurso',
            'aluno',
            'aluno__usuario',
        )

    def listar_para_usuario(self, usuario):
        queryset = self._listar_com_relacionamentos()
        if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            return queryset
        aluno = getattr(usuario, 'aluno', None)
        return queryset.filter(aluno=aluno) if aluno is not None else queryset.none()

    def obter_por_codigo(self, codigo):
        return self._listar_com_relacionamentos().get(codigo=codigo)

    def obter_bloqueado_por_id(self, ticket_id):
        from .models import Ticket

        return Ticket.objects.select_for_update().select_related(
            'aluno__usuario',
            'execucao_rota',
        ).get(pk=ticket_id)

    def contar_strikes_ativos(self, aluno):
        return aluno.tickets_transporte.filter(
            strike__status=StatusStrike.ATIVO,
        ).count()

    def existe_ticket_ativo(self, execucao, aluno):
        from .models import Ticket

        return Ticket.objects.filter(
            execucao_rota=execucao,
            aluno=aluno,
        ).exclude(status=StatusTicket.CANCELADO).exists()

    def contar_reservas(self, execucao):
        return execucao.tickets.filter(status=StatusTicket.RESERVADO).count()

    def _anotar_prioridade_pcd(self, queryset):
        return queryset.annotate(
            prioridade_pcd=Case(
                When(
                    aluno__usuario__deficiencia__isnull=False,
                    aluno__usuario__deficiencia__gt='',
                    then=Value(1),
                ),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )

    def _ordenar_reservas(self, queryset=None):
        from .models import Ticket

        if queryset is None:
            queryset = Ticket.objects.all()
        return self._anotar_prioridade_pcd(queryset).filter(
            status__in=(
                StatusTicket.RESERVADO,
                StatusTicket.EMBARCADO,
                StatusTicket.AUSENTE,
            ),
        ).order_by(
            '-prioridade_pcd',
            F('reservado_em').asc(nulls_last=True),
            'pk',
        )

    def _ordenar_fila(self, queryset=None):
        from .models import Ticket

        if queryset is None:
            queryset = Ticket.objects.all()
        return self._anotar_prioridade_pcd(queryset).filter(
            status=StatusTicket.EM_ESPERA,
        ).order_by('-prioridade_pcd', 'entrou_em_espera_em', 'pk')

    def _obter_posicao(self):
        ticket = self.object_instance
        return self.obter_posicoes_execucao(ticket.execucao_rota).get(ticket.pk)

    def obter_posicoes_execucao(self, execucao):
        posicoes = {}
        reservas = self._ordenar_reservas(execucao.tickets.all()).values_list('pk', flat=True)
        for atual, ticket_id in enumerate(reservas, start=1):
            posicoes[ticket_id] = {
                'tipo': 'RESERVA',
                'atual': atual,
                'total': execucao.quantidade_vagas,
            }

        fila = list(self._ordenar_fila(execucao.tickets.all()).values_list('pk', flat=True))
        for atual, ticket_id in enumerate(fila, start=1):
            posicoes[ticket_id] = {
                'tipo': 'ESPERA',
                'atual': atual,
                'total': len(fila),
            }
        return posicoes

    def obter_posicao_fila(self):
        posicao = self._obter_posicao()
        if posicao is None or posicao['tipo'] != 'ESPERA':
            return None
        return posicao['atual']

    def listar_reservas_conferencia(self, execucao, cpf=None):
        queryset = self._ordenar_reservas(execucao.tickets.all())
        if cpf:
            queryset = queryset.filter(aluno__usuario__cpf__icontains=cpf.strip())
        return queryset.select_related(
            'execucao_rota',
            'execucao_rota__rota',
            'execucao_rota__rota__percurso',
            'aluno',
            'aluno__usuario',
        )

    def proximo_da_fila(self, execucao):
        return self._ordenar_fila(
            execucao.tickets.select_for_update(),
        ).first()

    def contar_espera(self, execucao) -> int:
        return execucao.tickets.filter(status=StatusTicket.EM_ESPERA).count()

    def listar_reservados_bloqueados(self, execucao):
        from .models import Ticket

        return Ticket.objects.select_for_update().select_related(
            'execucao_rota',
            'aluno__usuario',
        ).filter(
            execucao_rota=execucao,
            status=StatusTicket.RESERVADO,
        )

    def gerar_codigo_qr(self):
        ticket = self.object_instance
        return signing.dumps(
            {'ticket': str(ticket.codigo), 'execucao': ticket.execucao_rota_id},
            salt=SALT_QR_TICKET,
            compress=True,
        )

    def decodificar_qr(self, codigo_qr):
        return signing.loads(codigo_qr, salt=SALT_QR_TICKET)
