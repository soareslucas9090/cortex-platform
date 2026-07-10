"""
Views de Login Social (Google via django-allauth)

==============================================================================
PRÉ-REQUISITOS
==============================================================================

1. Instale as dependências:
       pip install django-allauth dj-rest-auth

2. Configure o INSTALLED_APPS e MIDDLEWARE (veja adapters.py).

3. Configure SOCIALACCOUNT_ADAPTER no settings.py:
       SOCIALACCOUNT_ADAPTER = 'AppCore.basics.auth.social.adapters.JWTSocialAccountAdapter'
       (ou o adapter do seu projeto que herda de JWTSocialAccountAdapter)

4. Inclua as URLs no seu urls.py:
       from AppCore.basics.auth.social.urls import urlpatterns as social_urls

==============================================================================
FLUXO DO FRONTEND
==============================================================================

POST /auth/social/google/
  Body: {"access_token": "<token_google>"}
  Response: {"access": "...", "refresh": "..."}

O frontend deve primeiro obter o access_token do Google via SDK do Google
(ex: Google Identity Services / Google Sign-In) e então enviar para este endpoint.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from AppCore.basics.auth.social.serializers import (
    SocialTokenInputSerializer,
    SocialTokenResponseSerializer,
)
from AppCore.basics.mixins.mixins import AllowAnyMixin


try:
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.client import OAuth2Client

    _ALLAUTH_AVAILABLE = True
except ImportError:
    _ALLAUTH_AVAILABLE = False


class GoogleLoginView(AllowAnyMixin, APIView):
    """
    Autentica o usuário via Google OAuth2 e retorna tokens JWT.

    Requer que o access_token do Google seja obtido pelo cliente (SPA/mobile)
    e enviado neste endpoint. O servidor valida o token com o Google, cria
    ou recupera o usuário local via allauth, e emite JWT.
    """

    @extend_schema(
        tags=['Auth'],
        summary='Login com Google',
        description='''
        Autentica via Google OAuth2 e retorna tokens JWT (access + refresh).

        **Pré-requisito no cliente**: Obtenha o ``access_token`` do Google usando o
        Google Identity Services SDK antes de chamar este endpoint.

        **Permissões:** Público (AllowAny — não requer autenticação prévia).
        ''',
        request=SocialTokenInputSerializer,
        responses={
            status.HTTP_200_OK: SocialTokenResponseSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Token inválido ou ausente.'},
            status.HTTP_503_SERVICE_UNAVAILABLE: {'description': 'django-allauth não configurado.'},
        },
        examples=[],
    )
    def post(self, request, *args, **kwargs):
        if not _ALLAUTH_AVAILABLE:
            return Response(
                {
                    'status': 'error',
                    'detail': 'Login social não configurado. Instale django-allauth e dj-rest-auth.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        input_serializer = SocialTokenInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        access_token = input_serializer.validated_data.get('access_token')
        code = input_serializer.validated_data.get('code')

        try:
            adapter = GoogleOAuth2Adapter(request)
            client_class = OAuth2Client

            # Obtém o token do provider e conecta ao usuário local via allauth
            token = adapter.parse_token({'access_token': access_token} if access_token else {'code': code})
            login = adapter.complete_login(request, app=adapter.get_app(request), token=token, response=None)
            login.token = token
            login.state = {}

            from allauth.socialaccount.helpers import complete_social_login
            response = complete_social_login(request, login)

            # JWTSocialAccountAdapter anexou os tokens ao sociallogin
            jwt_tokens = getattr(login, '_jwt_tokens', None)

            if not jwt_tokens:
                return Response(
                    {'status': 'error', 'detail': 'Não foi possível completar a autenticação social.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(jwt_tokens, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Erro no login social Google: %s', e)
            return Response(
                {'status': 'error', 'detail': 'Token do Google inválido ou expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
