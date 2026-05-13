"""
Views de Autenticação do Projeto

Herdam de BaseLoginView do AppCore. Sobrescreva serializer_class aqui
para usar o LoginSerializer customizado deste projeto.
"""

from drf_spectacular.utils import extend_schema

from rest_framework import status

from AppCore.basics.auth.views import (
    BaseLoginView,
    AtualizarTokenView,
    VerificarTokenView,
)

from Auth.auth.serializers import LoginSerializer, LoginInputSerializer, LoginResponseSerializer


class LoginView(BaseLoginView):
    """
    Endpoint de login do projeto.

    Troque serializer_class por um serializer customizado se precisar de
    dados extras na resposta (ex: nome, perfis) ou login por tipo de usuário.
    """

    serializer_class = LoginSerializer

    @extend_schema(
        tags=['Auth'],
        summary='Login',
        request=LoginInputSerializer,
        responses={
            status.HTTP_200_OK: LoginResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Credenciais inválidas.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# Re-exporta para usar nas urls sem import adicional
__all__ = ['LoginView', 'AtualizarTokenView', 'VerificarTokenView']
