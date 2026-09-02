from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.views.basic_views import BasicPostAPIView
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.permissoes.access import PodeConferirTransporteMixin
from Transporte.tickets.serializers import TicketConferenciaSerializer

from .models import EntradaSemTicket
from .serializers import EntradaSemTicketSerializer, RegistrarEntradaSemTicketSerializer

PERMISSAO_CONFERIR = (
    '**Permissões:** capacidade transporte.conferir. Lê e opera execuções do dia e, '
    'após iniciar o monitoramento, as filas de ticket e de espera dessa execução. '
    'Não amplia cadastro nem recursos globais do módulo.'
)


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Registrar entrada sem ticket',
    description=(
        'Inclui aluno por CPF em vaga remanescente quando a fila de espera está vazia.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=RegistrarEntradaSemTicketSerializer,
    responses={
        status.HTTP_201_CREATED: EntradaSemTicketSerializer,
        status.HTTP_200_OK: TicketConferenciaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de entrada não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Aluno ou execução não encontrada.'},
    },
)
class RegistrarEntradaSemTicketView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = RegistrarEntradaSemTicketSerializer
    mensagem_sucesso = 'Entrada sem ticket registrada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_para_conferencia(
            kwargs['pk'],
            exigir_embarque=True,
            usuario=request.user,
        )
        ticket, entrada = EntradaSemTicket().business.registrar(
            execucao.pk,
            serializer_data['cpf'],
            serializer_data.get('observacao', ''),
        )
        if ticket is not None:
            return {
                'mensagem': 'Aluno da fila de espera embarcado com sucesso.',
                'dados': TicketConferenciaSerializer(ticket).data,
            }
        return {
            'dados': EntradaSemTicketSerializer(entrada).data,
            'status_code': status.HTTP_201_CREATED,
        }
