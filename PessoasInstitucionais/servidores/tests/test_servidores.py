from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException, NotFoundException
from Organizacional.setores.models import Setor
from Organizacional.funcoes.models import Funcao
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.choices import CategoriaServidor
from PessoasInstitucionais.servidores.models import Servidor
from Identidade.usuarios.models import Usuario


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


class ServidorBusinessTestCase(APITestCase):

    def setUp(self):
        self.cargo = Cargo.objects.create(nome='Professor')
        self.usuario = Usuario.objects.create_user(
            cpf='12345678901',
            password='Teste@1234',
            nome='João da Silva',
        )

    def test_criar_servidor_sucesso(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        self.assertEqual(servidor.usuario, self.usuario)
        self.assertEqual(servidor.cargo, self.cargo)
        self.assertEqual(servidor.categoria, CategoriaServidor.DOCENTE)
        self.assertTrue(servidor.ativo)

    def test_criar_servidor_usuario_ja_com_perfil(self):
        Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        with self.assertRaises(BusinessRuleException) as context:
            Servidor().business.criar_servidor(
                usuario_pk=self.usuario.pk,
                cargo_pk=self.cargo.pk,
                categoria=CategoriaServidor.TECNICO_ADMINISTRATIVO,
            )
        self.assertIn('já possui perfil de servidor', str(context.exception))

    def test_criar_servidor_usuario_inexistente(self):
        with self.assertRaises(NotFoundException):
            Servidor().business.criar_servidor(
                usuario_pk=99999,
                cargo_pk=self.cargo.pk,
                categoria=CategoriaServidor.DOCENTE,
            )

    def test_criar_servidor_cargo_inexistente(self):
        with self.assertRaises(NotFoundException):
            Servidor().business.criar_servidor(
                usuario_pk=self.usuario.pk,
                cargo_pk=99999,
                categoria=CategoriaServidor.DOCENTE,
            )

    def test_criar_servidor_cargo_inativo(self):
        self.cargo.ativo = False
        self.cargo.save()
        with self.assertRaises(BusinessRuleException) as context:
            Servidor().business.criar_servidor(
                usuario_pk=self.usuario.pk,
                cargo_pk=self.cargo.pk,
                categoria=CategoriaServidor.DOCENTE,
            )
        self.assertIn('cargo inativo', str(context.exception))

    def test_atualizar_dados_sucesso(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        servidor.business.atualizar_dados({
            'categoria': CategoriaServidor.TECNICO_ADMINISTRATIVO,
        })
        servidor.refresh_from_db()
        self.assertEqual(servidor.categoria, CategoriaServidor.TECNICO_ADMINISTRATIVO)

    def test_atualizar_cargo_sucesso(self):
        cargo2 = Cargo.objects.create(nome='Técnico Administrativo')
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        servidor.business.atualizar_dados({'cargo_pk': cargo2.pk})
        servidor.refresh_from_db()
        self.assertEqual(servidor.cargo, cargo2)

    def test_atualizar_cargo_inativo(self):
        cargo2 = Cargo.objects.create(nome='Técnico Administrativo', ativo=False)
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        with self.assertRaises(BusinessRuleException):
            servidor.business.atualizar_dados({'cargo_pk': cargo2.pk})

    def test_desativar_servidor_sucesso(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        servidor.business.desativar()
        servidor.refresh_from_db()
        self.assertFalse(servidor.ativo)

    def test_desativar_servidor_ja_inativo(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        servidor.business.desativar()
        with self.assertRaises(BusinessRuleException):
            servidor.business.desativar()

    def test_reativar_servidor_sucesso(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        servidor.business.desativar()
        servidor.business.reativar()
        servidor.refresh_from_db()
        self.assertTrue(servidor.ativo)

    def test_reativar_servidor_ja_ativo(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        with self.assertRaises(BusinessRuleException):
            servidor.business.reativar()

    def test_str_servidor(self):
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        self.assertEqual(str(servidor), 'João da Silva - Professor')

    # -------------------------------------------------------------------
    # Testes de integração: Organizacional x PessoasInstitucionais
    # -------------------------------------------------------------------

    def test_desativar_servidor_bloqueado_quando_responsavel_por_setor_ativo(self):
        """
        Integração 5.3: desativar um Servidor que seja o responsável ativo
        de um setor ativo deve ser bloqueado pela regra de domínio.
        """
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        funcao = Funcao.objects.create(sigla='CH', descricao='Chefe')
        setor = Setor.objects.create(nome='TI', sigla='TI')
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=setor,
            funcao=funcao,
            responsavel=True,
        )

        with self.assertRaises(BusinessRuleException) as ctx:
            servidor.business.desativar()
        self.assertIn('responsável pelo setor', str(ctx.exception))

    def test_desativar_servidor_permitido_apos_remover_responsabilidade(self):
        """
        Integração 5.3: após remover a responsabilidade de setor, a
        desativação do servidor deve ser permitida normalmente.
        """
        servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )
        funcao = Funcao.objects.create(sigla='CH2', descricao='Chefe 2')
        setor = Setor.objects.create(nome='RH', sigla='RH')
        vinculo = SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=setor,
            funcao=funcao,
            responsavel=True,
        )
        # Remove a responsabilidade antes de desativar
        vinculo.responsavel = False
        vinculo.save(update_fields=['responsavel'])

        servidor.business.desativar()
        servidor.refresh_from_db()
        self.assertFalse(servidor.ativo)


class ServidoresAPITestCase(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.cargo = Cargo.objects.create(nome='Professor')
        self.usuario = Usuario.objects.create_user(
            cpf='12345678901',
            password='Teste@1234',
            nome='João da Silva',
        )
        self.servidor = Servidor().business.criar_servidor(
            usuario_pk=self.usuario.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
        )

    def test_listar_servidores(self):
        url = reverse('pessoas-institucionais:servidor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_criar_servidor(self):
        outro_usuario = Usuario.objects.create_user(
            cpf='98765432100',
            password='Teste@1234',
            nome='Maria Souza',
        )
        url = reverse('pessoas-institucionais:servidor-list')
        data = {
            'usuario_pk': outro_usuario.pk,
            'cargo_pk': self.cargo.pk,
            'categoria': CategoriaServidor.TECNICO_ADMINISTRATIVO,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_detalhar_servidor(self):
        url = reverse('pessoas-institucionais:servidor-detail', kwargs={'pk': self.servidor.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_desativar_servidor(self):
        url = reverse('pessoas-institucionais:servidor-desativar', kwargs={'pk': self.servidor.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.servidor.refresh_from_db()
        self.assertFalse(self.servidor.ativo)

    def test_reativar_servidor(self):
        self.servidor.business.desativar()
        url = reverse('pessoas-institucionais:servidor-reativar', kwargs={'pk': self.servidor.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.servidor.refresh_from_db()
        self.assertTrue(self.servidor.ativo)
