import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsOwnerOrAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
)

from .models import Contato
from .serializers import ContatoInputSerializer, ContatoSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Identidade'],
    summary='Listar contatos do usuário',
    description='''
    Retorna a lista de contatos de um usuário específico.

    **Permissões:** O próprio usuário ou administradores.

    **Query params:**
    - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.

    **Segurança:** os resultados já estão restritos ao usuário da URL — query params
    apenas reduzem o conjunto, nunca expandem o acesso.
    ''',
    parameters=[
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: ContatoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ListarContatosView(IsOwnerOrAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/{usuario_pk}/contatos/"""
    serializer_class = ContatoSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Contatos listados com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def validate_get(self, request, *args, **kwargs):
        from Identidade.usuarios.models import Usuario
        Usuario.objects.get(pk=self.kwargs['usuario_pk'])
        self.verificar_acesso_usuario(request, self.kwargs['usuario_pk'])

    def get_queryset(self):
        return Contato.objects.filter(usuario_id=self.kwargs['usuario_pk'])


@extend_schema(
    tags=['Identidade'],
    summary='Adicionar contato ao usuário',
    description='''
    Adiciona um novo contato (e-mail acadêmico, e-mail pessoal ou telefone) ao usuário.

    **Permissões:** O próprio usuário ou administradores.

    Informe ao menos um dos campos de contato.
    ''',
    request=ContatoInputSerializer,
    responses={
        status.HTTP_201_CREATED: ContatoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AdicionarContatoView(IsOwnerOrAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{usuario_pk}/contatos/"""
    serializer_class = ContatoInputSerializer
    mensagem_sucesso = 'Contato adicionado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_post(self, serializer_data, request, **kwargs):
        from django.shortcuts import get_object_or_404
        from Identidade.usuarios.models import Usuario
        self.verificar_acesso_usuario(request, self.kwargs['usuario_pk'])
        usuario = get_object_or_404(Usuario, pk=self.kwargs['usuario_pk'])
        contato = usuario.business.adicionar_contato(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ContatoSerializer(contato).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Atualizar contato',
    description='''
    Atualiza parcialmente os dados de um contato do usuário.

    **Permissões:** O próprio usuário ou administradores.
    ''',
    request=ContatoInputSerializer,
    responses={
        status.HTTP_200_OK: ContatoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Contato não encontrado.'},
    },
)
class AtualizarContatoView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    """PATCH /identidade/usuarios/{usuario_pk}/contatos/{pk}/"""
    serializer_class = ContatoInputSerializer
    mensagem_sucesso = 'Contato atualizado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def get_queryset(self):
        return Contato.objects.filter(usuario_id=self.kwargs['usuario_pk'])

    def do_action_patch(self, serializer_data, request, **kwargs):
        self.object.business.atualizar_contato(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': ContatoSerializer(self.object).data,
        }
