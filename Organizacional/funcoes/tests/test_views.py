from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome, is_admin=True)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def criar_funcao(sigla='TI', descricao='Técnico de Informática', e_gratificada=False, ativo=True):
    return Funcao.objects.create(
        sigla=sigla, descricao=descricao, e_gratificada=e_gratificada, ativo=ativo,
    )


class ListarFuncoesViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.url = reverse('organizacional:funcoes')

    def test_admin_lista_funcoes_com_sucesso(self):
        criar_funcao()
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

    def test_filtro_ativo_true_retorna_somente_ativas(self):
        criar_funcao(sigla='TI', descricao='Ativa', ativo=True)
        criar_funcao(sigla='RH', descricao='Inativa', ativo=False)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        siglas = [f['sigla'] for f in resposta.data['dados']]
        self.assertIn('TI', siglas)
        self.assertNotIn('RH', siglas)

    def test_filtro_ativo_false_retorna_somente_inativas(self):
        criar_funcao(sigla='TI', descricao='Ativa', ativo=True)
        criar_funcao(sigla='RH', descricao='Inativa', ativo=False)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        siglas = [f['sigla'] for f in resposta.data['dados']]
        self.assertNotIn('TI', siglas)
        self.assertIn('RH', siglas)

    def test_filtro_ativo_invalido_e_ignorado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'invalido'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_retorna_lista_vazia_sem_funcoes(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])


class CriarFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.url = reverse('organizacional:funcoes')
        self.payload_valido = {
            'sigla': 'TI',
            'descricao': 'Técnico de Informática',
        }

    def test_admin_cria_funcao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['dados']['sigla'], 'TI')

    def test_funcao_criada_e_ativa_por_padrao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['ativo'])

    def test_cria_funcao_gratificada(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'e_gratificada': True}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['e_gratificada'])

    def test_e_gratificada_padrao_e_false(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resposta.data['dados']['e_gratificada'])

    def test_usuario_comum_nao_pode_criar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sigla_duplicada_retorna_400(self):
        criar_funcao(sigla='TI', descricao='Existente')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sigla_obrigatoria_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'descricao': 'Sem sigla'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_descricao_obrigatoria_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'sigla': 'TI'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)


class DetalheFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.funcao = criar_funcao()
        self.url = reverse('organizacional:funcao-detalhe', kwargs={'pk': self.funcao.pk})

    def test_admin_obtem_funcao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], 'success')
        self.assertEqual(resposta.data['dados']['sigla'], self.funcao.sigla)

    def test_usuario_comum_nao_pode_acessar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funcao_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:funcao-detalhe', kwargs={'pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AtualizarFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.funcao = criar_funcao(sigla='TI', descricao='Descrição Original')
        self.url = reverse('organizacional:funcao-detalhe', kwargs={'pk': self.funcao.pk})

    def test_admin_atualiza_descricao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'descricao': 'Descrição Atualizada'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['descricao'], 'Descrição Atualizada')

    def test_admin_atualiza_sigla_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'IT'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['sigla'], 'IT')

    def test_retorna_dados_atualizados_na_resposta(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'descricao': 'Nova'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('dados', resposta.data)

    def test_usuario_comum_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.patch(self.url, {'descricao': 'Invasor'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'descricao': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sigla_duplicada_retorna_400(self):
        criar_funcao(sigla='RH', descricao='Recursos Humanos')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'RH'})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_com_mesma_sigla_nao_retorna_erro(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'sigla': 'TI'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_funcao_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:funcao-detalhe', kwargs={'pk': 99999})
        resposta = self.client.patch(url, {'descricao': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class DesativarFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.funcao = criar_funcao(ativo=True)
        self.url = reverse('organizacional:funcao-desativar', kwargs={'pk': self.funcao.pk})

    def test_admin_desativa_funcao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.funcao.refresh_from_db()
        self.assertFalse(self.funcao.ativo)

    def test_usuario_comum_nao_pode_desativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funcao_ja_inativa_retorna_400(self):
        self.funcao.ativo = False
        self.funcao.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_funcao_em_uso_em_vinculo_retorna_400(self):
        from Organizacional.setores.models import Setor
        from Organizacional.vinculos.models import SetorVinculo
        setor = Setor.objects.create(nome='Setor Teste', sigla='ST')
        SetorVinculo.objects.create(
            usuario=self.admin, setor=setor, funcao=self.funcao, responsavel=False,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_funcao_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:funcao-desativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class ReativarFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.funcao = criar_funcao(ativo=False)
        self.url = reverse('organizacional:funcao-reativar', kwargs={'pk': self.funcao.pk})

    def test_admin_reativa_funcao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.funcao.refresh_from_db()
        self.assertTrue(self.funcao.ativo)

    def test_usuario_comum_nao_pode_reativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funcao_ja_ativa_retorna_400(self):
        self.funcao.ativo = True
        self.funcao.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_funcao_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('organizacional:funcao-reativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
