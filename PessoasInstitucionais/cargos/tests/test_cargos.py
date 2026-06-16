from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.cargos.models import Cargo


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


class CargoBusinessTestCase(APITestCase):
    
    def test_criar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        self.assertEqual(cargo.nome, 'Professor')
        self.assertTrue(cargo.ativo)

    def test_criar_cargo_nome_duplicado(self):
        Cargo().business.criar_cargo(nome='Professor')
        with self.assertRaises(BusinessRuleException) as context:
            Cargo().business.criar_cargo(nome='Professor')
        self.assertIn('Já existe um cargo cadastrado com esse nome', str(context.exception))

    def test_atualizar_dados_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.atualizar_dados({'nome': 'Professor Titular'})
        cargo.refresh_from_db()
        self.assertEqual(cargo.nome, 'Professor Titular')

    def test_atualizar_dados_nome_duplicado(self):
        Cargo().business.criar_cargo(nome='Professor')
        cargo2 = Cargo().business.criar_cargo(nome='Técnico')
        with self.assertRaises(BusinessRuleException):
            cargo2.business.atualizar_dados({'nome': 'Professor'})

    def test_desativar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        cargo.refresh_from_db()
        self.assertFalse(cargo.ativo)

    def test_desativar_cargo_ja_inativo(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        with self.assertRaises(BusinessRuleException):
            cargo.business.desativar()

    def test_reativar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        cargo.business.reativar()
        cargo.refresh_from_db()
        self.assertTrue(cargo.ativo)

    def test_reativar_cargo_ja_ativo(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        with self.assertRaises(BusinessRuleException):
            cargo.business.reativar()


class CargosAPITestCase(APITestCase):

    def setUp(self):
        Cargo.objects.all().delete()
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.cargo = Cargo.objects.create(nome='Professor')

    def test_listar_cargos(self):
        url = reverse('pessoas-institucionais:cargo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_criar_cargo(self):
        url = reverse('pessoas-institucionais:cargo-list')
        response = self.client.post(url, {'nome': 'Técnico Administrativo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Cargo.objects.filter(nome='Técnico Administrativo').exists())

    def test_detalhar_cargo(self):
        url = reverse('pessoas-institucionais:cargo-detail', kwargs={'pk': self.cargo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dados']['nome'], 'Professor')

    def test_desativar_cargo(self):
        url = reverse('pessoas-institucionais:cargo-desativar', kwargs={'pk': self.cargo.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cargo.refresh_from_db()
        self.assertFalse(self.cargo.ativo)

    def test_reativar_cargo(self):
        self.cargo.business.desativar()
        url = reverse('pessoas-institucionais:cargo-reativar', kwargs={'pk': self.cargo.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cargo.refresh_from_db()
        self.assertTrue(self.cargo.ativo)
