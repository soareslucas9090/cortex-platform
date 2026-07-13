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

from .models import Bloco
from .serializers import (
    AtualizarBlocoSerializer,
    BlocoSerializer,
    CriarBlocoSerializer,
    SerializerVazio,
)


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Listar blocos',
    description='''
    Retorna a lista paginada de blocos.

    **Permissões:** Qualquer usuário autenticado. Escrita exige capacidade `cadastrar`.
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
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={status.HTTP_200_OK: BlocoSerializer(many=True)},
)
class ListarBlocosView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/blocos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = BlocoSerializer
    mensagem_sucesso = 'Blocos listados com sucesso.'

    def get_queryset(self):
        qs = Bloco.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        return qs


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Criar bloco',
    description='Cria um novo bloco.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=CriarBlocoSerializer,
    responses={status.HTTP_201_CREATED: BlocoSerializer},
)
class CriarBlocoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/blocos/"""
    serializer_class = CriarBlocoSerializer
    mensagem_sucesso = 'Bloco criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        bloco = Bloco().business.criar_bloco(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': BlocoSerializer(bloco).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Detalhe do bloco',
    description='Retorna os dados de um bloco.\n\n**Permissões:** Qualquer usuário autenticado.',
    responses={status.HTTP_200_OK: BlocoSerializer},
)
class DetalheBlocoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/blocos/<pk>/"""
    queryset = Bloco.objects.all()
    serializer_class = BlocoSerializer
    mensagem_sucesso = 'Bloco obtido com sucesso.'


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Atualizar bloco',
    description='Atualiza parcialmente um bloco.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=AtualizarBlocoSerializer,
    responses={status.HTTP_200_OK: BlocoSerializer},
)
class AtualizarBlocoView(PodeCadastrarInfraestruturaMixin, BasicPatchAPIView):
    """PATCH /cortex/infraestrutura/blocos/<pk>/"""
    queryset = Bloco.objects.all()
    serializer_class = AtualizarBlocoSerializer
    mensagem_sucesso = 'Bloco atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': BlocoSerializer(self.object).data,
        }


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Desativar bloco',
    description='Desativa um bloco. Bloqueado se houver salas ativas.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Bloco desativado com sucesso.'}},
)
class DesativarBlocoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/blocos/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Bloco desativado com sucesso.'
    queryset = Bloco.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Infraestrutura · Blocos'],
    summary='Reativar bloco',
    description='Reativa um bloco previamente desativado.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Bloco reativado com sucesso.'}},
)
class ReativarBlocoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/blocos/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Bloco reativado com sucesso.'
    queryset = Bloco.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()
