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
    tags=['Funções'],
    summary='Listar funções',
    description='''
    Retorna a lista paginada de funções organizacionais.

    **Permissões:** Apenas administradores.

    **Query params apenas reduzem o conjunto â€” nunca expandem o acesso.**
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por ativa (true) ou inativa (false).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1â€“100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: FuncaoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class ListarFuncoesView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/organizacional/funcoes/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = FuncaoSerializer
    mensagem_sucesso = 'Funções listadas com sucesso.'

    def get_queryset(self):
        qs = Funcao.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs


@extend_schema(
    tags=['Funções'],
    summary='Criar função',
    description='Cria uma nova função organizacional. A sigla deve ser única.\n\n**Permissões:** Apenas administradores.',
    request=CriarFuncaoSerializer,
    responses={
        status.HTTP_201_CREATED: FuncaoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já¡ cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class CriarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/funcoes/"""
    serializer_class = CriarFuncaoSerializer
    mensagem_sucesso = 'Função criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        funcao = FuncaoBusiness().criar_funcao(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': FuncaoSerializer(funcao).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Funções'],
    summary='Detalhe da função',
    description='Retorna os dados de uma função específica.\n\n**Permissões:** Apenas administradores.',
    responses={
        status.HTTP_200_OK: FuncaoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
    },
)
class DetalheFuncaoView(IsAdminMixin, BasicRetrieveAPIView):
    """GET /cortex/organizacional/funcoes/<pk>/"""
    queryset = Funcao.objects.all()
    serializer_class = FuncaoSerializer
    mensagem_sucesso = 'Função obtida com sucesso.'


@extend_schema(
    tags=['Funções'],
    summary='Atualizar função',
    description='Atualiza parcialmente os dados da função.\n\n**Permissões:** Apenas administradores.',
    request=AtualizarFuncaoSerializer,
    responses={
        status.HTTP_200_OK: FuncaoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já¡ cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
    },
)
class AtualizarFuncaoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/organizacional/funcoes/<pk>/"""
    queryset = Funcao.objects.all()
    serializer_class = AtualizarFuncaoSerializer
    mensagem_sucesso = 'Função atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': FuncaoSerializer(self.object).data,
        }


@extend_schema(
    tags=['Funções'],
    summary='Desativar função',
    description='Desativa uma função. Bloqueado se estiver em uso em vínculos.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Função desativada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Função já¡ inativa ou em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
    },
)
class DesativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/funcoes/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Função desativada com sucesso.'
    queryset = Funcao.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Funções'],
    summary='Reativar função',
    description='Reativa uma função previamente desativada.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Função reativada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Função já está ativa.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
    },
)
class ReativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/funcoes/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Função reativada com sucesso.'
    queryset = Funcao.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()

