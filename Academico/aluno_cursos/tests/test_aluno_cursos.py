from rest_framework import status
from rest_framework.test import APITestCase

from Identidade.usuarios.models import Usuario
from Academico.alunos.models import Aluno
from Academico.cursos.models import Curso
from Academico.aluno_cursos.models import AlunoCurso


def criar_usuario(cpf, nome):
    return Usuario.objects.create_user(cpf=cpf, password='Password123!', nome=nome)


def criar_aluno(usuario):
    return Aluno.objects.create(usuario=usuario)


def criar_curso(nome, codigo):
    return Curso.objects.create(nome=nome, codigo_curso=codigo)


class AlunoCursoAPITestCase(APITestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            cpf='00000000000',
            password='Password123!',
            nome='Admin',
        )
        self.client.force_authenticate(user=self.admin)

        self.usuario = criar_usuario('11111111111', 'João Silva')
        self.aluno = criar_aluno(self.usuario)
        self.curso = criar_curso('Sistemas de Informação', 'SI001')

    def test_criar_vinculo_com_sucesso(self):
        url = '/academico/aluno-cursos/'
        data = {'aluno': self.aluno.pk, 'curso': self.curso.pk}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertTrue(
            AlunoCurso.objects.filter(aluno=self.aluno, curso=self.curso).exists()
        )

    def test_nao_permite_vinculo_ativo_duplicado(self):
        AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = '/academico/aluno-cursos/'
        data = {'aluno': self.aluno.pk, 'curso': self.curso.pk}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())

    def test_permite_novo_vinculo_apos_encerrar_anterior(self):
        vinculo = AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso, ativo=False)

        url = '/academico/aluno-cursos/'
        data = {'aluno': self.aluno.pk, 'curso': self.curso.pk}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    def test_listar_vinculos(self):
        AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = '/academico/aluno-cursos/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detalhar_vinculo(self):
        vinculo = AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = f'/academico/aluno-cursos/{vinculo.pk}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_atualizar_vinculo(self):
        vinculo = AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = f'/academico/aluno-cursos/{vinculo.pk}/'
        data = {'ano_conclusao': 2026}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        vinculo.refresh_from_db()
        self.assertEqual(vinculo.ano_conclusao, 2026)

    def test_encerrar_vinculo(self):
        vinculo = AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = f'/academico/aluno-cursos/{vinculo.pk}/encerrar/'
        data = {'ano_conclusao': 2025}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        vinculo.refresh_from_db()
        self.assertFalse(vinculo.ativo)
        self.assertEqual(vinculo.ano_conclusao, 2025)

    def test_nao_permite_encerrar_vinculo_ja_encerrado(self):
        vinculo = AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso, ativo=False)

        url = f'/academico/aluno-cursos/{vinculo.pk}/encerrar/'
        data = {'ano_conclusao': 2025}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())

    def test_filtrar_por_aluno(self):
        AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)

        url = f'/academico/aluno-cursos/?aluno={self.aluno.pk}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
