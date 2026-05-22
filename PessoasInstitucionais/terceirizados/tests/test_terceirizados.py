import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException, NotFoundException
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.terceirizados.models import Terceirizado
from Identidade.usuarios.models import Usuario


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


def criar_usuario(cpf='12345678901', nome='João da Silva'):
    return Usuario.objects.create_user(
        cpf=cpf,
        password='Teste@1234',
        nome=nome,
    )


def criar_empresa(nome='Empresa Teste LTDA', ativo=True):
    return EmpresaInstituicao.objects.create(nome=nome, ativo=ativo)


class TerceirizadoBusinessTestCase(APITestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.usuario = criar_usuario()
        self.data_inicio = datetime.date(2024, 1, 15)

    def test_criar_terceirizado_sucesso(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        self.assertEqual(terceirizado.usuario, self.usuario)
        self.assertEqual(terceirizado.empresa, self.empresa)
        self.assertEqual(terceirizado.cargo_funcao, 'Técnico de TI')
        self.assertEqual(terceirizado.data_inicio, self.data_inicio)
        self.assertIsNone(terceirizado.data_fim)
        self.assertTrue(terceirizado.ativo)

    def test_criar_terceirizado_usuario_ja_com_perfil(self):
        Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        with self.assertRaises(BusinessRuleException) as context:
            Terceirizado().business.criar_terceirizado(
                usuario_pk=self.usuario.pk,
                empresa_pk=self.empresa.pk,
                cargo_funcao='Auxiliar Administrativo',
                data_inicio=self.data_inicio,
            )
        self.assertIn('já possui perfil de terceirizado', str(context.exception))

    def test_criar_terceirizado_usuario_inexistente(self):
        with self.assertRaises(NotFoundException):
            Terceirizado().business.criar_terceirizado(
                usuario_pk=99999,
                empresa_pk=self.empresa.pk,
                cargo_funcao='Técnico de TI',
                data_inicio=self.data_inicio,
            )

    def test_criar_terceirizado_empresa_inexistente(self):
        with self.assertRaises(NotFoundException):
            Terceirizado().business.criar_terceirizado(
                usuario_pk=self.usuario.pk,
                empresa_pk=99999,
                cargo_funcao='Técnico de TI',
                data_inicio=self.data_inicio,
            )

    def test_criar_terceirizado_empresa_inativa(self):
        empresa_inativa = criar_empresa(nome='Empresa Inativa', ativo=False)
        with self.assertRaises(BusinessRuleException) as context:
            Terceirizado().business.criar_terceirizado(
                usuario_pk=self.usuario.pk,
                empresa_pk=empresa_inativa.pk,
                cargo_funcao='Técnico de TI',
                data_inicio=self.data_inicio,
            )
        self.assertIn('inativa', str(context.exception))

    def test_criar_terceirizado_com_data_fim(self):
        data_fim = datetime.date(2024, 12, 31)
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
            data_fim=data_fim,
        )
        self.assertEqual(terceirizado.data_fim, data_fim)

    def test_atualizar_cargo_funcao_sucesso(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        terceirizado.business.atualizar_dados({'cargo_funcao': 'Auxiliar Administrativo'})
        terceirizado.refresh_from_db()
        self.assertEqual(terceirizado.cargo_funcao, 'Auxiliar Administrativo')

    def test_atualizar_empresa_sucesso(self):
        empresa2 = criar_empresa(nome='Outra Empresa LTDA')
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        terceirizado.business.atualizar_dados({'empresa_pk': empresa2.pk})
        terceirizado.refresh_from_db()
        self.assertEqual(terceirizado.empresa, empresa2)

    def test_atualizar_empresa_inativa(self):
        empresa_inativa = criar_empresa(nome='Empresa Inativa', ativo=False)
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        with self.assertRaises(BusinessRuleException):
            terceirizado.business.atualizar_dados({'empresa_pk': empresa_inativa.pk})

    def test_desativar_terceirizado_sucesso(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        terceirizado.business.desativar()
        terceirizado.refresh_from_db()
        self.assertFalse(terceirizado.ativo)

    def test_desativar_terceirizado_ja_inativo(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        terceirizado.business.desativar()
        with self.assertRaises(BusinessRuleException):
            terceirizado.business.desativar()

    def test_reativar_terceirizado_sucesso(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        terceirizado.business.desativar()
        terceirizado.business.reativar()
        terceirizado.refresh_from_db()
        self.assertTrue(terceirizado.ativo)

    def test_reativar_terceirizado_ja_ativo(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        with self.assertRaises(BusinessRuleException):
            terceirizado.business.reativar()

    def test_str_terceirizado(self):
        terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )
        self.assertEqual(str(terceirizado), 'João da Silva - Empresa Teste LTDA')


class TerceirizadosAPITestCase(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.empresa = EmpresaInstituicao.objects.create(nome='Empresa Teste LTDA')
        self.usuario = Usuario.objects.create_user(
            cpf='12345678901',
            password='Teste@1234',
            nome='João da Silva',
        )
        self.data_inicio = datetime.date(2024, 1, 15)
        self.terceirizado = Terceirizado().business.criar_terceirizado(
            usuario_pk=self.usuario.pk,
            empresa_pk=self.empresa.pk,
            cargo_funcao='Técnico de TI',
            data_inicio=self.data_inicio,
        )

    def test_listar_terceirizados(self):
        url = reverse('pessoas-institucionais:terceirizado-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_criar_terceirizado(self):
        outro_usuario = Usuario.objects.create_user(
            cpf='98765432100',
            password='Teste@1234',
            nome='Maria Souza',
        )
        url = reverse('pessoas-institucionais:terceirizado-list')
        data = {
            'usuario_pk': outro_usuario.pk,
            'empresa_pk': self.empresa.pk,
            'cargo_funcao': 'Auxiliar Administrativo',
            'data_inicio': '2024-03-01',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_detalhar_terceirizado(self):
        url = reverse('pessoas-institucionais:terceirizado-detail', kwargs={'pk': self.terceirizado.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_desativar_terceirizado(self):
        url = reverse('pessoas-institucionais:terceirizado-desativar', kwargs={'pk': self.terceirizado.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.terceirizado.refresh_from_db()
        self.assertFalse(self.terceirizado.ativo)

    def test_reativar_terceirizado(self):
        self.terceirizado.business.desativar()
        url = reverse('pessoas-institucionais:terceirizado-reativar', kwargs={'pk': self.terceirizado.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.terceirizado.refresh_from_db()
        self.assertTrue(self.terceirizado.ativo)
