from django.test import TestCase

from Identidade.usuarios.tests.test_views import criar_usuario
from Infraestrutura.permissoes.choices import capacidades_infraestrutura_vazias
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
