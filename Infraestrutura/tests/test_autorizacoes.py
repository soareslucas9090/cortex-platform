import datetime

from django.test import TestCase

from Identidade.usuarios.models import Usuario
from Infraestrutura.autorizacoes.models import Autorizacao
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_autorizar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'AUT_{usuario.cpf}', descricao='Autorizador')
    setor = Setor.objects.create(sigla=f'A{usuario.cpf[-3:]}', nome='Setor Autorizador')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, autorizar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class AutorizacaoRulesTest(TestCase):

    def setUp(self):
        self.beneficiario = criar_usuario('44444444444', nome='Beneficiário')
        self.autorizador = conceder_capacidade_autorizar(
            criar_usuario('55555555555', nome='Autorizador'),
        )
        self.bloco = Bloco.objects.create(nome='Bloco Aut')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Aut')
        self.recurso = Recurso.objects.create(
            codigo='CHV-AUT',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        self.hoje = datetime.date.today()

    def test_xor_rejeita_sala_e_recurso_juntos(self):
        with self.assertRaises(Exception):
            Autorizacao().business.conceder_autorizacao(
                beneficiario_id=self.beneficiario.pk,
                concedente=self.autorizador,
                sala_id=self.sala.pk,
                recurso_id=self.recurso.pk,
                data_inicio=self.hoje,
            )

    def test_xor_rejeita_sem_alvo(self):
        with self.assertRaises(Exception):
            Autorizacao().business.conceder_autorizacao(
                beneficiario_id=self.beneficiario.pk,
                concedente=self.autorizador,
                data_inicio=self.hoje,
            )

    def test_sem_capacidade_autorizar_nao_concede(self):
        sem_permissao = criar_usuario('66666666666', nome='Sem Permissão')
        with self.assertRaises(Exception):
            Autorizacao().business.conceder_autorizacao(
                beneficiario_id=self.beneficiario.pk,
                concedente=sem_permissao,
                sala_id=self.sala.pk,
                data_inicio=self.hoje,
            )

    def test_rejeita_autorizacao_duplicada_mesmo_periodo(self):
        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        with self.assertRaises(Exception):
            Autorizacao().business.conceder_autorizacao(
                beneficiario_id=self.beneficiario.pk,
                concedente=self.autorizador,
                recurso_id=self.recurso.pk,
                data_inicio=self.hoje,
                data_fim=None,
            )

    def test_rejeita_periodo_sobreposto(self):
        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=self.hoje + datetime.timedelta(days=30),
        )
        with self.assertRaises(Exception):
            Autorizacao().business.conceder_autorizacao(
                beneficiario_id=self.beneficiario.pk,
                concedente=self.autorizador,
                recurso_id=self.recurso.pk,
                data_inicio=self.hoje + datetime.timedelta(days=15),
                data_fim=self.hoje + datetime.timedelta(days=45),
            )

    def test_permite_novo_periodo_apos_revogacao(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        autorizacao.business.revogar(self.autorizador)
        nova = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        self.assertNotEqual(autorizacao.pk, nova.pk)

    def test_reativar_autorizacao_revogada(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        autorizacao.business.revogar(self.autorizador)
        autorizacao.business.reativar(self.autorizador)
        autorizacao.refresh_from_db()
        self.assertIsNone(autorizacao.revogado_em)
        self.assertIsNone(autorizacao.revogador)
        self.assertTrue(autorizacao.vigente)

    def test_reativar_rejeita_se_ha_sobreposicao_com_outra_vigente(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        autorizacao.business.revogar(self.autorizador)
        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        with self.assertRaises(Exception):
            autorizacao.business.reativar(self.autorizador)

    def test_reativar_rejeita_autorizacao_ja_vigente(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        with self.assertRaises(Exception):
            autorizacao.business.reativar(self.autorizador)

    def test_permite_periodos_sequenciais_sem_sobreposicao(self):
        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje,
            data_fim=self.hoje + datetime.timedelta(days=10),
        )
        nova = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            recurso_id=self.recurso.pk,
            data_inicio=self.hoje + datetime.timedelta(days=11),
            data_fim=self.hoje + datetime.timedelta(days=20),
        )
        self.assertIsNotNone(nova.pk)


class AutorizacaoVigenciaTest(TestCase):

    def setUp(self):
        self.beneficiario = criar_usuario('77777777777', nome='Benef Vigência')
        self.autorizador = conceder_capacidade_autorizar(
            criar_usuario('88888888888', nome='Autorizador Vigência'),
        )
        self.bloco = Bloco.objects.create(nome='Bloco Vig')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Vig')
        self.hoje = datetime.date.today()

    def test_autorizacao_temporaria_expirada_nao_e_vigente(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            sala_id=self.sala.pk,
            data_inicio=self.hoje - datetime.timedelta(days=10),
            data_fim=self.hoje - datetime.timedelta(days=1),
        )
        self.assertFalse(autorizacao.vigente)

    def test_autorizacao_permanente_e_vigente(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            sala_id=self.sala.pk,
            data_inicio=self.hoje,
            data_fim=None,
        )
        self.assertTrue(autorizacao.vigente)

    def test_revogacao_encerra_vigencia(self):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            sala_id=self.sala.pk,
            data_inicio=self.hoje,
        )
        autorizacao.business.revogar(self.autorizador)
        autorizacao.refresh_from_db()
        self.assertIsNotNone(autorizacao.revogado_em)
        self.assertEqual(autorizacao.revogador, self.autorizador)
        self.assertFalse(autorizacao.vigente)


class AutorizacaoSalaCobreRecursoTest(TestCase):

    def setUp(self):
        self.beneficiario = criar_usuario('99999999999', nome='Benef Sala')
        self.autorizador = conceder_capacidade_autorizar(
            criar_usuario('10101010101', nome='Autorizador Sala'),
        )
        self.bloco = Bloco.objects.create(nome='Bloco Cobertura')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Cobertura')
        self.hoje = datetime.date.today()

    def test_autorizacao_por_sala_cobre_recurso_novo(self):
        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.beneficiario.pk,
            concedente=self.autorizador,
            sala_id=self.sala.pk,
            data_inicio=self.hoje,
        )
        recurso_novo = Recurso.objects.create(
            codigo='CHV-NOVO',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        helper = Autorizacao().helper
        self.assertTrue(
            helper.usuario_tem_autorizacao_vigente_para_recurso(self.beneficiario, recurso_novo),
        )
