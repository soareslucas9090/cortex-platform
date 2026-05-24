from django.urls import path, include

app_name = 'academico'

urlpatterns = [
    path('', include('Academico.cursos.urls')),
    path('', include('Academico.alunos.urls')),
    path('', include('Academico.aluno_cursos.urls')),
]
