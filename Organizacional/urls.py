from django.urls import path, include

app_name = 'organizacional'

urlpatterns = [
    path('', include('Organizacional.organizacional.urls')),
]
