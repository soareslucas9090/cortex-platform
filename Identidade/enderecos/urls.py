from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import ObterEnderecoView, SalvarEnderecoView

urlpatterns = [
    path(
        'usuarios/<int:usuario_pk>/endereco/',
        roteador_por_metodo(GET=ObterEnderecoView, PUT=SalvarEnderecoView),
        name='endereco',
    ),
]
