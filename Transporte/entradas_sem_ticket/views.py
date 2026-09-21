from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.views.basic_views import BasicPostAPIView
from Transporte.permissoes.access import PodeConferirTransporteMixin

from .models import EntradaSemTicket
from .serializers import (
    AlunoEntradaSerializer,
    ElegibilidadeEntradaSerializer,
    RegistrarEntradaSemTicketSerializer,
    ResultadoRegistroEntradaSerializer,
    ValidarEntradaSemTicketSerializer,
)

PERMISSAO_CONFERIR = (
    '**Permissões:** capacidade transporte.conferir. Lê e opera execuções do dia e, '
    'após iniciar o monitoramento, a chamada de tickets e a entrada por CPF dessa execução. '
    'Não amplia cadastro nem recursos globais do módulo.'
)
REGRA_CPF = (
    'Registra um CPF por vez após o encerramento da chamada de tickets. '
    'Quem está EM_ESPERA fica CONTEMPLADO e recebe EntradaSemTicket. '
    'Quem não for registrado permanece EM_ESPERA após finalizar a conferência.'
)
REGRA_AUSENTE_CPF = (
    'Quem está AUSENTE e entra por CPF passa a EMBARCADO sem EntradaSemTicket e sem strike '
    'até a finalização da conferência.'
)


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Validar CPF para entrada sem ticket',
    description=(
        'Consulta as regras de elegibilidade sem persistir e devolve os dados do aluno '
        'para o card. Disponível somente na fase de CPF, antes de finalizar a conferência. '
        f'{REGRA_CPF} {REGRA_AUSENTE_CPF}\n\n'
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
    summary='Registrar entrada por CPF',
    description=(
        'Recebe `{ "cpf": "..." }` e persiste um registro por vez. Replay do mesmo aluno '
        'devolve 200. '
        f'{REGRA_CPF} {REGRA_AUSENTE_CPF}\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=RegistrarEntradaSemTicketSerializer,
    responses={
        status.HTTP_200_OK: ResultadoRegistroEntradaSerializer,
        status.HTTP_201_CREATED: ResultadoRegistroEntradaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de entrada não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Aluno ou execução não encontrada.'},
    },
)
class RegistrarEntradaSemTicketView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = RegistrarEntradaSemTicketSerializer
    mensagem_sucesso = 'Entrada por CPF registrada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        resultado = EntradaSemTicket().business.registrar_um(
            kwargs['pk'],
            serializer_data['cpf'],
        )
        replay = resultado['replay']
        return {
            'dados': ResultadoRegistroEntradaSerializer(
                resultado,
                context={'request': request},
            ).data,
            'status_code': status.HTTP_200_OK if replay else status.HTTP_201_CREATED,
        }
