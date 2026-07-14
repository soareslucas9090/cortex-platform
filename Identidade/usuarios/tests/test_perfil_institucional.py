"""
Testes de integração — Etapa 5.1 da Milestone 5
Valida a exposição dos perfis institucionais no domínio Identidade,
garantindo integração com PessoasInstitucionais via reverse relations nativas.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.urls import reverse

from Identidade.usuarios.models import Usuario


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False, **kwargs):
    return Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
        is_admin=is_admin,
        **kwargs,
    )


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_perfil_servidor(usuario, nome_cargo='Professor EBTT'):
    from PessoasInstitucionais.cargos.models import Cargo
    from PessoasInstitucionais.servidores.models import Servidor

    cargo = Cargo.objects.create(nome=nome_cargo, ativo=True)
    return Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1)


def criar_perfil_terceirizado(usuario, nome_empresa='Empresa Limpeza IFPI'):
    from PessoasInstitucionais.cargos.models import Cargo
    from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
    from PessoasInstitucionais.terceirizados.models import Terceirizado

    empresa = EmpresaInstituicao.objects.create(
        nome=nome_empresa,
        cnpj='12345678901234',
        ativo=True,
    )
    cargo = Cargo.objects.create(nome='Serviços Gerais', ativo=True)
    return Terceirizado.objects.create(
        usuario=usuario,
        empresa_instituicao=empresa,
        cargo=cargo,
    )


class PerfilInstitucionalSerializerTest(APITestCase):
    """Garante que servidor e terceirizado são expostos corretamente na API de Usuario."""

    def setUp(self):
        self.admin = criar_usuario('00000000011', nome='Admin', is_admin=True)
        self.usuario_sem_perfil = criar_usuario('00000000012', nome='Sem Perfil Institucional')
        self.usuario_servidor = criar_usuario('00000000013', nome='Servidor Integração')
        self.usuario_terceirizado = criar_usuario('00000000014', nome='Terceirizado Integração')
        criar_perfil_servidor(self.usuario_servidor)
        criar_perfil_terceirizado(self.usuario_terceirizado)
        self.token_admin = obter_tokens(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')

    def test_usuario_sem_perfil_institucional_retorna_campos_nulos(self):
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_sem_perfil.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIsNone(resposta.data['dados']['servidor'])
        self.assertIsNone(resposta.data['dados']['terceirizado'])

    def test_usuario_servidor_exposto_no_detalhe(self):
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_servidor.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        servidor = resposta.data['dados']['servidor']
        self.assertIsNotNone(servidor)
        self.assertEqual(servidor['pk'], self.usuario_servidor.pk)
        self.assertEqual(servidor['cargo_nome'], 'Professor EBTT')
        self.assertTrue(servidor['ativo'])
        self.assertIsNone(resposta.data['dados']['terceirizado'])

    def test_usuario_terceirizado_exposto_no_detalhe(self):
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_terceirizado.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        terceirizado = resposta.data['dados']['terceirizado']
        self.assertIsNotNone(terceirizado)
        self.assertEqual(terceirizado['pk'], self.usuario_terceirizado.pk)
        self.assertEqual(terceirizado['empresa_nome'], 'Empresa Limpeza IFPI')
        self.assertEqual(terceirizado['cargo_nome'], 'Serviços Gerais')
        self.assertTrue(terceirizado['ativo'])
        self.assertIsNone(resposta.data['dados']['servidor'])

    def test_campos_institucionais_presentes_na_listagem(self):
        url = reverse('identidade:usuario-list')
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        for usuario in resposta.data['dados']:
            self.assertIn('servidor', usuario)
            self.assertIn('terceirizado', usuario)

    def test_perfil_servidor_reflete_desativacao(self):
        self.usuario_servidor.servidor.ativo = False
        self.usuario_servidor.servidor.save(update_fields=['ativo'])

        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_servidor.pk})
        resposta = self.client.get(url)
        self.assertFalse(resposta.data['dados']['servidor']['ativo'])
