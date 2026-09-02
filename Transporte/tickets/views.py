from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .models import Ticket
from .serializers import (
    ResultadoAusenciaTicketSerializer,
    ResultadoCancelamentoTicketSerializer,
    ResultadoValidacaoQrSerializer,
    SerializerVazio,
    TicketSerializer,
    ValidarQrSerializer,
)

PERMISSAO_ALUNO = (
    '**Permissões:** Usuário autenticado. A operação exige perfil de aluno ativo e matriculado; '
    'tickets são sempre escopados ao próprio aluno.'
)
PERMISSAO_ADMIN = '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Listar tickets',
    description=(
        'Lista os tickets do aluno autenticado. L3 lista todos os tickets.\n\n'
        '**Permissões:** Autenticado. L1 vê apenas os próprios tickets; L3 vê todos.'
    ),
    responses={
        status.HTTP_200_OK: TicketSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarTicketsView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = TicketSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Tickets listados com sucesso.'

    def get_queryset(self):
        return Ticket().business.listar_para_usuario(self.request.user)


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Detalhar ticket',
    description=(
        'Retorna o ticket e o conteúdo assinado usado pelo frontend para renderizar o QR Code.\n\n'
        '**Permissões:** Autenticado. L1 vê apenas ticket próprio; L3 vê todos.'
    ),
    responses={
        status.HTTP_200_OK: TicketSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Ticket não encontrado no escopo.'},
    },
)
class DetalharTicketView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    serializer_class = TicketSerializer
    lookup_field = 'codigo'
    lookup_url_kwarg = 'codigo'
    mensagem_sucesso = 'Ticket obtido com sucesso.'

    def get_queryset(self):
        return Ticket().business.listar_para_usuario(self.request.user)


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Reservar ticket',
    description=(
        'Reserva uma vaga disponível, de segunda a sexta, da meia-noite do dia da '
        f'execução até exatamente 30 minutos antes da saída.\n\n{PERMISSAO_ALUNO}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_201_CREATED: TicketSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de reserva não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ReservarTicketView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Ticket reservado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket = Ticket().business.solicitar_reserva(kwargs['pk'], request.user)
        return {'dados': TicketSerializer(ticket).data, 'status_code': status.HTTP_201_CREATED}


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Entrar na fila de espera',
    description=(
        'Entra explicitamente na fila quando a execução está lotada, de segunda a '
        f'sexta, da meia-noite até exatamente 30 minutos antes da saída.\n\n{PERMISSAO_ALUNO}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_201_CREATED: TicketSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra da fila de espera não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class EntrarFilaEsperaView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Entrada na fila de espera realizada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket = Ticket().business.entrar_fila(kwargs['pk'], request.user)
        return {'dados': TicketSerializer(ticket).data, 'status_code': status.HTTP_201_CREATED}


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Cancelar ticket reservado',
    description=(
        'Cancela uma reserva, de segunda a sexta, da meia-noite até exatamente '
        f'30 minutos antes da saída.\n\n{PERMISSAO_ALUNO}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ResultadoCancelamentoTicketSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Cancelamento não permitido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Ticket não encontrado.'},
    },
)
class CancelarTicketView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Ticket cancelado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket = Ticket().business.obter_por_codigo(kwargs['codigo'])
        ticket, promovido = ticket.business.cancelar(request.user)
        return {
            'dados': {
                'ticket': TicketSerializer(ticket).data,
                'ticket_promovido': TicketSerializer(promovido).data if promovido else None,
            },
        }


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Sair da fila de espera',
    description=(
        'Remove o próprio ticket da fila, de segunda a sexta, da meia-noite até '
        f'exatamente 30 minutos antes da saída.\n\n{PERMISSAO_ALUNO}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: TicketSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Saída da fila não permitida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Ticket não encontrado.'},
    },
)
class SairFilaEsperaView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Saída da fila realizada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket = Ticket().business.obter_por_codigo(kwargs['codigo'])
        ticket = ticket.business.sair_fila(request.user)
        return {'dados': TicketSerializer(ticket).data}


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Marcar aluno ausente',
    description=f'Marca um ticket reservado como ausente e cria um strike.\n\n{PERMISSAO_ADMIN}',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ResultadoAusenciaTicketSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Ausência não pode ser registrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Ticket não encontrado.'},
    },
)
class MarcarTicketAusenteView(IsAdminMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Ausência registrada e strike criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket = Ticket().business.obter_por_codigo(kwargs['codigo'])
        ticket, strike = ticket.business.marcar_ausente()
        return {'dados': {'ticket': TicketSerializer(ticket).data, 'strike_id': strike.pk}}


@extend_schema(
    tags=['Transporte · Tickets'],
    summary='Validar QR Code de embarque',
    description=(
        'Valida o conteúdo assinado do QR Code e registra o embarque de forma idempotente.\n\n'
        f'{PERMISSAO_ADMIN}'
    ),
    request=ValidarQrSerializer,
    responses={
        status.HTTP_200_OK: ResultadoValidacaoQrSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'QR Code inválido ou embarque indisponível.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
    },
)
class ValidarQrTicketView(IsAdminMixin, BasicPostAPIView):
    serializer_class = ValidarQrSerializer
    mensagem_sucesso = 'QR Code validado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        ticket, ja_validado = Ticket().business.validar_qr(serializer_data['codigo_qr'])
        return {
            'dados': {
                'ticket': TicketSerializer(ticket).data,
                'ja_validado': ja_validado,
            },
        }
