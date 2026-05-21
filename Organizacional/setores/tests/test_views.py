from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Organizacional.setores.models import Setor


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome, is_admin=True)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def criar_setor(sigla='TI', nome='Tecnologia da Informação', ativo=True):
    return Setor.objects.create(sigla=sigla, nome=nome, ativo=ativo)


class ListarSetoresViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.url = reverse('organizacional:setores')

    def test_admin_lista_setores_com_sucesso(self):
        criar_setor()
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
        criar_setor(sigla='TI', nome='Ativo', ativo=True)
        criar_setor(sigla='RH', nome='Inativo', ativo=False)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        siglas = [s['sigla'] for s in resposta.data['dados']]
        self.assertIn('TI', siglas)
        self.assertNotIn('RH', siglas)

    def test_filtro_ativo_false_retorna_somente_inativos(self):
        criar_setor(sigla='TI', nome='Ativo', ativo=True)
        criar_setor(sigla='RH', nome='Inativo', ativo=False)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        siglas = [s['sigla'] for s in resposta.data['dados']]
        self.assertNotIn('TI', siglas)
        self.assertIn('RH', siglas)

    def test_filtro_ativo_invalido_e_ignorado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'invalido'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_retorna_lista_vazia_sem_setores(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])


class CriarSetorViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.url = reverse('organizacional:setores')
        self.payload_valido = {
            'nome': 'Tecnologia da Informação',
            'sigla': 'TI',
        }

    def test_admin_cria_setor_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['dados']['sigla'], 'TI')
        self.assertEqual(resposta.data['dados']['nome'], 'Tecnologia da Informação')

    def test_setor_criado_e_ativo_por_padrao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['ativo'])

    def test_usuario_comum_nao_pode_criar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sigla_duplicada_retorna_400(self):
        criar_setor(sigla='TI')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nome_obrigatorio_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'sigla': 'TI'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sigla_obrigatoria_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'nome': 'Tecnologia'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)


class DetalheSetorViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.url = reverse('organizacional:setor-detalhe', kwargs={'pk': self.setor.pk})

    def test_admin_obtem_setor_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], 'success')
        self.assertEqual(resposta.data['dados']['sigla'], self.setor.sigla)

    def test_usuario_comum_nao_pode_acessar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:setor-detalhe', kwargs={'pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AtualizarSetorViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor(sigla='TI', nome='Nome Original')
        self.url = reverse('organizacional:setor-detalhe', kwargs={'pk': self.setor.pk})

    def test_admin_atualiza_nome_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'nome': 'Nome Atualizado'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['nome'], 'Nome Atualizado')

    def test_admin_atualiza_sigla_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'IT'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['sigla'], 'IT')

    def test_retorna_dados_atualizados_na_resposta(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'nome': 'Novo Nome'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('dados', resposta.data)

    def test_usuario_comum_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.patch(self.url, {'nome': 'Invasor'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'nome': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sigla_duplicada_retorna_400(self):
        criar_setor(sigla='RH', nome='Recursos Humanos')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'RH'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_com_mesma_sigla_nao_retorna_erro(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'TI'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_setor_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:setor-detalhe', kwargs={'pk': 99999})
        resposta = self.client.patch(url, {'nome': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class DesativarSetorViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor(ativo=True)
        self.url = reverse('organizacional:setor-desativar', kwargs={'pk': self.setor.pk})

    def test_admin_desativa_setor_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.setor.refresh_from_db()
        self.assertFalse(self.setor.ativo)

    def test_usuario_comum_nao_pode_desativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_ja_inativo_retorna_400(self):
        self.setor.ativo = False
        self.setor.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_setor_com_vinculos_ativos_retorna_400(self):
        from Organizacional.funcoes.models import Funcao
        from Organizacional.vinculos.models import SetorVinculo
        funcao = Funcao.objects.create(sigla='AUX', descricao='Auxiliar')
        SetorVinculo.objects.create(
            usuario=self.admin, setor=self.setor, funcao=funcao, responsavel=False,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_setor_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:setor-desativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class ReativarSetorViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor(ativo=False)
        self.url = reverse('organizacional:setor-reativar', kwargs={'pk': self.setor.pk})

    def test_admin_reativa_setor_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.setor.refresh_from_db()
        self.assertTrue(self.setor.ativo)

    def test_usuario_comum_nao_pode_reativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_ja_ativo_retorna_400(self):
        self.setor.ativo = True
        self.setor.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_setor_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:setor-reativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
