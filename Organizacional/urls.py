from django.urls import path, include

app_name = 'organizacional'

urlpatterns = [
    path('', include('Organizacional.setores.urls')),
    path('', include('Organizacional.funcoes.urls')),
    path('', include('Organizacional.vinculos.urls')),
]
