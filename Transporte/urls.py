from django.urls import path, include

app_name = 'transporte'

urlpatterns = [
    path('', include('Transporte.percursos.urls')),
    path('', include('Transporte.rotas.urls')),
    path('', include('Transporte.execucoes_rotas.urls')),
    path('', include('Transporte.tickets.urls')),
    path('', include('Transporte.strikes.urls')),
    path('', include('Transporte.justificativas.urls')),
    path('', include('Transporte.entradas_sem_ticket.urls')),
    path('', include('Transporte.bloqueios.urls')),
]
