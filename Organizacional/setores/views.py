import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .models import Setor
from .serializers import (
    AtualizarSetorSerializer,
    CriarSetorSerializer,
    SerializerVazio,
    SetorSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Setores'],
    summary='Listar setores',
    description='''
    Retorna a lista paginada de setores da instituição.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).

    **Query params apenas reduzem o conjunto — nunca expandem o acesso.**
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por ativo (true) ou inativo (false).',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'sigla', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte da sigla (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: SetorSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class ListarSetoresView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/organizacional/setores/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SetorSerializer
    mensagem_sucesso = 'Setores listados com sucesso.'

    def get_queryset(self):
        qs = Setor.objects.all()
        
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
            
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
            
        sigla = self.request.query_params.get('sigla')
        if sigla:
            qs = qs.filter(sigla__unaccent__icontains=sigla)
            
        return qs


@extend_schema(
    tags=['Setores'],
    summary='Criar setor',
    description='Cria um novo setor. A sigla deve ser única.\n\n**Permissões:** Apenas administradores.',
    request=CriarSetorSerializer,
    responses={
        status.HTTP_201_CREATED: SetorSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class CriarSetorView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/"""
    serializer_class = CriarSetorSerializer
    mensagem_sucesso = 'Setor criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        setor = Setor().business.criar_setor(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SetorSerializer(setor).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Setores'],
    summary='Detalhe do setor',
    description='Retorna os dados de um setor específico.\n\n**Permissões:** Qualquer usuário autenticado (catálogo de referência).',
    responses={
        status.HTTP_200_OK: SetorSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class DetalheSetorView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/organizacional/setores/<pk>/"""
    queryset = Setor.objects.all()
    serializer_class = SetorSerializer
    mensagem_sucesso = 'Setor obtido com sucesso.'


@extend_schema(
    tags=['Setores'],
    summary='Atualizar setor',
    description='Atualiza parcialmente os dados do setor (nome e/ou sigla).\n\n**Permissões:** Apenas administradores.',
    request=AtualizarSetorSerializer,
    responses={
        status.HTTP_200_OK: SetorSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class AtualizarSetorView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/organizacional/setores/<pk>/"""
    queryset = Setor.objects.all()
    serializer_class = AtualizarSetorSerializer
    mensagem_sucesso = 'Setor atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SetorSerializer(self.object).data,
        }


@extend_schema(
    tags=['Setores'],
    summary='Desativar setor',
    description='Desativa um setor. Bloqueado se houver vínculos ativos.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Setor desativado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Setor já inativo ou com vínculos ativos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class DesativarSetorView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Setor desativado com sucesso.'
    queryset = Setor.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Setores'],
    summary='Reativar setor',
    description='Reativa um setor previamente desativado.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Setor reativado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Setor já está ativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class ReativarSetorView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Setor reativado com sucesso.'
    queryset = Setor.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()
