from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from Transporte.permissoes.access import PodeConferirTransporteMixin
from Transporte.tickets.models import Ticket
from Transporte.tickets.serializers import TicketConferenciaSerializer

from .choices import StatusExecucaoRota
from .models import ExecucaoRota
from .serializers import (
    CriarExecucaoRotaSerializer,
    ExecucaoRotaSerializer,
    FinalizarChamadaSerializer,
    SerializerVazio,
)

PERMISSAO_LISTAGEM = (
    '**Permissões:** Autenticado. L3 (EDITAR_TUDO) vê todas as execuções; '
    'demais usuários veem somente execuções abertas, em dia útil, da meia-noite '
    'do dia da viagem até exatamente 30 minutos antes da saída.'
)
PERMISSAO_ADMIN = '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
PERMISSAO_CONFERIR = (
    '**Permissões:** capacidade transporte.conferir. Lê e opera execuções do dia e, '
    'após iniciar o monitoramento, as filas de ticket e de espera dessa execução. '
    'Não amplia cadastro nem recursos globais do módulo.'
)


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Listar execuções de rotas',
    description=(
        f'Lista as ocorrências das rotas. Os filtros apenas reduzem o escopo já permitido '
        f'ao usuário e não liberam execuções fora dele.\n\n{PERMISSAO_LISTAGEM}'
    ),
    parameters=[
        OpenApiParameter('status', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('data', OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarExecucoesRotasView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = ExecucaoRotaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Execuções de rotas listadas com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_para_usuario(
            self.request.user,
            self.request.query_params.get('status'),
            self.request.query_params.get('data'),
        )


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Criar execução de rota',
    description=f'Cria manualmente uma ocorrência de uma rota.\n\n{PERMISSAO_ADMIN}',
    request=CriarExecucaoRotaSerializer,
    responses={
        status.HTTP_201_CREATED: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados ou regras da rota inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
    },
)
class CriarExecucaoRotaView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarExecucaoRotaSerializer
    mensagem_sucesso = 'Execução de rota criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.criar_execucao(**serializer_data)
        return {
            'dados': ExecucaoRotaSerializer(execucao).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Detalhar execução de rota',
    description=f'Retorna uma execução de rota.\n\n{PERMISSAO_LISTAGEM}',
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada no escopo.'},
    },
)
class DetalharExecucaoRotaView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    serializer_class = ExecucaoRotaSerializer
    mensagem_sucesso = 'Execução de rota obtida com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_para_usuario(self.request.user)


class AlterarStatusExecucaoRotaView(IsAdminMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    novo_status = None

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_por_id(kwargs['pk'])
        execucao = execucao.business.alterar_status(self.novo_status)
        return {'dados': ExecucaoRotaSerializer(execucao).data}


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Abrir reservas',
    description=f'Reabre as reservas de uma execução fechada.\n\n{PERMISSAO_ADMIN}',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Transição de status inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class AbrirReservasExecucaoRotaView(AlterarStatusExecucaoRotaView):
    novo_status = StatusExecucaoRota.ABERTA
    mensagem_sucesso = 'Reservas abertas com sucesso.'


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Fechar reservas',
    description=f'Fecha as reservas de uma execução.\n\n{PERMISSAO_ADMIN}',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Transição de status inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class FecharReservasExecucaoRotaView(AlterarStatusExecucaoRotaView):
    novo_status = StatusExecucaoRota.FECHADA
    mensagem_sucesso = 'Reservas fechadas com sucesso.'


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Iniciar embarque',
    description=(
        'Inicia o monitoramento da execução do dia somente depois de 30 minutos antes da saída.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Fora da janela T-30 ou transição inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class IniciarEmbarqueExecucaoRotaView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Embarque iniciado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_para_conferencia(kwargs['pk'])
        execucao = execucao.business.iniciar_embarque()
        return {'dados': ExecucaoRotaSerializer(execucao).data}


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Finalizar execução',
    description=(
        'Embarca a fila que cabe nas vagas restantes, marca o restante da espera '
        f'como não contemplado (sem strike) e finaliza a execução.\n\n{PERMISSAO_CONFERIR}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Chamada pendente ou transição inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class FinalizarExecucaoRotaView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Execução finalizada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_para_conferencia(kwargs['pk'])
        execucao = execucao.business.finalizar_conferencia()
        return {'dados': ExecucaoRotaSerializer(execucao).data}


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Cancelar execução',
    description=(
        'Cancela uma execução ainda não iniciada em embarque e ainda não finalizada.\n\n'
        f'{PERMISSAO_ADMIN}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Transição de status inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class CancelarExecucaoRotaView(AlterarStatusExecucaoRotaView):
    novo_status = StatusExecucaoRota.CANCELADA
    mensagem_sucesso = 'Execução cancelada com sucesso.'


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Listar execuções do dia para conferência',
    description=(
        'Lista somente as execuções do dia. Query params apenas reduzem o conjunto.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    parameters=[
        OpenApiParameter(
            'data',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=False,
            description='Se diferente de hoje, retorna vazio. Não amplia o acesso.',
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
    },
)
class ListarExecucoesConferenciaView(PodeConferirTransporteMixin, BasicGetAPIView):
    serializer_class = ExecucaoRotaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Execuções do dia listadas com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_para_conferencia(
            self.request.query_params.get('data'),
        )


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Listar tickets da chamada',
    description=(
        'Lista os tickets da execução monitorada. O filtro cpf apenas reduz o conjunto.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    parameters=[
        OpenApiParameter(
            'cpf',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por CPF. Apenas reduz o conjunto já autorizado.',
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: TicketConferenciaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada no escopo.'},
    },
)
class ListarReservasConferenciaView(PodeConferirTransporteMixin, BasicGetAPIView):
    serializer_class = TicketConferenciaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Tickets da conferência listados com sucesso.'

    def get_queryset(self):
        execucao = ExecucaoRota().business.obter_para_conferencia(
            self.kwargs['pk'],
            exigir_embarque=True,
        )
        return Ticket().business.listar_reservas_conferencia(
            execucao,
            self.request.query_params.get('cpf'),
        )


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Finalizar chamada de tickets',
    description=(
        'Grava ausências (com strike) e embarca os demais tickets reservados.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=FinalizarChamadaSerializer,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Chamada inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
    },
)
class FinalizarChamadaConferenciaView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = FinalizarChamadaSerializer
    mensagem_sucesso = 'Chamada de tickets concluída com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_para_conferencia(
            kwargs['pk'],
            exigir_embarque=True,
        )
        execucao = execucao.business.finalizar_chamada(serializer_data.get('ausentes') or [])
        return {'dados': ExecucaoRotaSerializer(execucao).data}


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Listar fila de espera visível',
    description=(
        'Lista somente quem caberia agora (PcD + FIFO, limitado às vagas restantes). '
        'Quem está além desse limite não aparece; a remoção nesta tela vale só para '
        'os tickets listados. A promoção de toda a espera ocorre ao finalizar.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    parameters=[
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: TicketConferenciaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
    },
)
class ListarFilaConferenciaView(PodeConferirTransporteMixin, BasicGetAPIView):
    serializer_class = TicketConferenciaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Fila de espera listada com sucesso.'

    def get_queryset(self):
        execucao = ExecucaoRota().business.obter_para_conferencia(
            self.kwargs['pk'],
            exigir_embarque=True,
        )
        return Ticket().business.listar_fila_visivel_conferencia(execucao)


@extend_schema(
    tags=['Transporte · Conferência'],
    summary='Remover aluno da fila de espera',
    description=(
        'Cancela o ticket em espera sem gerar strike. Só aceita os N tickets da '
        'fila visível (vagas restantes), os mesmos do GET da fila.\n\n'
        f'{PERMISSAO_CONFERIR}'
    ),
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: TicketConferenciaSerializer,
        status.HTTP_400_BAD_REQUEST: {
            'description': (
                'Chamada pendente, ticket fora da fila visível, ou ticket que não está em espera.'
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade conferir.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Ticket ou execução não encontrado.'},
    },
)
class RemoverFilaConferenciaView(PodeConferirTransporteMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Aluno removido da fila de espera sem strike.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        execucao = ExecucaoRota().business.obter_para_conferencia(
            kwargs['pk'],
            exigir_embarque=True,
        )
        ticket = Ticket().business.obter_por_codigo(kwargs['codigo'])
        ticket = ticket.business.remover_espera_conferencia(execucao)
        return {'dados': TicketConferenciaSerializer(ticket).data}
