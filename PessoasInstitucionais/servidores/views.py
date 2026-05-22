from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.serializers import Serializer

from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
    BasicPatchAPIView,
)

from .choices import CategoriaServidor
from .models import Servidor
from .serializers import (
    ServidorSerializer,
    CriarServidorSerializer,
    AtualizarServidorSerializer,
)


# Classe vazia para endpoints que não recebem body
class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Servidores'],
    summary='Listar servidores',
    description='''
    Lista todos os servidores cadastrados.

    **Permissões:** Apenas administradores.

    Query params apenas reduzem o conjunto, nunca expandem o acesso.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por status: true = Ativo, false = Inativo.',
        ),
        OpenApiParameter(
            'categoria', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por categoria: 1 = Docente, 2 = Técnico-Administrativo.',
            enum=[c.value for c in CategoriaServidor],
        ),
        OpenApiParameter(
            'cargo', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por ID do cargo.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: ServidorSerializer(many=True),
    },
)
class ListarServidoresView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = ServidorSerializer
    mensagem_sucesso = 'Servidores listados com sucesso.'

    def get_queryset(self):
        qs = Servidor.objects.select_related('usuario', 'cargo').all()

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')

        categoria = self.request.query_params.get('categoria')
        if categoria is not None:
            try:
                categoria_int = int(categoria)
                if categoria_int in CategoriaServidor.values:
                    qs = qs.filter(categoria=categoria_int)
            except (ValueError, TypeError):
                pass

        cargo = self.request.query_params.get('cargo')
        if cargo is not None:
            try:
                cargo_int = int(cargo)
                qs = qs.filter(cargo_id=cargo_int)
            except (ValueError, TypeError):
                pass

        return qs


@extend_schema(
    tags=['Servidores'],
    summary='Criar servidor',
    description='''
    Cria um novo perfil de servidor para um usuário existente.

    **Permissões:** Apenas administradores.

    **Regras:**
    - O usuário informado deve existir e não possuir perfil de servidor.
    - O cargo informado deve existir e estar ativo.
    ''',
    request=CriarServidorSerializer,
    responses={
        status.HTTP_201_CREATED: ServidorSerializer,
    },
)
class CriarServidorView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarServidorSerializer
    mensagem_sucesso = 'Servidor criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        servidor = Servidor().business.criar_servidor(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ServidorSerializer(servidor).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Servidores'],
    summary='Detalhar servidor',
    description='''
    Exibe os detalhes de um servidor específico.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: ServidorSerializer,
    },
)
class DetalharServidorView(IsAdminMixin, BasicRetrieveAPIView):
    queryset = Servidor.objects.select_related('usuario', 'cargo').all()
    serializer_class = ServidorSerializer
    mensagem_sucesso = 'Servidor detalhado com sucesso.'


@extend_schema(
    tags=['Servidores'],
    summary='Atualizar servidor',
    description='''
    Atualiza os dados de um servidor existente.

    **Permissões:** Apenas administradores.
    ''',
    request=AtualizarServidorSerializer,
    responses={
        status.HTTP_200_OK: ServidorSerializer,
    },
)
class AtualizarServidorView(IsAdminMixin, BasicPatchAPIView):
    queryset = Servidor.objects.select_related('usuario', 'cargo').all()
    serializer_class = AtualizarServidorSerializer
    mensagem_sucesso = 'Servidor atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        servidor = self.get_object()
        servidor.business.atualizar_dados(serializer_data)
        servidor.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ServidorSerializer(servidor).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Servidores'],
    summary='Desativar servidor',
    description='''
    Desativa o perfil de um servidor.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ServidorSerializer,
    },
)
class DesativarServidorView(IsAdminMixin, BasicPostAPIView):
    queryset = Servidor.objects.select_related('usuario', 'cargo').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Servidor desativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        servidor = self.get_object()
        servidor.business.desativar()
        servidor.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ServidorSerializer(servidor).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Servidores'],
    summary='Reativar servidor',
    description='''
    Reativa o perfil de um servidor inativo.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: ServidorSerializer,
    },
)
class ReativarServidorView(IsAdminMixin, BasicPostAPIView):
    queryset = Servidor.objects.select_related('usuario', 'cargo').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Servidor reativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        servidor = self.get_object()
        servidor.business.reativar()
        servidor.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ServidorSerializer(servidor).data,
            'status_code': status.HTTP_200_OK,
        }
