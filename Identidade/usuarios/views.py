import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin, IsOwnerOrAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .business import UsuarioBusiness
from .models import Usuario
from .serializers import (
    AtualizarUsuarioSerializer,
    CriarUsuarioSerializer,
    SerializerVazio,
    UsuarioSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Identidade'],
    summary='Listar usuários',
    description='''
    Retorna a lista paginada de usuários do sistema.

    **Permissões:** Apenas administradores.

    **Query params:**
    - `ativo` (bool, opcional): filtra por status — `true` (ativos) ou `false` (inativos).
      Omitindo o parâmetro, retorna todos.
    - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.

    **Segurança:** os query params apenas restringem o conjunto de resultados dentro do
    escopo já autorizado — nunca expandem o acesso além do permitido pela permissão.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por status ativo (true) ou inativo (false).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: UsuarioSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class ListarUsuariosView(IsAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuários listados com sucesso.'

    def get_queryset(self):
        qs = Usuario.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs


@extend_schema(
    tags=['Identidade'],
    summary='Criar usuário',
    description='''
    Cria um novo usuário no sistema.

    **Permissões:** Apenas administradores.

    Não há auto-cadastro — usuários são sempre criados por administradores,
    individualmente ou em lote via JSON.
    ''',
    request=CriarUsuarioSerializer,
    responses={
        status.HTTP_201_CREATED: UsuarioSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou CPF já cadastrado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class CriarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/"""
    serializer_class = CriarUsuarioSerializer
    mensagem_sucesso = 'Usuário criado com sucesso.'

    def do_action_post(self, serializer_data, request):
        usuario = UsuarioBusiness().criar_usuario(
            cpf=serializer_data['cpf'],
            nome=serializer_data['nome'],
            password=serializer_data['password'],
            email=serializer_data.get('email'),
            deficiencia=serializer_data.get('deficiencia', ''),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(usuario).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Detalhe do usuário',
    description='''
    Retorna os dados de um usuário específico.

    **Permissões:** O próprio usuário ou administradores.
    ''',
    responses={
        status.HTTP_200_OK: UsuarioSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class DetalheUsuarioView(IsOwnerOrAdminMixin, BasicRetrieveAPIView):
    """GET /identidade/usuarios/{pk}/"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuário obtido com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj


@extend_schema(
    tags=['Identidade'],
    summary='Atualizar dados do usuário',
    description='''
    Atualiza parcialmente os dados básicos do usuário (nome, e-mail, foto, deficiência).

    **Permissões:** O próprio usuário ou administradores.

    CPF não é alterável neste endpoint.
    ''',
    request=AtualizarUsuarioSerializer,
    responses={
        status.HTTP_200_OK: UsuarioSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AtualizarUsuarioView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    """PATCH /identidade/usuarios/{pk}/"""
    queryset = Usuario.objects.all()
    serializer_class = AtualizarUsuarioSerializer
    mensagem_sucesso = 'Usuário atualizado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_patch(self, serializer_data, request, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(self.object).data,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Desativar usuário',
    description='''
    Desativa um usuário do sistema (não remove o registro).

    **Permissões:** Apenas administradores.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Usuário desativado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Usuário já está inativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class DesativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário desativado com sucesso.'
    queryset = Usuario.objects.all()

    def do_action_post(self, serializer_data, request, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Identidade'],
    summary='Reativar usuário',
    description='''
    Reativa um usuário previamente desativado.

    **Permissões:** Apenas administradores.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Usuário reativado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Usuário já está ativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ReativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário reativado com sucesso.'
    queryset = Usuario.objects.all()

    def do_action_post(self, serializer_data, request, **kwargs):
        self.get_object().business.reativar()
