from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicRetrieveAPIView

from .models import TipoAutorizacaoAcesso
from .serializers import TipoAutorizacaoAcessoSerializer

PERMISSOES_CATALOGO = '''
    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Cadastro apenas no Django Admin.
    '''


@extend_schema(
    tags=['AcessoCampus'],
    summary='Listar tipos de autorização',
    description=f'''
    Lista os tipos de autorização cadastrados. Entrada no campus e Saída do campus são tipos-base.

    {PERMISSOES_CATALOGO}
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False,
            description='Filtra por ativo (true) ou inativo (false).',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description='Parte do nome, sem diferenciar acento.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: TipoAutorizacaoAcessoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarTiposAutorizacaoView(IsAuthenticatedMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = TipoAutorizacaoAcessoSerializer
    mensagem_sucesso = 'Tipos de autorização listados com sucesso.'

    def get_queryset(self):
        qs = TipoAutorizacaoAcesso.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        return qs


@extend_schema(
    tags=['AcessoCampus'],
    summary='Detalhar tipo de autorização',
    description=f'''
    Retorna os dados de um tipo específico.

    {PERMISSOES_CATALOGO}
    ''',
    responses={
        status.HTTP_200_OK: TipoAutorizacaoAcessoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Tipo não encontrado.'},
    },
)
class DetalheTipoAutorizacaoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    queryset = TipoAutorizacaoAcesso.objects.all()
    serializer_class = TipoAutorizacaoAcessoSerializer
    mensagem_sucesso = 'Tipo de autorização obtido com sucesso.'
