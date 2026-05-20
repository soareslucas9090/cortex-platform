from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False, **kwargs):
    """Cria e retorna um Usuario para uso nos testes."""
    usuario = Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
        is_admin=is_admin,
        **kwargs,
    )
    return usuario


class ListarUsuariosViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario_comum = criar_usuario('00000000002', nome='Comum')
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.usuario_comum)
        self.url = reverse('identidade:usuarios')

    def test_admin_lista_usuarios_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], 'success')
        self.assertIn('dados', resposta.data)

    def test_usuario_comum_nao_pode_listar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_ativo_true_retorna_somente_ativos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        self.usuario_comum.ativo = False
        self.usuario_comum.save()
        resposta = self.client.get(self.url, {'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertNotIn(self.usuario_comum.cpf, cpfs)

    def test_filtro_ativo_false_retorna_somente_inativos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        self.usuario_comum.ativo = False
        self.usuario_comum.save()
        resposta = self.client.get(self.url, {'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertIn(self.usuario_comum.cpf, cpfs)

    def test_filtro_ativo_invalido_e_ignorado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'invalido'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


class CriarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario_comum = criar_usuario('00000000002', nome='Comum')
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.usuario_comum)
        self.url = reverse('identidade:usuarios')
        self.payload_valido = {
            'cpf': '11111111111',
            'nome': 'Novo Usuário',
            'password': 'Senha@123',
        }

    def test_admin_cria_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['dados']['cpf'], '11111111111')

    def test_usuario_comum_nao_pode_criar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cpf_duplicado_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'cpf': self.admin.cpf}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_senha_fraca_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'password': '123'}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cria_usuario_com_email_opcional(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'email': 'novo@exemplo.com'}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)


class DetalheUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:usuario-detalhe', kwargs={'pk': self.usuario.pk})

    def test_admin_obtem_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['cpf'], self.usuario.cpf)

    def test_proprio_usuario_obtem_seus_dados(self):
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
        url = reverse('identidade:usuario-detalhe', kwargs={'pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AtualizarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Original')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:usuario-detalhe', kwargs={'pk': self.usuario.pk})

    def test_admin_atualiza_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'nome': 'Atualizado'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['nome'], 'Atualizado')

    def test_proprio_usuario_atualiza_seus_dados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'nome': 'Novo Nome'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_outro_usuario_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.patch(self.url, {'nome': 'Invasor'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'nome': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_campos_parciais_sao_aceitos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'email': 'novo@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


class DesativarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Ativo')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.url = reverse('identidade:usuario-desativar', kwargs={'pk': self.usuario.pk})

    def test_admin_desativa_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.ativo)

    def test_usuario_ja_inativo_retorna_400(self):
        self.usuario.ativo = False
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_comum_nao_pode_desativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:usuario-desativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class ReativarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Inativo')
        self.usuario.ativo = False
        self.usuario.save(update_fields=['ativo'])
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.url = reverse('identidade:usuario-reativar', kwargs={'pk': self.usuario.pk})

    def test_admin_reativa_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.ativo)

    def test_usuario_ja_ativo_retorna_400(self):
        self.usuario.ativo = True
        self.usuario.save(update_fields=['ativo'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_comum_nao_pode_reativar(self):
        # Usuário inativo não consegue autenticar (JWT rejeita is_active=False) → 401
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:usuario-reativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
