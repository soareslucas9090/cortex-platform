from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .models import Rota
from .serializers import (
    AtualizarRotaSerializer,
    CriarRotaSerializer,
    RotaDoDiaSerializer,
    RotaSerializer,
    SerializerVazio,
)

PERMISSAO_TI = (
    '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
)

PERMISSAO_MOTORISTA = (
    '**Permissões:** Motorista ativo. Todos os motoristas visualizam todas as rotas do dia.'
)


@extend_schema(
    tags=['Transporte · Motorista'],
    summary='Listar rotas do dia',
    description=f'''
    Lista todas as rotas e percursos ativos programados para o dia atual, em ordem de horário.
    Quando existe uma execução para a rota, inclui o status operacional, a capacidade
    congelada da execução e a quantidade real de vagas ocupadas por tickets.
    Rotas ainda sem execução retornam status nulo e zero tickets solicitados.
    Este endpoint é exclusivamente de leitura e não cria nem altera dados operacionais.

    {PERMISSAO_MOTORISTA}
    ''',
    responses={
        status.HTTP_200_OK: RotaDoDiaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Usuário não é motorista ativo.'},
    },
)
class ListarRotasDoDiaView(IsAuthenticatedMixin, BasicGetAPIView):
    pagination_class = None
    serializer_class = RotaDoDiaSerializer
    mensagem_sucesso = 'Rotas do dia listadas com sucesso.'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Rota.objects.none()
        return Rota().business.listar_rotas_do_dia(self.request.user)


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Listar rotas',
    description=f'''
    Lista as rotas cadastradas, com filtros e paginação.

    {PERMISSAO_TI}

    **Paginação:** query param `paginacao` (padrão 10, máximo 100).

    **Filtros:** os query params apenas reduzem o conjunto de resultados.
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False, description='Filtra por status: true = Ativo, false = Inativo. Omitir para todos.'),
        OpenApiParameter('percurso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filtra pelo identificador do percurso.'),
        OpenApiParameter('dia_semana', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Filtra pelo dia da semana (segunda, terca, quarta, quinta, sexta, sabado, domingo). Valores inválidos são ignorados.'),
        OpenApiParameter('busca', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Filtra por parte do apelido do percurso (ignora acentos e maiúsculas).'),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Tamanho da página (1–100, padrão 10).'),
    ],
    responses={
        status.HTTP_200_OK: RotaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ListarRotasView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/transporte/rotas/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = RotaSerializer
    mensagem_sucesso = 'Rotas listadas com sucesso.'

    def get_queryset(self):
        return Rota().business.listar_rotas(
            ativo=self.request.query_params.get('ativo'),
            percurso_id=self.request.query_params.get('percurso_id'),
            dia_semana=self.request.query_params.get('dia_semana'),
            busca=self.request.query_params.get('busca'),
        )


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Criar rota',
    description=f'''
    Cadastra uma nova rota vinculada a um percurso.

    {PERMISSAO_TI}
    ''',
    request=CriarRotaSerializer,
    responses={
        status.HTTP_201_CREATED: RotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou rota duplicada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Percurso não encontrado.'},
    },
)
class CriarRotaView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/rotas/"""
    serializer_class = CriarRotaSerializer
    mensagem_sucesso = 'Rota criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        rota = Rota().business.criar_rota(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RotaSerializer(rota).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Detalhar rota',
    description=f'''
    Retorna os dados de uma rota.

    {PERMISSAO_TI}
    ''',
    responses={
        status.HTTP_200_OK: RotaSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Rota não encontrada.'},
    },
)
class DetalharRotaView(IsAdminMixin, BasicRetrieveAPIView):
    """GET /cortex/transporte/rotas/<pk>/"""
    queryset = Rota.objects.select_related('percurso').all()
    serializer_class = RotaSerializer
    mensagem_sucesso = 'Rota obtida com sucesso.'


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Atualizar rota',
    description=f'''
    Atualiza parcialmente uma rota.

    {PERMISSAO_TI}
    ''',
    request=AtualizarRotaSerializer,
    responses={
        status.HTTP_200_OK: RotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou rota duplicada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Rota não encontrada.'},
    },
)
class AtualizarRotaView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/transporte/rotas/<pk>/"""
    queryset = Rota.objects.select_related('percurso').all()
    serializer_class = AtualizarRotaSerializer
    mensagem_sucesso = 'Rota atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        self.object.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RotaSerializer(self.object).data,
        }


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Desativar rota',
    description=f'''
    Desativa uma rota ativa.

    {PERMISSAO_TI}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: RotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Rota já está inativa.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Rota não encontrada.'},
    },
)
class DesativarRotaView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/rotas/<pk>/desativar/"""
    queryset = Rota.objects.select_related('percurso').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Rota desativada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        rota = self.get_object()
        rota.business.desativar()
        rota.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RotaSerializer(rota).data,
        }


@extend_schema(
    tags=['Transporte · Rotas'],
    summary='Reativar rota',
    description=f'''
    Reativa uma rota inativa.

    {PERMISSAO_TI}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: RotaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Rota já está ativa ou o percurso está inativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Rota não encontrada.'},
    },
)
class ReativarRotaView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/rotas/<pk>/reativar/"""
    queryset = Rota.objects.select_related('percurso').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Rota reativada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        rota = self.get_object()
        rota.business.reativar()
        rota.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RotaSerializer(rota).data,
        }
