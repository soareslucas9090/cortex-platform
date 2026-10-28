from django.urls import include, path

app_name = 'acesso_campus'

urlpatterns = [
    path('', include('AcessoCampus.solicitacoes.urls')),
]
