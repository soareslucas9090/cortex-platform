from rest_framework import status

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from Infraestrutura.permissoes.access import PodeCadastrarInfraestruturaMixin

from .business import RecursoBusiness
from .choices import TipoRecurso
from .models import Recurso
from .serializers import (
    AtualizarRecursoSerializer,
    CriarRecursoSerializer,
    RecursoSerializer,
    SerializerVazio,
)


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Listar recursos',
    description='''
    Retorna a lista paginada de recursos físicos.

    **Permissões:** Qualquer usuário autenticado. Escrita exige capacidade `cadastrar`.
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('codigo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('tipo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('sala_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: RecursoSerializer(many=True)},
)
class ListarRecursosView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/recursos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = RecursoSerializer
    mensagem_sucesso = 'Recursos listados com sucesso.'

    def get_queryset(self):
        qs = Recurso.objects.select_related('sala').all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        codigo = self.request.query_params.get('codigo')
        if codigo:
            qs = qs.filter(codigo__unaccent__icontains=codigo)
        tipo = self.request.query_params.get('tipo')
        if tipo and tipo in TipoRecurso.values:
            qs = qs.filter(tipo=tipo)
        sala_id = self.request.query_params.get('sala_id')
        if sala_id and sala_id.isdigit():
            qs = qs.filter(sala_id=sala_id)
        return qs


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Criar recurso',
    description='''
    Cria um novo recurso. Tipo chave exige sala vinculada.

    **Permissões:** Capacidade `cadastrar` em Infraestrutura.
    ''',
    request=CriarRecursoSerializer,
    responses={status.HTTP_201_CREATED: RecursoSerializer},
)
class CriarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/"""
    serializer_class = CriarRecursoSerializer
    mensagem_sucesso = 'Recurso criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        recurso = RecursoBusiness().criar_recurso(**serializer_data)
        recurso = Recurso.objects.select_related('sala').get(pk=recurso.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RecursoSerializer(recurso).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Detalhe do recurso',
    description='Retorna os dados de um recurso.\n\n**Permissões:** Qualquer usuário autenticado.',
    responses={status.HTTP_200_OK: RecursoSerializer},
)
class DetalheRecursoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/recursos/<pk>/"""
    queryset = Recurso.objects.select_related('sala').all()
    serializer_class = RecursoSerializer
    mensagem_sucesso = 'Recurso obtido com sucesso.'


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Atualizar recurso',
    description='Atualiza parcialmente um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=AtualizarRecursoSerializer,
    responses={status.HTTP_200_OK: RecursoSerializer},
)
class AtualizarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPatchAPIView):
    """PATCH /cortex/infraestrutura/recursos/<pk>/"""
    queryset = Recurso.objects.select_related('sala').all()
    serializer_class = AtualizarRecursoSerializer
    mensagem_sucesso = 'Recurso atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        self.object.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RecursoSerializer(self.object).data,
        }


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Desativar recurso',
    description='Desativa um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Recurso desativado com sucesso.'}},
)
class DesativarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Recurso desativado com sucesso.'
    queryset = Recurso.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Reativar recurso',
    description='Reativa um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Recurso reativado com sucesso.'}},
)
class ReativarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Recurso reativado com sucesso.'
    queryset = Recurso.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()
