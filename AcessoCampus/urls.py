from django.urls import include, path

app_name = 'acesso_campus'

urlpatterns = [
    path('', include('AcessoCampus.tipos.urls')),
    path('', include('AcessoCampus.solicitacoes.urls')),
    path('portaria/', include('AcessoCampus.eventos.urls')),
]
