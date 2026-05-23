from django.urls import path, include

app_name = 'academico'

urlpatterns = [
    path('cursos/', include('Academico.cursos.urls')),
    path('alunos/', include('Academico.alunos.urls')),
]
