from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException, NotFoundException
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.choices import CategoriaServidor
from PessoasInstitucionais.servidores.models import Servidor
from Identidade.usuarios.models import Usuario


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
