"""
URLs para login social.

Inclua no seu urls.py de projeto:

    from django.urls import path, include

    urlpatterns = [
        path('auth/social/', include('AppCore.basics.auth.social.urls')),
        # ou junto com as auth urls:
        path('auth/token_jwt/', include('Auth.auth.urls')),
    ]
"""

from django.urls import path

from AppCore.basics.auth.social.views import GoogleLoginView

app_name = 'appcore-auth-social'

urlpatterns = [
    path('google/', GoogleLoginView.as_view(), name='google-login'),
]
