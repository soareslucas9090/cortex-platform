from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Identidade.matriculas.models import Matricula
from Identidade.matriculas.choices import SituacaoMatricula


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False):
    return Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
        is_admin=is_admin,
    )


class ListarMatriculasViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.matricula_ativa = Matricula.objects.create(
            usuario=self.usuario,
            matricula='MAT001',
            situacao=SituacaoMatricula.ATIVA,
        )
        self.matricula_inativa = Matricula.objects.create(
            usuario=self.usuario,
            matricula='MAT002',
            situacao=SituacaoMatricula.INATIVA,
        )
        self.url = reverse('identidade:matriculas', kwargs={'usuario_pk': self.usuario.pk})

    def test_admin_lista_matriculas_de_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('dados', resposta.data)

    def test_proprio_usuario_lista_suas_matriculas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_outro_usuario_nao_tem_acesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_situacao_ativa_retorna_somente_ativas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'situacao': SituacaoMatricula.ATIVA})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        numeros = [m['matricula'] for m in resposta.data['dados']]
        self.assertIn('MAT001', numeros)
        self.assertNotIn('MAT002', numeros)

    def test_filtro_situacao_invalida_e_ignorado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'situacao': 99})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:matriculas', kwargs={'usuario_pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AdicionarMatriculaViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.url = reverse('identidade:matriculas', kwargs={'usuario_pk': self.usuario.pk})
        self.payload_valido = {'matricula': 'MAT2024001'}

    def test_admin_adiciona_matricula_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_usuario_comum_nao_pode_adicionar_matricula(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_numero_matricula_duplicado_retorna_400(self):
        Matricula.objects.create(
            usuario=self.usuario,
            matricula='MAT2024001',
            situacao=SituacaoMatricula.ATIVA,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:matriculas', kwargs={'usuario_pk': 99999})
        resposta = self.client.post(url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class DesativarMatriculaViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.matricula = Matricula.objects.create(
            usuario=self.usuario,
            matricula='MAT001',
            situacao=SituacaoMatricula.ATIVA,
        )
        self.url = reverse(
            'identidade:matricula-desativar',
            kwargs={'usuario_pk': self.usuario.pk, 'pk': self.matricula.pk},
        )

    def test_admin_desativa_matricula_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.matricula.refresh_from_db()
        self.assertEqual(self.matricula.situacao, SituacaoMatricula.INATIVA)

    def test_usuario_comum_nao_pode_desativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_matricula_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'identidade:matricula-desativar',
            kwargs={'usuario_pk': self.usuario.pk, 'pk': 99999},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_matricula_de_outro_usuario_retorna_404(self):
        outro = criar_usuario('00000000004', nome='Outro')
        matricula_outro = Matricula.objects.create(
            usuario=outro,
            matricula='MAT999',
            situacao=SituacaoMatricula.ATIVA,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'identidade:matricula-desativar',
            kwargs={'usuario_pk': self.usuario.pk, 'pk': matricula_outro.pk},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
