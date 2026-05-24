from django.urls import path, include

app_name = 'academico'

urlpatterns = [
    path('cursos/', include('Academico.cursos.urls')),
    path('alunos/', include('Academico.alunos.urls')),
    path('aluno-cursos/', include('Academico.aluno_cursos.urls')),
]
