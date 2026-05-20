from django.urls import path, include

app_name = 'identidade'

urlpatterns = [
    path('', include('Identidade.usuarios.urls')),
    path('', include('Identidade.contatos.urls')),
    path('', include('Identidade.enderecos.urls')),
    path('', include('Identidade.matriculas.urls')),
]
