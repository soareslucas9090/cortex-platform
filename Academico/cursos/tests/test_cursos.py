from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from Academico.cursos.models import Curso
from Academico.cursos.choices import TurnoCurso


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


def criar_curso(nome='Sistemas de Informação', codigo='SI-001', turno=TurnoCurso.NOTURNO):
    return Curso.objects.create(nome=nome, codigo_curso=codigo, turno=turno)


class CursoBusinessTestCase(APITestCase):

    def test_criar_curso_sucesso(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        self.assertEqual(curso.nome, 'Sistemas de Informação')
        self.assertEqual(curso.codigo_curso, 'SI-001')
        self.assertTrue(curso.ativo)

    def test_criar_curso_codigo_duplicado(self):
        Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(nome='Sistemas II', codigo_curso='SI-001')
        self.assertIn('Já existe um curso cadastrado com esse código', str(ctx.exception))

    def test_criar_curso_com_turno(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação', codigo_curso='SI-001', turno=TurnoCurso.NOTURNO
        )
        self.assertEqual(curso.turno, TurnoCurso.NOTURNO)

    def test_atualizar_dados_sucesso(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso.business.atualizar_dados({'nome': 'Ciência da Computação'})
        curso.refresh_from_db()
        self.assertEqual(curso.nome, 'Ciência da Computação')

    def test_atualizar_dados_codigo_duplicado(self):
        Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso2 = Curso().business.criar_curso(nome='Engenharia de Software', codigo_curso='ES-001')
        with self.assertRaises(BusinessRuleException):
            curso2.business.atualizar_dados({'codigo_curso': 'SI-001'})

    def test_atualizar_dados_mesmo_codigo(self):
        """Deve permitir atualizar sem mudar o código (excluindo o próprio da verificação)."""
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso.business.atualizar_dados({'nome': 'Sistemas de Informação Atualizado', 'codigo_curso': 'SI-001'})
        curso.refresh_from_db()
        self.assertEqual(curso.nome, 'Sistemas de Informação Atualizado')

    def test_desativar_curso_sucesso(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso.business.desativar()
        curso.refresh_from_db()
        self.assertFalse(curso.ativo)

    def test_desativar_curso_ja_inativo(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso.business.desativar()
        with self.assertRaises(BusinessRuleException):
            curso.business.desativar()

    def test_reativar_curso_sucesso(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        curso.business.desativar()
        curso.business.reativar()
        curso.refresh_from_db()
        self.assertTrue(curso.ativo)

    def test_reativar_curso_ja_ativo(self):
        curso = Curso().business.criar_curso(nome='Sistemas de Informação', codigo_curso='SI-001')
        with self.assertRaises(BusinessRuleException):
            curso.business.reativar()


class CursosAPITestCase(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.curso = criar_curso()

    def test_listar_cursos(self):
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_listar_cursos_filtrar_ativo(self):
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'ativo': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_listar_cursos_filtrar_inativo(self):
        self.curso.business.desativar()
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'ativo': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_listar_cursos_filtrar_turno(self):
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'turno': TurnoCurso.NOTURNO})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_criar_curso(self):
        url = reverse('academico:curso-list')
        payload = {'nome': 'Engenharia de Software', 'codigo_curso': 'ES-001'}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Curso.objects.filter(codigo_curso='ES-001').exists())

    def test_criar_curso_codigo_duplicado(self):
        url = reverse('academico:curso-list')
        payload = {'nome': 'Outro Curso', 'codigo_curso': 'SI-001'}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhar_curso(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dados']['codigo_curso'], 'SI-001')

    def test_atualizar_curso(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        payload = {'nome': 'Sistemas de Informação - Atualizado'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.nome, 'Sistemas de Informação - Atualizado')

    def test_desativar_curso(self):
        url = reverse('academico:curso-desativar', kwargs={'pk': self.curso.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertFalse(self.curso.ativo)

    def test_reativar_curso(self):
        self.curso.business.desativar()
        url = reverse('academico:curso-reativar', kwargs={'pk': self.curso.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertTrue(self.curso.ativo)

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nao_admin_retorna_403(self):
        usuario_comum = Usuario.objects.create_user(cpf='00000000002', password='Senha@123', nome='Comum')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario_comum)}')
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
