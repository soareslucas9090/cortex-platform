from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.views.basic_views import BasicPostAPIView
from Transporte.permissoes.access import PodeConferirTransporteMixin

from .models import EntradaSemTicket
from .serializers import (
    AlunoEntradaSerializer,
    ElegibilidadeEntradaSerializer,
    EntradaSemTicketSerializer,
    RegistrarEntradaSemTicketSerializer,
    ValidarEntradaSemTicketSerializer,
)

PERMISSAO_CONFERIR = (
    '**Permissões:** capacidade transporte.conferir. Lê e opera execuções do dia e, '
    'após iniciar o monitoramento, as filas de ticket e de espera dessa execução. '
    'Não amplia cadastro nem recursos globais do módulo.'
)


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Validar CPF para entrada sem ticket',
    description=(
        'Consulta as regras de elegibilidade sem persistir. '
        'O POST em entradas-sem-ticket/ revalida tudo e grava.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=ValidarEntradaSemTicketSerializer,
    responses={
        status.HTTP_200_OK: ElegibilidadeEntradaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de entrada não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Aluno ou execução não encontrada.'},
    },
)
class ValidarEntradaSemTicketView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = ValidarEntradaSemTicketSerializer
    mensagem_sucesso = 'Aluno elegível para entrada sem ticket.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        aluno = EntradaSemTicket().business.validar_elegibilidade(
            kwargs['pk'],
            serializer_data['cpf'],
        )
        return {
            'dados': {
                'aluno': AlunoEntradaSerializer(aluno).data,
                'elegivel': True,
            },
        }


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
        entrada = EntradaSemTicket().business.registrar(
            kwargs['pk'],
            serializer_data['cpf'],
            serializer_data.get('observacao', ''),
        )
        return {
            'dados': EntradaSemTicketSerializer(entrada).data,
            'status_code': status.HTTP_201_CREATED,
        }
