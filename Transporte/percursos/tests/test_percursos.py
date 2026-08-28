from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor
from Transporte.percursos.models import Percurso


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin TI'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def criar_servidor(cpf='00000000003', nome='Servidor'):
    usuario = Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)
    cargo = Cargo.objects.create(nome=f'Cargo {cpf}')
    Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1, ativo=True)
    return usuario


def criar_percurso(apelido='Rota R.SÃ', descricao='IFPI – Posto R.Sã – FM'):
    return Percurso.objects.create(apelido=apelido, descricao=descricao)


class PercursoBusinessTestCase(APITestCase):

    def test_criar_percurso_sucesso(self):
        percurso = Percurso().business.criar_percurso(
            apelido='Rota Pontões',
            descricao='IFPI – São Jorge Super – Pontões',
        )
        self.assertEqual(percurso.apelido, 'Rota Pontões')
        self.assertTrue(percurso.ativo)

    def test_criar_percurso_apelido_duplicado(self):
        Percurso().business.criar_percurso(apelido='Rota R.SÃ', descricao='Trajeto A')
        with self.assertRaises(BusinessRuleException) as ctx:
            Percurso().business.criar_percurso(apelido='rota r.sã', descricao='Trajeto B')
        self.assertIn('Já existe um percurso cadastrado com esse apelido', str(ctx.exception))

    def test_atualizar_dados_sucesso(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='Desc A')
        percurso.business.atualizar_dados({'descricao': 'Desc B'})
        percurso.refresh_from_db()
        self.assertEqual(percurso.descricao, 'Desc B')

    def test_atualizar_dados_apelido_duplicado(self):
        Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        percurso = Percurso().business.criar_percurso(apelido='Rota B', descricao='B')
        with self.assertRaises(BusinessRuleException):
            percurso.business.atualizar_dados({'apelido': 'Rota A'})

    def test_atualizar_dados_mesmo_apelido(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        percurso.business.atualizar_dados({'apelido': 'Rota A', 'descricao': 'Atualizada'})
        percurso.refresh_from_db()
        self.assertEqual(percurso.descricao, 'Atualizada')

    def test_desativar_percurso_sucesso(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        percurso.business.desativar()
        percurso.refresh_from_db()
        self.assertFalse(percurso.ativo)

    def test_desativar_percurso_ja_inativo(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        percurso.business.desativar()
        with self.assertRaises(BusinessRuleException):
            percurso.business.desativar()

    def test_reativar_percurso_sucesso(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        percurso.business.desativar()
        percurso.business.reativar()
        percurso.refresh_from_db()
        self.assertTrue(percurso.ativo)

    def test_reativar_percurso_ja_ativo(self):
        percurso = Percurso().business.criar_percurso(apelido='Rota A', descricao='A')
        with self.assertRaises(BusinessRuleException):
            percurso.business.reativar()


class PercursosAPITestCase(APITestCase):

    def setUp(self):
        Percurso.objects.all().delete()
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.percurso = criar_percurso()
        self.url_list = reverse('transporte:percursos-list')

    def test_listar_percursos(self):
        resposta = self.client.get(self.url_list)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listar_percursos_filtrar_ativo(self):
        resposta = self.client.get(self.url_list, {'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listar_percursos_filtrar_inativo(self):
        self.percurso.business.desativar()
        resposta = self.client.get(self.url_list, {'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listar_percursos_busca_por_apelido(self):
        criar_percurso(apelido='Rota Pontões', descricao='Outro trajeto')
        resposta = self.client.get(self.url_list, {'busca': 'Pontões'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        apelidos = [item['apelido'] for item in resposta.data['dados']]
        self.assertEqual(apelidos, ['Rota Pontões'])

    def test_listar_percursos_busca_por_descricao(self):
        criar_percurso(apelido='Rota Pontões', descricao='IFPI São Jorge Super Pontões')
        resposta = self.client.get(self.url_list, {'busca': 'São Jorge'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        apelidos = [item['apelido'] for item in resposta.data['dados']]
        self.assertEqual(apelidos, ['Rota Pontões'])

    def test_criar_percurso(self):
        payload = {'apelido': 'Rota Centro', 'descricao': 'IFPI – Centro'}
        resposta = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Percurso.objects.filter(apelido='Rota Centro').exists())

    def test_criar_percurso_apelido_duplicado(self):
        payload = {'apelido': 'Rota R.SÃ', 'descricao': 'Outro trajeto'}
        resposta = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhar_percurso(self):
        url = reverse('transporte:percurso-detail', kwargs={'pk': self.percurso.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['apelido'], 'Rota R.SÃ')

    def test_atualizar_percurso(self):
        url = reverse('transporte:percurso-detail', kwargs={'pk': self.percurso.pk})
        resposta = self.client.patch(url, {'descricao': 'Trajeto atualizado'}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.percurso.refresh_from_db()
        self.assertEqual(self.percurso.descricao, 'Trajeto atualizado')

    def test_desativar_percurso(self):
        url = reverse('transporte:percurso-desativar', kwargs={'pk': self.percurso.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.percurso.refresh_from_db()
        self.assertFalse(self.percurso.ativo)

    def test_desativar_percurso_ja_inativo(self):
        self.percurso.business.desativar()
        url = reverse('transporte:percurso-desativar', kwargs={'pk': self.percurso.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reativar_percurso(self):
        self.percurso.business.desativar()
        url = reverse('transporte:percurso-reativar', kwargs={'pk': self.percurso.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.percurso.refresh_from_db()
        self.assertTrue(self.percurso.ativo)

    def test_reativar_percurso_ja_ativo(self):
        url = reverse('transporte:percurso-reativar', kwargs={'pk': self.percurso.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        resposta = self.client.get(self.url_list)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_l1_nao_pode_listar_nem_criar(self):
        usuario = criar_usuario_comum()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        self.assertEqual(self.client.get(self.url_list).status_code, status.HTTP_403_FORBIDDEN)
        resposta = self.client.post(
            self.url_list,
            {'apelido': 'Rota Nova', 'descricao': 'Trajeto'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l2_nao_pode_listar_nem_criar(self):
        servidor = criar_servidor()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(servidor)}')
        self.assertEqual(self.client.get(self.url_list).status_code, status.HTTP_403_FORBIDDEN)
        resposta = self.client.post(
            self.url_list,
            {'apelido': 'Rota Nova', 'descricao': 'Trajeto'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l3_recebe_permissao_gerenciar_transporte(self):
        self.assertTrue(self.admin.permissoes['transporte']['gerenciar'])

    def test_l1_nao_recebe_permissao_gerenciar_transporte(self):
        usuario = criar_usuario_comum(cpf='00000000009')
        self.assertFalse(usuario.permissoes['transporte']['gerenciar'])
