from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import ListarStrikesView

urlpatterns = [
    path('strikes/', roteador_por_metodo(GET=ListarStrikesView), name='strike-list'),
]
