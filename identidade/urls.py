from django.urls import path, include

app_name = 'identidade'

urlpatterns = [
    path('', include('Identidade.identidade.urls')),
]
