import datetime

from django.test import TestCase
from django.utils import timezone

from Identidade.usuarios.models import Usuario
from Infraestrutura.autorizacoes.models import Autorizacao
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.emprestimos.choices import CARGO_SERVENTE_LIMPEZA, HORAS_ALERTA_ATRASO
from Infraestrutura.emprestimos.models import Emprestimo, ItemEmprestimo
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala, SalaSetor
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.terceirizados.models import Terceirizado


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_operar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'OP_{usuario.cpf}', descricao='Operador')
    setor = Setor.objects.create(sigla=f'O{usuario.cpf[-3:]}', nome='Setor Operador')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, operar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class EmprestimoElegibilidadeTest(TestCase):

    def setUp(self):
        self.operador = conceder_capacidade_operar(criar_usuario('15151515151', nome='Operador'))
        self.solicitante = criar_usuario('16161616161', nome='Solicitante')
        self.bloco = Bloco.objects.create(nome='Bloco Emp')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Emp')
        self.chave = Recurso.objects.create(
            codigo='CHV-EMP',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        self.midia = Recurso.objects.create(
            codigo='MID-EMP',
            tipo=TipoRecurso.MIDIA,
        )

    def test_chave_via_sala_setor(self):
        setor = Setor.objects.create(sigla='SET', nome='Setor Sala')
        SalaSetor.objects.create(sala=self.sala, setor=setor)
        SetorVinculo.objects.create(usuario=self.solicitante, setor=setor, funcao=None)

        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave.pk],
        )
        self.assertEqual(emprestimo.solicitante, self.solicitante)

    def test_midia_exige_autorizacao(self):
        with self.assertRaises(Exception):
            Emprestimo().business.realizar_emprestimo(
                solicitante_id=self.solicitante.pk,
                responsavel=self.operador,
                recurso_ids=[self.midia.pk],
            )

    def test_midia_com_autorizacao(self):
        autorizador = conceder_capacidade_operar(criar_usuario('18181818181', nome='Autorizador Emp'))
        funcao_aut = Funcao.objects.create(papel_funcao='AUT_EMP', descricao='Aut')
        setor_aut = Setor.objects.create(sigla='AUT', nome='Setor Aut')
        PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao_aut.pk, autorizar=True)
        SetorVinculo.objects.create(usuario=autorizador, setor=setor_aut, funcao=funcao_aut)

        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.solicitante.pk,
            concedente=autorizador,
            recurso_id=self.midia.pk,
            data_inicio=datetime.date.today(),
        )

        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.midia.pk],
        )
        self.assertEqual(emprestimo.itens.count(), 1)

    def test_servente_limpeza_retira_qualquer_chave(self):
        empresa = EmpresaInstituicao.objects.create(nome='Empresa Limpeza')
        cargo, _ = Cargo.objects.get_or_create(nome=CARGO_SERVENTE_LIMPEZA, defaults={'ativo': True})
        limpeza = criar_usuario('19191919191', nome='Servente Limpeza')
        Terceirizado().business.criar_terceirizado(
            usuario_pk=limpeza.pk,
            empresa_pk=empresa.pk,
            cargo_pk=cargo.pk,
            data_inicio=datetime.date.today(),
        )
        outra_sala = Sala.objects.create(bloco=self.bloco, nome='Sala Outra')
        outra_chave = Recurso.objects.create(
            codigo='CHV-OUT',
            tipo=TipoRecurso.CHAVE,
            sala=outra_sala,
        )

        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=limpeza.pk,
            responsavel=self.operador,
            recurso_ids=[outra_chave.pk],
        )
        self.assertEqual(emprestimo.solicitante, limpeza)


class EmprestimoOperacoesTest(TestCase):

    def setUp(self):
        self.operador = conceder_capacidade_operar(criar_usuario('20202020202', nome='Operador Op'))
        self.solicitante = criar_usuario('21212121212', nome='Solicitante Op')
        self.novo_solicitante = criar_usuario('22222222223', nome='Novo Solicitante')
        self.bloco = Bloco.objects.create(nome='Bloco Op')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Op')
        setor = Setor.objects.create(sigla='SOP', nome='Setor Op')
        SalaSetor.objects.create(sala=self.sala, setor=setor)
        SetorVinculo.objects.create(usuario=self.solicitante, setor=setor, funcao=None)
        SetorVinculo.objects.create(usuario=self.novo_solicitante, setor=setor, funcao=None)
        self.chave1 = Recurso.objects.create(
            codigo='CHV-OP1',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        self.chave2 = Recurso.objects.create(
            codigo='CHV-OP2',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )

    def test_nao_permite_segundo_emprestimo_aberto_no_recurso(self):
        Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave1.pk],
        )
        with self.assertRaises(Exception):
            Emprestimo().business.realizar_emprestimo(
                solicitante_id=self.solicitante.pk,
                responsavel=self.operador,
                recurso_ids=[self.chave1.pk],
            )

    def test_devolucao_parcial_mantem_emprestimo_ativo(self):
        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave1.pk, self.chave2.pk],
        )
        item_id = emprestimo.itens.filter(recurso=self.chave1).values_list('pk', flat=True).first()
        emprestimo.business.devolver_itens(self.operador, [item_id])
        emprestimo.refresh_from_db()
        self.assertTrue(emprestimo.ativo)

    def test_devolucao_total_encerra_emprestimo(self):
        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave1.pk],
        )
        item_id = emprestimo.itens.first().pk
        emprestimo.business.devolver_itens(self.operador, [item_id])
        emprestimo.refresh_from_db()
        self.assertFalse(emprestimo.ativo)

    def test_trocar_titular_abre_novo_emprestimo(self):
        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave1.pk],
        )
        novo = emprestimo.business.trocar_titular(
            self.operador,
            novo_solicitante_id=self.novo_solicitante.pk,
        )
        emprestimo.refresh_from_db()
        self.assertFalse(emprestimo.ativo)
        self.assertNotEqual(novo.pk, emprestimo.pk)
        self.assertEqual(novo.solicitante, self.novo_solicitante)
        self.assertTrue(novo.ativo)

    def test_atrasado_apos_24_horas(self):
        emprestimo = Emprestimo().business.realizar_emprestimo(
            solicitante_id=self.solicitante.pk,
            responsavel=self.operador,
            recurso_ids=[self.chave1.pk],
            retirada_em=timezone.now() - datetime.timedelta(hours=HORAS_ALERTA_ATRASO + 1),
        )
        self.assertTrue(emprestimo.atrasado)
