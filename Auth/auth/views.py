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
    BaseMeView,
)

from Auth.auth.serializers import (
    LoginSerializer,
    LoginInputSerializer,
    LoginResponseSerializer,
    ProjectMeSerializer,
)


class LoginView(BaseLoginView):
    """
    Endpoint de login do projeto.

    Troque serializer_class por um serializer customizado se precisar de
    dados extras na resposta (ex: nome, perfis) ou login por tipo de usuário.
    """

    serializer_class = LoginSerializer

    @extend_schema(
        tags=['Auth'],
        summary='Login — obter tokens JWT',
        description='''
        Autentica o usuário e retorna os tokens de acesso (access) e renovação (refresh).

        **Permissões:** Público (AllowAny — não requer autenticação).

        O campo ``login`` aceita **e-mail** ou **CPF** (com ou sem máscara).

        **Exemplos de identificador:**
        - E-mail: `usuario@email.com`
        - CPF sem máscara: `12345678901`
        - CPF com máscara: `123.456.789-01`

        **Token de acesso:** válido por 30 minutos.
        **Token de renovação:** válido por 7 dias.

        Em caso de falha, a resposta é sempre genérica e não revela
        o motivo específico (usuário inexistente, senha incorreta ou inativo).
        ''',
        request=LoginInputSerializer,
        responses={
            status.HTTP_200_OK: LoginResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Credenciais inválidas.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(BaseMeView):
    """
    Retorna os dados do usuário atualmente autenticado, incluindo permissões do frontend.
    """
    serializer_class = ProjectMeSerializer

    @extend_schema(
        tags=['Auth'],
        summary='Dados do usuário logado',
        description='''
        Retorna as informações do usuário atual, incluindo suas permissões.

        **Permissões:** Qualquer usuário autenticado (L1–L3).
        ''',
        responses={
            status.HTTP_200_OK: ProjectMeSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# Re-exporta para usar nas urls sem import adicional
__all__ = ['LoginView', 'AtualizarTokenView', 'VerificarTokenView', 'MeView']
