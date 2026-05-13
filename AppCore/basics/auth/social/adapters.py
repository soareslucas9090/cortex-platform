"""
Adapter do django-allauth para emissão de JWT após login social

Este adapter intercepta o fluxo de login social do allauth e, em vez de criar
uma sessão Django tradicional, emite tokens JWT (access + refresh) via Simple JWT.

==============================================================================
CONFIGURAÇÃO NECESSÁRIA NO SETTINGS.PY
==============================================================================

1. Adicione ao INSTALLED_APPS (descomente a seção allauth):
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

2. Adicione ao MIDDLEWARE:
    'allauth.account.middleware.AccountMiddleware',

3. Configure o adapter:
    SOCIALACCOUNT_ADAPTER = 'AppCore.basics.auth.social.adapters.JWTSocialAccountAdapter'

4. Configure o provider Google no SOCIALACCOUNT_PROVIDERS (já presente comentado no settings.py).

5. Adicione SITE_ID = 1 e rode:
    python manage.py migrate
    python manage.py createcachetable  # se usar cache de sites

==============================================================================
FLUXO DE AUTENTICAÇÃO SOCIAL
==============================================================================

Frontend (SPA/Mobile):
  1. Usuário clica em "Login com Google"
  2. Frontend abre o fluxo OAuth do Google e recebe o authorization_code ou access_token
  3. Frontend envia o token para POST /auth/social/google/
  4. Backend valida com Google, cria/recupera usuário via allauth
  5. JWTSocialAccountAdapter intercepta → emite JWT
  6. Resposta retorna access + refresh tokens (mesmo formato do login padrão)

==============================================================================
EXEMPLO DE OVERRIDE
==============================================================================

Para adicionar dados extras ao payload JWT após login social:

    from AppCore.basics.auth.social.adapters import JWTSocialAccountAdapter

    class MeuAdapter(JWTSocialAccountAdapter):
        def get_extra_jwt_payload(self, user, sociallogin) -> dict:
            return {
                'nome': user.nome,
                'is_admin': user.is_admin,
            }

    # settings.py
    SOCIALACCOUNT_ADAPTER = 'meuapp.adapters.MeuAdapter'
"""

try:
    from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
    from allauth.socialaccount.models import SocialLogin
    from rest_framework_simplejwt.tokens import RefreshToken

    class JWTSocialAccountAdapter(DefaultSocialAccountAdapter):
        """
        Adapter que emite tokens JWT após autenticação social bem-sucedida.

        Armazena os tokens no objeto sociallogin para que a view possa
        retorná-los na resposta HTTP sem criar sessão Django.
        """

        def get_extra_jwt_payload(self, user, sociallogin: SocialLogin) -> dict:
            """
            Hook para adicionar dados extras ao payload JWT após login social.

            Sobrescreva este método para incluir dados do usuário na resposta,
            seguindo o mesmo padrão de BaseLoginSerializer.get_extra_payload().

            Args:
                user: Instância do usuário autenticado/criado.
                sociallogin: Objeto SocialLogin do allauth com dados da conta social.

            Returns:
                dict com dados extras para incluir na resposta.
            """
            return {}

        def save_user(self, request, sociallogin: SocialLogin, form=None):
            """Persiste o usuário e anexa os tokens JWT ao sociallogin."""
            user = super().save_user(request, sociallogin, form)
            self._attach_jwt_tokens(user, sociallogin)
            return user

        def _attach_jwt_tokens(self, user, sociallogin: SocialLogin) -> None:
            """Gera os tokens JWT e os anexa ao objeto sociallogin."""
            refresh = RefreshToken.for_user(user)
            extra = self.get_extra_jwt_payload(user, sociallogin)

            sociallogin._jwt_tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                **extra,
            }

except ImportError:
    # django-allauth não instalado — adapter não disponível
    # Instale com: pip install django-allauth dj-rest-auth
    class JWTSocialAccountAdapter:  # type: ignore[no-redef]
        """
        Adapter não disponível: django-allauth não está instalado.
        Execute: pip install django-allauth dj-rest-auth
        """
        pass
