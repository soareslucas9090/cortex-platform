from django.urls import path

from Auth.auth.views import LoginView, AtualizarTokenView, VerificarTokenView, MeView

app_name = 'token-jwt'

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('refresh/', AtualizarTokenView.as_view(), name='token-refresh'),
    path('verify/', VerificarTokenView.as_view(), name='token-verify'),
    path('me/', MeView.as_view(), name='me'),
]
