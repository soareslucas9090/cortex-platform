from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Identidade.enderecos.models import Endereco


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


PAYLOAD_ENDERECO = {
    'logradouro': 'Rua das Flores',
    'numero': '100',
    'bairro': 'Centro',
    'cep': '60000000',
    'cidade': 'Fortaleza',
    'estado': 'CE',
}


class ObterEnderecoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.endereco = Endereco.objects.create(usuario=self.usuario, **PAYLOAD_ENDERECO)
        self.url = reverse('identidade:endereco', kwargs={'usuario_pk': self.usuario.pk})

    def test_admin_obtem_endereco_de_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['cidade'], 'Fortaleza')

    def test_proprio_usuario_obtem_seu_endereco(self):
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

    def test_usuario_sem_endereco_retorna_404(self):
        usuario_sem_endereco = criar_usuario('00000000004', nome='Sem Endereço')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:endereco', kwargs={'usuario_pk': usuario_sem_endereco.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:endereco', kwargs={'usuario_pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class SalvarEnderecoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:endereco', kwargs={'usuario_pk': self.usuario.pk})

    def test_admin_salva_endereco_de_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.put(self.url, PAYLOAD_ENDERECO)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_proprio_usuario_salva_seu_endereco(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.put(self.url, PAYLOAD_ENDERECO)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_atualiza_endereco_existente(self):
        Endereco.objects.create(usuario=self.usuario, **PAYLOAD_ENDERECO)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        payload_novo = {**PAYLOAD_ENDERECO, 'cidade': 'Caucaia'}
        resposta = self.client.put(self.url, payload_novo)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.endereco.cidade, 'Caucaia')

    def test_outro_usuario_nao_pode_salvar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.put(self.url, PAYLOAD_ENDERECO)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.put(self.url, PAYLOAD_ENDERECO)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cep_invalido_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        payload_invalido = {**PAYLOAD_ENDERECO, 'cep': '123'}
        resposta = self.client.put(self.url, payload_invalido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_estado_invalido_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        payload_invalido = {**PAYLOAD_ENDERECO, 'estado': 'XX'}
        resposta = self.client.put(self.url, payload_invalido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:endereco', kwargs={'usuario_pk': 99999})
        resposta = self.client.put(url, PAYLOAD_ENDERECO)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
