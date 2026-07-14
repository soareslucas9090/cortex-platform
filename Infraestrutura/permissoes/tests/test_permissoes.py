from django.test import TestCase

from Identidade.usuarios.tests.test_views import criar_usuario
from Infraestrutura.permissoes.access import (
    usuario_pode_autorizar_infraestrutura,
    usuario_pode_cadastrar_infraestrutura,
    usuario_pode_operar_infraestrutura,
    usuario_tem_acesso_total_infraestrutura,
)
from Infraestrutura.permissoes.choices import (
    capacidades_infraestrutura_completas,
    capacidades_infraestrutura_vazias,
)
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def criar_funcao(papel_funcao='AUX', descricao='Auxiliar', ativo=True):
    return Funcao.objects.create(
        papel_funcao=papel_funcao,
        descricao=descricao,
        ativo=ativo,
    )


def criar_setor(sigla='TI', nome='Tecnologia da Informação', ativo=True):
    return Setor.objects.create(sigla=sigla, nome=nome, ativo=ativo)


class PermissaoInfraestruturaCompilacaoTest(TestCase):

    def setUp(self):
        self.usuario = criar_usuario('12312312312', nome='Usuário Permissões')
        self.setor = criar_setor()
        self.funcao_operar = criar_funcao(papel_funcao='GUA', descricao='Guarda')
        self.funcao_autorizar = criar_funcao(papel_funcao='DIR', descricao='Diretor')

    def test_usuario_sem_vinculo_tem_capacidades_desligadas(self):
        resultado = PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(self.usuario)
        self.assertEqual(resultado, capacidades_infraestrutura_vazias())

    def test_compila_capacidade_operar_do_vinculo_ativo(self):
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=self.funcao_operar.pk,
            operar=True,
        )
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=self.setor,
            funcao=self.funcao_operar,
        )

        resultado = PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(self.usuario)
        self.assertTrue(resultado['operar'])
        self.assertFalse(resultado['cadastrar'])

    def test_compila_uniao_or_entre_funcoes(self):
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=self.funcao_operar.pk,
            operar=True,
        )
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=self.funcao_autorizar.pk,
            autorizar=True,
            cadastrar=True,
        )
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=self.setor,
            funcao=self.funcao_operar,
        )
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=self.setor,
            funcao=self.funcao_autorizar,
        )

        resultado = PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(self.usuario)
        self.assertTrue(resultado['operar'])
        self.assertTrue(resultado['autorizar'])
        self.assertTrue(resultado['cadastrar'])

    def test_vinculo_com_setor_inativo_nao_conta(self):
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=self.funcao_operar.pk,
            operar=True,
        )
        setor_inativo = criar_setor(sigla='IN', nome='Inativo', ativo=False)
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=setor_inativo,
            funcao=self.funcao_operar,
        )

        resultado = PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(self.usuario)
        self.assertEqual(resultado, capacidades_infraestrutura_vazias())

    def test_vinculo_com_funcao_inativa_nao_conta(self):
        funcao_inativa = criar_funcao(papel_funcao='OLD', descricao='Inativa', ativo=True)
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=funcao_inativa.pk,
            operar=True,
        )
        funcao_inativa.ativo = False
        funcao_inativa.save(update_fields=['ativo'])
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=self.setor,
            funcao=funcao_inativa,
        )

        resultado = PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(self.usuario)
        self.assertEqual(resultado, capacidades_infraestrutura_vazias())

    def test_usuario_permissions_inclui_chave_infraestrutura(self):
        PermissaoFuncaoInfraestrutura().business.criar_permissao(
            funcao_id=self.funcao_operar.pk,
            operar=True,
            retirada_irrestrita=True,
        )
        SetorVinculo.objects.create(
            usuario=self.usuario,
            setor=self.setor,
            funcao=self.funcao_operar,
        )

        permissoes = self.usuario.permissoes
        self.assertIn('infraestrutura', permissoes)
        self.assertTrue(permissoes['infraestrutura']['operar'])
        self.assertTrue(permissoes['infraestrutura']['retirada_irrestrita'])


class PermissaoInfraestruturaAdminSuperuserTest(TestCase):

    def test_admin_sem_vinculo_tem_capacidades_completas(self):
        admin = criar_usuario('99999999991', nome='Admin Infra', is_admin=True)
        self.assertEqual(admin.permissoes['infraestrutura'], capacidades_infraestrutura_completas())

    def test_superuser_sem_vinculo_tem_capacidades_completas(self):
        superuser = criar_usuario('99999999992', nome='Super Infra', is_superuser=True)
        self.assertEqual(superuser.permissoes['infraestrutura'], capacidades_infraestrutura_completas())

    def test_admin_tem_acesso_total_nas_checagens_de_api(self):
        admin = criar_usuario('99999999993', nome='Admin API', is_admin=True)
        self.assertTrue(usuario_tem_acesso_total_infraestrutura(admin))
        self.assertTrue(usuario_pode_cadastrar_infraestrutura(admin))
        self.assertTrue(usuario_pode_autorizar_infraestrutura(admin))
        self.assertTrue(usuario_pode_operar_infraestrutura(admin))

    def test_usuario_comum_sem_vinculo_nao_tem_acesso_total(self):
        usuario = criar_usuario('99999999994', nome='Comum Infra')
        self.assertFalse(usuario_tem_acesso_total_infraestrutura(usuario))
        self.assertFalse(usuario_pode_cadastrar_infraestrutura(usuario))
