from django.urls import path, include

app_name = 'auth'

urlpatterns = [
    path('token_jwt/', include('Auth.auth.urls')),
    # Login social desabilitado — habilite quando configurar allauth em INSTALLED_APPS:
    # path('social/', include('AppCore.basics.auth.social.urls')),
]
