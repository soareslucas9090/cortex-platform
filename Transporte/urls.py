from django.urls import path, include

app_name = 'transporte'

urlpatterns = [
    path('', include('Transporte.percursos.urls')),
]
