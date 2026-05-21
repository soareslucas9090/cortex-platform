import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .business import FuncaoBusiness
from .models import Funcao
from .serializers import (
    AtualizarFuncaoSerializer,
    CriarFuncaoSerializer,
    FuncaoSerializer,
    SerializerVazio,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Listar funÃ§Ãµes',
    description='''
    Retorna a lista paginada de funÃ§Ãµes organizacionais.

    **PermissÃµes:** Apenas administradores.

    **Query params apenas reduzem o conjunto â€” nunca expandem o acesso.**
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por ativa (true) ou inativa (false).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da pÃ¡gina (1â€“100, padrÃ£o 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: FuncaoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
    },
)
class ListarFuncoesView(IsAdminMixin, BasicGetAPIView):
    """GET /organizacional/funcoes/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = FuncaoSerializer
    mensagem_sucesso = 'FunÃ§Ãµes listadas com sucesso.'

    def get_queryset(self):
        qs = Funcao.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Criar funÃ§Ã£o',
    description='Cria uma nova funÃ§Ã£o organizacional. A sigla deve ser Ãºnica.\n\n**PermissÃµes:** Apenas administradores.',
    request=CriarFuncaoSerializer,
    responses={
        status.HTTP_201_CREATED: FuncaoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados invÃ¡lidos ou sigla jÃ¡ cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
    },
)
class CriarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/funcoes/"""
    serializer_class = CriarFuncaoSerializer
    mensagem_sucesso = 'FunÃ§Ã£o criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        funcao = FuncaoBusiness().criar_funcao(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': FuncaoSerializer(funcao).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Detalhe da funÃ§Ã£o',
    description='Retorna os dados de uma funÃ§Ã£o especÃ­fica.\n\n**PermissÃµes:** Apenas administradores.',
    responses={
        status.HTTP_200_OK: FuncaoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'FunÃ§Ã£o nÃ£o encontrada.'},
    },
)
class DetalheFuncaoView(IsAdminMixin, BasicRetrieveAPIView):
    """GET /organizacional/funcoes/<pk>/"""
    queryset = Funcao.objects.all()
    serializer_class = FuncaoSerializer
    mensagem_sucesso = 'FunÃ§Ã£o obtida com sucesso.'


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Atualizar funÃ§Ã£o',
    description='Atualiza parcialmente os dados da funÃ§Ã£o.\n\n**PermissÃµes:** Apenas administradores.',
    request=AtualizarFuncaoSerializer,
    responses={
        status.HTTP_200_OK: FuncaoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados invÃ¡lidos ou sigla jÃ¡ cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'FunÃ§Ã£o nÃ£o encontrada.'},
    },
)
class AtualizarFuncaoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /organizacional/funcoes/<pk>/"""
    queryset = Funcao.objects.all()
    serializer_class = AtualizarFuncaoSerializer
    mensagem_sucesso = 'FunÃ§Ã£o atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': FuncaoSerializer(self.object).data,
        }


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Desativar funÃ§Ã£o',
    description='Desativa uma funÃ§Ã£o. Bloqueado se estiver em uso em vÃ­nculos.\n\n**PermissÃµes:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'FunÃ§Ã£o desativada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'FunÃ§Ã£o jÃ¡ inativa ou em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'FunÃ§Ã£o nÃ£o encontrada.'},
    },
)
class DesativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/funcoes/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'FunÃ§Ã£o desativada com sucesso.'
    queryset = Funcao.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['FunÃ§Ãµes'],
    summary='Reativar funÃ§Ã£o',
    description='Reativa uma funÃ§Ã£o previamente desativada.\n\n**PermissÃµes:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'FunÃ§Ã£o reativada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'FunÃ§Ã£o jÃ¡ estÃ¡ ativa.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'FunÃ§Ã£o nÃ£o encontrada.'},
    },
)
class ReativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/funcoes/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'FunÃ§Ã£o reativada com sucesso.'
    queryset = Funcao.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()

