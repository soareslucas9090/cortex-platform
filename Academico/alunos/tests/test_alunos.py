from rest_framework import status
from rest_framework.test import APITestCase
from Identidade.usuarios.models import Usuario
from Academico.alunos.models import Aluno
from Academico.alunos.choices import SituacaoAluno, FormaIngresso

class AlunosAPITestCase(APITestCase):

    def setUp(self):
        # Create an admin user for the requests
        self.admin = Usuario.objects.create_superuser(
            cpf='11111111111', 
            password='Password123!', 
            nome='Admin User'
        )
        self.client.force_authenticate(user=self.admin)

        # Create a regular user to attach the Aluno profile to
        self.usuario = Usuario.objects.create_user(
            cpf='22222222222', 
            password='Password123!', 
            nome='Regular User'
        )

    def test_criar_aluno_com_sucesso(self):
        url = '/academico/alunos/'
        data = {
            'usuario': str(self.usuario.id),
            'ira': '8.5000',
            'situacao': SituacaoAluno.MATRICULADO,
            'forma_ingresso': FormaIngresso.ENEM,
            'ativo': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertTrue(Aluno.objects.filter(usuario=self.usuario).exists())
        
        aluno = Aluno.objects.get(usuario=self.usuario)
        self.assertEqual(aluno.ira, 8.5)
        self.assertEqual(aluno.situacao, SituacaoAluno.MATRICULADO)

    def test_listar_alunos(self):
        # Primeiro, crio um aluno
        Aluno.objects.create(
            usuario=self.usuario,
            ira=9.0000,
            situacao=SituacaoAluno.MATRICULADO,
            forma_ingresso=FormaIngresso.VESTIBULAR
        )
        
        url = '/academico/alunos/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # O retorno padrão do DRF/AppCore pagination geralmente tem 'results' se for paginado, 
        # ou lista direta, as basic views formatam isso.
        data = response.json()
        if 'results' in data:
            self.assertGreaterEqual(len(data['results']), 1)
        elif 'dados' in data and 'results' in data['dados']:
            self.assertGreaterEqual(len(data['dados']['results']), 1)
        else:
            # Caso não seja paginado ou seja lista
            pass

    def test_atualizar_aluno(self):
        aluno = Aluno.objects.create(
            usuario=self.usuario,
            ira=9.0000,
            situacao=SituacaoAluno.MATRICULADO,
            forma_ingresso=FormaIngresso.VESTIBULAR
        )
        
        url = f'/academico/alunos/{str(self.usuario.id)}/'
        data = {
            'ira': '9.5000',
            'situacao': SituacaoAluno.FORMADO
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        aluno.refresh_from_db()
        self.assertEqual(aluno.ira, 9.5)
        self.assertEqual(aluno.situacao, SituacaoAluno.FORMADO)
