from django.urls import path, include

app_name = 'pessoas-institucionais'

urlpatterns = [
    path('cargos/', include('PessoasInstitucionais.cargos.urls')),
    path('empresas/', include('PessoasInstitucionais.empresas_instituicoes.urls')),
    path('servidores/', include('PessoasInstitucionais.servidores.urls')),
    path('terceirizados/', include('PessoasInstitucionais.terceirizados.urls')),
]
