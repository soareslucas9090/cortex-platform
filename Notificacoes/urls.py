from django.urls import include, path

app_name = 'notificacoes'

urlpatterns = [
    path('', include('Notificacoes.notificacoes.urls')),
]
