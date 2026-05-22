from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.empresas_instituicoes.business import EmpresaInstituicaoBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', email='test@test.com', nome=nome)


class TestEmpresaInstituicaoBusiness(APITestCase):

    def setUp(self):
        self.empresa = EmpresaInstituicao.objects.create(
            nome='Empresa Teste',
            cnpj='11111111111111'
        )

    def test_criar_empresa(self):
        business = EmpresaInstituicaoBusiness()
        empresa = business.criar_empresa({'nome': 'Nova Empresa', 'cnpj': '22222222222222'})
        self.assertTrue(EmpresaInstituicao.objects.filter(nome='Nova Empresa').exists())
        self.assertEqual(empresa.nome, 'Nova Empresa')
        self.assertEqual(empresa.cnpj, '22222222222222')

    def test_criar_empresa_nome_duplicado(self):
        business = EmpresaInstituicaoBusiness()
        with self.assertRaises(BusinessRuleException) as context:
            business.criar_empresa({'nome': 'Empresa Teste'})
        self.assertIn('Já existe uma empresa/instituição cadastrada com esse nome.', str(context.exception))

    def test_criar_empresa_cnpj_duplicado(self):
        business = EmpresaInstituicaoBusiness()
        with self.assertRaises(BusinessRuleException) as context:
            business.criar_empresa({'nome': 'Outra Empresa', 'cnpj': '11111111111111'})
        self.assertIn('Já existe uma empresa/instituição cadastrada com esse CNPJ.', str(context.exception))

    def test_atualizar_dados(self):
        business = EmpresaInstituicaoBusiness(object_instance=self.empresa)
        business.atualizar_dados({'nome': 'Empresa Atualizada'})
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.nome, 'Empresa Atualizada')

    def test_desativar_reativar(self):
        business = EmpresaInstituicaoBusiness(object_instance=self.empresa)
        business.desativar()
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.ativo)

        business.reativar()
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.ativo)


class TestEmpresaInstituicaoAPI(APITestCase):

    def setUp(self):
        self.comum = criar_usuario_comum()
        self.token = obter_tokens(self.comum)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.empresa = EmpresaInstituicao.objects.create(
            nome='Empresa Teste',
            cnpj='11111111111111'
        )

    def test_list_empresas(self):
        url = reverse('pessoas_institucionais:empresa-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_empresa(self):
        url = reverse('pessoas_institucionais:empresa-list')
        data = {'nome': 'Nova via API', 'cnpj': '12345678901234'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmpresaInstituicao.objects.filter(nome='Nova via API').exists())

    def test_desativar_empresa(self):
        url = reverse('pessoas_institucionais:empresa-desativar', kwargs={'pk': self.empresa.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.ativo)
