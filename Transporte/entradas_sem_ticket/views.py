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
    'após iniciar o monitoramento, a chamada de tickets e a entrada por CPF dessa execução. '
    'Não amplia cadastro nem recursos globais do módulo.'
)
REGRA_CPF = (
    'Inclui aluno por CPF nas vagas restantes após a chamada de tickets. '
    'Quem está EM_ESPERA e for informado no lote fica CONTEMPLADO e recebe EntradaSemTicket. '
    'Quem não for informado permanece EM_ESPERA após finalizar a conferência: '
    'esse é o desfecho nessa execução, sem promoção posterior.'
)
REGRA_AUSENTE_CPF = (
    'Quem está AUSENTE nesta execução pode entrar se houver vaga '
    'e o aluno tiver menos de 3 strikes ativos; o ticket permanece AUSENTE e o '
    'strike não é desfeito.'
)


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Validar CPF para entrada sem ticket',
    description=(
        'Consulta as regras de elegibilidade sem persistir e devolve os dados do aluno '
        'para o card. Depois do primeiro lote não vazio, devolve 400: o conjunto já '
        'foi concluído e a tela não deve mostrar card que não dá para gravar. '
        'O POST em entradas-sem-ticket/ revalida o lote e grava. '
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
    summary='Registrar entradas sem ticket em lote',
    description=(
        'Recebe `{ "cpfs": [...] }`, revalida cada CPF e grava o lote numa transação. '
        'Replay do mesmo conjunto devolve 200. Conjunto diferente após o primeiro lote '
        'não vazio devolve 400. Lista vazia não conclui o lote (201 sem persistir). '
        f'{REGRA_CPF} {REGRA_AUSENTE_CPF}\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=RegistrarEntradaSemTicketSerializer,
    responses={
        status.HTTP_200_OK: EntradaSemTicketSerializer(many=True),
        status.HTTP_201_CREATED: EntradaSemTicketSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de entrada não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Aluno ou execução não encontrada.'},
    },
)
class RegistrarEntradaSemTicketView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = RegistrarEntradaSemTicketSerializer
    mensagem_sucesso = 'Entradas sem ticket registradas com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        resultado = EntradaSemTicket().business.registrar(
            kwargs['pk'],
            serializer_data.get('cpfs') or [],
        )
        replay = resultado['replay']
        return {
            'dados': EntradaSemTicketSerializer(resultado['entradas'], many=True).data,
            'status_code': status.HTTP_200_OK if replay else status.HTTP_201_CREATED,
        }
