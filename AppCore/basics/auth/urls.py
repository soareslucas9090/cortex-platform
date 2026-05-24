"""
URLs de Autenticação Base

Use via include() no seu urls.py de projeto:

    from django.urls import path, include

    urlpatterns = [
        path('auth/token_jwt/', include('AppCore.basics.auth.urls')),
    ]

Ou no thin app Auth/:

    path('auth/', include('Auth.auth.urls'))
"""

from django.urls import path

from AppCore.basics.auth.views import BaseLoginView, AtualizarTokenView, VerificarTokenView, MeView

app_name = 'appcore-auth'

urlpatterns = [
    path('', BaseLoginView.as_view(), name='login'),
    path('refresh/', AtualizarTokenView.as_view(), name='token-refresh'),
    path('verify/', VerificarTokenView.as_view(), name='token-verify'),
    path('me/', MeView.as_view(), name='me'),
]
