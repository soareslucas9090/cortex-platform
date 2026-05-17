"""
Views de Autenticação Base

Herda das views padrão do Simple JWT e adiciona documentação via drf-spectacular.
Projetos devem herdar estas views ou usar diretamente via include das urls.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from AppCore.basics.auth.serializers import BaseLoginSerializer


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

        O campo de identificação padrão é definido pelo serializer configurado no projeto.
        Projetos com ``BaseHybridLoginSerializer`` aceitam ``login`` como e-mail ou CPF.

        **Campos adicionais** podem aparecer na resposta dependendo do serializer configurado
        no projeto (ex: nome do usuário, perfis, campus).

        **Token de acesso**: válido por 30 minutos (padrão).
        **Token de renovação**: válido por 7 dias (padrão).
        ''',
        responses={
            status.HTTP_200_OK: {'description': 'Login bem-sucedido. Retorna access e refresh tokens.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Credenciais inválidas.'},
        },
        examples=[
            OpenApiExample(
                'Login com e-mail',
                value={'login': 'usuario@email.com', 'password': 'Senha@123'},
                request_only=True,
            ),
            OpenApiExample(
                'Login com CPF (com máscara)',
                value={'login': '123.456.789-01', 'password': 'Senha@123'},
                request_only=True,
            ),
            OpenApiExample(
                'Login com CPF (sem máscara)',
                value={'login': '12345678901', 'password': 'Senha@123'},
                request_only=True,
            ),
        ],
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
        description='Usa o refresh token para emitir um novo access token sem precisar de nova autenticação.',
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
        description='Retorna 200 se o token for válido, 401 caso contrário.',
        responses={
            status.HTTP_200_OK: {'description': 'Token válido.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Token inválido ou expirado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
