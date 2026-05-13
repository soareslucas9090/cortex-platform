from django.urls import path, include

app_name = 'auth'

urlpatterns = [
    path('token_jwt/', include('Auth.auth.urls')),
    path('social/', include('AppCore.basics.auth.social.urls')),
]
