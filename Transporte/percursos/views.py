from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .models import Percurso
from .serializers import (
    AtualizarPercursoSerializer,
    CriarPercursoSerializer,
    PercursoSerializer,
    SerializerVazio,
)

PERMISSAO_TI = (
    '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
)


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Listar percursos',
    description=f'''
    Lista os percursos cadastrados, com busca, filtro de status e paginação.

    {PERMISSAO_TI}

    **Paginação:** query param `paginacao` (padrão 10, máximo 100).

    **Filtros:** os query params apenas reduzem o conjunto de resultados.
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False, description='Filtra por status: true = Ativo, false = Inativo. Omitir para todos.'),
        OpenApiParameter('busca', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Filtra por parte do apelido ou da descrição (ignora acentos e maiúsculas).'),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Tamanho da página (1–100, padrão 10).'),
    ],
    responses={
        status.HTTP_200_OK: PercursoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ListarPercursosView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/transporte/percursos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = PercursoSerializer
    mensagem_sucesso = 'Percursos listados com sucesso.'

    def get_queryset(self):
        qs = Percurso.objects.all()

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')

        busca = self.request.query_params.get('busca')
        if busca:
            qs = qs.filter(
                Q(apelido__unaccent__icontains=busca) | Q(descricao__unaccent__icontains=busca)
            )

        return qs


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Criar percurso',
    description=f'''
    Cadastra um novo percurso.

    {PERMISSAO_TI}
    ''',
    request=CriarPercursoSerializer,
    responses={
        status.HTTP_201_CREATED: PercursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou apelido já em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class CriarPercursoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/percursos/"""
    serializer_class = CriarPercursoSerializer
    mensagem_sucesso = 'Percurso criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        percurso = Percurso().business.criar_percurso(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': PercursoSerializer(percurso).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Detalhar percurso',
    description=f'''
    Retorna os dados de um percurso.

    {PERMISSAO_TI}
    ''',
    responses={
        status.HTTP_200_OK: PercursoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Percurso não encontrado.'},
    },
)
class DetalharPercursoView(IsAdminMixin, BasicRetrieveAPIView):
    """GET /cortex/transporte/percursos/<pk>/"""
    queryset = Percurso.objects.all()
    serializer_class = PercursoSerializer
    mensagem_sucesso = 'Percurso obtido com sucesso.'


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Atualizar percurso',
    description=f'''
    Atualiza parcialmente um percurso.

    {PERMISSAO_TI}
    ''',
    request=AtualizarPercursoSerializer,
    responses={
        status.HTTP_200_OK: PercursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou apelido já em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Percurso não encontrado.'},
    },
)
class AtualizarPercursoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/transporte/percursos/<pk>/"""
    queryset = Percurso.objects.all()
    serializer_class = AtualizarPercursoSerializer
    mensagem_sucesso = 'Percurso atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        self.object.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': PercursoSerializer(self.object).data,
        }


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Desativar percurso',
    description=f'''
    Desativa um percurso ativo.

    {PERMISSAO_TI}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: PercursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Percurso já está inativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Percurso não encontrado.'},
    },
)
class DesativarPercursoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/percursos/<pk>/desativar/"""
    queryset = Percurso.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Percurso desativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        percurso = self.get_object()
        percurso.business.desativar()
        percurso.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': PercursoSerializer(percurso).data,
        }


@extend_schema(
    tags=['Transporte · Percursos'],
    summary='Reativar percurso',
    description=f'''
    Reativa um percurso inativo.

    {PERMISSAO_TI}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: PercursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Percurso já está ativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Percurso não encontrado.'},
    },
)
class ReativarPercursoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/transporte/percursos/<pk>/reativar/"""
    queryset = Percurso.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Percurso reativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        percurso = self.get_object()
        percurso.business.reativar()
        percurso.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': PercursoSerializer(percurso).data,
        }
