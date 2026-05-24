from django.urls import path, include

app_name = 'pessoas-institucionais'

urlpatterns = [
    path('', include('PessoasInstitucionais.cargos.urls')),
    path('', include('PessoasInstitucionais.empresas_instituicoes.urls')),
    path('', include('PessoasInstitucionais.servidores.urls')),
    path('', include('PessoasInstitucionais.terceirizados.urls')),
]
