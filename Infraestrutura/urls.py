from django.urls import path, include

app_name = 'infraestrutura'

urlpatterns = [
    path('', include('Infraestrutura.blocos.urls')),
    path('', include('Infraestrutura.salas.urls')),
    path('', include('Infraestrutura.recursos.urls')),
    path('', include('Infraestrutura.autorizacoes.urls')),
]
