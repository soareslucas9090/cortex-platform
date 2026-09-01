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

from .choices import StatusExecucaoRota
from .models import ExecucaoRota
from .serializers import CriarExecucaoRotaSerializer, ExecucaoRotaSerializer, SerializerVazio

PERMISSAO_LISTAGEM = (
    '**Permissões:** Autenticado. L3 (EDITAR_TUDO) vê todas as execuções; '
    'demais usuários veem somente execuções abertas, em dia útil, da meia-noite '
    'do dia da viagem até exatamente 30 minutos antes da saída.'
)
PERMISSAO_ADMIN = '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'


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
    tags=['Transporte · Execuções de rotas'],
    summary='Iniciar embarque',
    description=f'Inicia o embarque e habilita a leitura dos QR Codes.\n\n{PERMISSAO_ADMIN}',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Transição de status inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class IniciarEmbarqueExecucaoRotaView(AlterarStatusExecucaoRotaView):
    novo_status = StatusExecucaoRota.EM_EMBARQUE
    mensagem_sucesso = 'Embarque iniciado com sucesso.'


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Finalizar execução',
    description=f'Finaliza uma execução em embarque.\n\n{PERMISSAO_ADMIN}',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ExecucaoRotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Transição de status inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Execução não encontrada.'},
    },
)
class FinalizarExecucaoRotaView(AlterarStatusExecucaoRotaView):
    novo_status = StatusExecucaoRota.FINALIZADA
    mensagem_sucesso = 'Execução finalizada com sucesso.'


@extend_schema(
    tags=['Transporte · Execuções de rotas'],
    summary='Cancelar execução',
    description=f'Cancela uma execução ainda não finalizada.\n\n{PERMISSAO_ADMIN}',
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
