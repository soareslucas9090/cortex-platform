import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema

from AppCore.basics.mixins.mixins import IsOwnerOrAdminMixin
from AppCore.basics.views.basic_views import BasicPutAPIView, BasicRetrieveAPIView
from AppCore.core.exceptions.exceptions import NotFoundException

from .models import Endereco
from .serializers import EnderecoInputSerializer, EnderecoSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Identidade'],
    summary='Obter endereço do usuário',
    description='''
    Retorna o endereço cadastrado do usuário.

    **Permissões:** O próprio usuário ou administradores.

    Retorna 404 se o endereço ainda não foi cadastrado.
    ''',
    responses={
        status.HTTP_200_OK: EnderecoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Endereço não cadastrado.'},
    },
)
class ObterEnderecoView(IsOwnerOrAdminMixin, BasicRetrieveAPIView):
    """GET /identidade/usuarios/{usuario_pk}/endereco/"""
    serializer_class = EnderecoSerializer
    mensagem_sucesso = 'Endereço obtido com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def get_object(self):
        from django.shortcuts import get_object_or_404
        from Identidade.usuarios.models import Usuario
        usuario = get_object_or_404(Usuario, pk=self.kwargs['usuario_pk'])
        try:
            endereco = usuario.endereco
        except Endereco.DoesNotExist:
            raise NotFoundException('Endereço não cadastrado para este usuário.')
        self.check_object_permissions(self.request, endereco)
        return endereco


@extend_schema(
    tags=['Identidade'],
    summary='Salvar endereço do usuário',
    description='''
    Cria ou atualiza o endereço do usuário (operação idempotente).

    **Permissões:** O próprio usuário ou administradores.
    ''',
    request=EnderecoInputSerializer,
    responses={
        status.HTTP_200_OK: EnderecoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class SalvarEnderecoView(IsOwnerOrAdminMixin, BasicPutAPIView):
    """PUT /identidade/usuarios/{usuario_pk}/endereco/"""
    serializer_class = EnderecoInputSerializer
    mensagem_sucesso = 'Endereço salvo com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def get_object(self):
        from django.shortcuts import get_object_or_404
        from Identidade.usuarios.models import Usuario
        usuario = get_object_or_404(Usuario, pk=self.kwargs['usuario_pk'])
        self.check_object_permissions(self.request, usuario)
        return usuario

    def do_action_put(self, serializer_data, request):
        endereco = self.object.business.salvar_endereco(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EnderecoSerializer(endereco).data,
        }
