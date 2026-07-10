from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Identidade.contatos.models import Contato


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


class ListarContatosViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.contato = Contato.objects.create(
            usuario=self.usuario,
            email_pessoal='pessoal@exemplo.com',
        )
        self.url = reverse('identidade:contatos', kwargs={'usuario_pk': self.usuario.pk})

    def test_admin_lista_contatos_de_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('dados', resposta.data)

    def test_proprio_usuario_lista_seus_contatos(self):
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

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:contatos', kwargs={'usuario_pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_servidor_l2_pode_ler_contatos_de_outro_usuario(self):
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.servidores.models import Servidor

        cargo = Cargo.objects.create(nome='Cargo L2')
        servidor_user = criar_usuario('44444444444', nome='Servidor L2')
        Servidor.objects.create(usuario=servidor_user, cargo=cargo, categoria=1, ativo=True)
        token_servidor = obter_tokens(servidor_user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_servidor}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


class AdicionarContatoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:contatos', kwargs={'usuario_pk': self.usuario.pk})
        self.payload_valido = {'email_pessoal': 'pessoal@exemplo.com'}

    def test_admin_adiciona_contato_a_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_proprio_usuario_adiciona_seu_contato(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url, {'telefone': '85999999999'})
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_outro_usuario_nao_pode_adicionar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payload_sem_campos_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url, {})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:contatos', kwargs={'usuario_pk': 99999})
        resposta = self.client.post(url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_servidor_l2_nao_pode_adicionar_contato_de_outro_usuario(self):
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.servidores.models import Servidor

        cargo = Cargo.objects.create(nome='Cargo L2 Post')
        servidor_user = criar_usuario('55555555555', nome='Servidor L2 Post')
        Servidor.objects.create(usuario=servidor_user, cargo=cargo, categoria=1, ativo=True)
        token_servidor = obter_tokens(servidor_user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_servidor}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)


class AtualizarContatoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.contato = Contato.objects.create(
            usuario=self.usuario,
            email_pessoal='original@exemplo.com',
        )
        self.url = reverse(
            'identidade:contato-detalhe',
            kwargs={'usuario_pk': self.usuario.pk, 'pk': self.contato.pk},
        )

    def test_admin_atualiza_contato_de_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'email_pessoal': 'novo@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['email_pessoal'], 'novo@exemplo.com')

    def test_proprio_usuario_atualiza_seu_contato(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'telefone': '85988888888'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_outro_usuario_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.patch(self.url, {'email_pessoal': 'invasor@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'email_pessoal': 'teste@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_contato_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'identidade:contato-detalhe',
            kwargs={'usuario_pk': self.usuario.pk, 'pk': 99999},
        )
        resposta = self.client.patch(url, {'email_pessoal': 'teste@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
