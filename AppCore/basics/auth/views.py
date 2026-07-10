"""
Views de Autenticação Base

Herda das views padrão do Simple JWT e adiciona documentação via drf-spectacular.
Projetos devem herdar estas views ou usar diretamente via include das urls.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from AppCore.basics.auth.serializers import BaseLoginSerializer, BaseMeSerializer


class BaseMeView(RetrieveAPIView):
    """
    Retorna os dados do usuário atualmente autenticado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BaseMeSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=['Auth'],
        summary='Dados do usuário logado',
        description='''
        Retorna as informações do usuário atual.

        **Permissões:** Qualquer usuário autenticado (L1–L3).
        ''',
        responses={
            status.HTTP_200_OK: BaseMeSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class BaseLoginView(TokenObtainPairView):
    """
    View de login base. Sobrescreva ``serializer_class`` para usar
    um serializer customizado com payload extra ou login por tipo.

    Exemplo:
        class LoginView(BaseLoginView):
            serializer_class = MeuLoginSerializer
    """

    serializer_class = BaseLoginSerializer

    @extend_schema(
        tags=['Auth'],
        summary='Login — obter tokens JWT',
        description='''
        Autentica o usuário e retorna os tokens de acesso (access) e renovação (refresh).

        **Permissões:** Público (AllowAny — não requer autenticação).

        O campo de identificação e o formato da requisição dependem do serializer
        configurado no projeto (ex: ``login`` com e-mail ou CPF ao usar ``BaseHybridLoginSerializer``).

        **Campos adicionais** podem aparecer na resposta dependendo do serializer configurado
        no projeto (ex: nome do usuário, perfis, campus).

        **Token de acesso**: válido por 1 dia (padrão).
        **Token de renovação**: válido por 7 dias (padrão).
        ''',
        responses={
            status.HTTP_200_OK: {'description': 'Login bem-sucedido. Retorna access e refresh tokens.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Credenciais inválidas.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AtualizarTokenView(TokenRefreshView):
    """
    Renova o token de acesso usando o token de renovação (refresh).
    """

    @extend_schema(
        tags=['Auth'],
        summary='Renovar token de acesso',
        description='''
        Usa o refresh token para emitir um novo access token sem precisar de nova autenticação.

        **Permissões:** Público (AllowAny — não requer autenticação).
        ''',
        responses={
            status.HTTP_200_OK: {'description': 'Novo access token gerado.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Refresh token inválido ou expirado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class VerificarTokenView(TokenVerifyView):
    """
    Verifica se um token JWT é válido e não expirou.
    """

    @extend_schema(
        tags=['Auth'],
        summary='Verificar validade do token',
        description='''
        Retorna 200 se o token for válido, 401 caso contrário.

        **Permissões:** Público (AllowAny — não requer autenticação).
        ''',
        responses={
            status.HTTP_200_OK: {'description': 'Token válido.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Token inválido ou expirado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
