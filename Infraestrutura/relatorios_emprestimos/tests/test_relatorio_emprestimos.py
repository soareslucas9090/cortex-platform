import datetime
from datetime import date, time
from unittest import mock
from zoneinfo import ZoneInfo

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import ValidationException
from Identidade.usuarios.models import TipoContaColetiva, Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.emprestimos.choices import OrigemContaColetiva
from Infraestrutura.emprestimos.helpers import FUSO_HORARIO_EMPRESTIMOS
from Infraestrutura.emprestimos.models import Emprestimo, ItemEmprestimo
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura, PermissaoUsuarioInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.relatorios_emprestimos.constantes import LIMITE_EMPRESTIMOS_RELATORIO
from Infraestrutura.relatorios_emprestimos.models import RelatorioEmprestimos
from Infraestrutura.salas.models import Sala
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_operar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'OP_{usuario.cpf}', descricao='Operador')
    setor = Setor.objects.create(sigla=f'O{usuario.cpf[-3:]}', nome='Setor Operador')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, operar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class RelatorioEmprestimosBaseTest(APITestCase):

    def setUp(self):
        self.operador = conceder_capacidade_operar(criar_usuario('52000000001', nome='Operador Rel'))
        self.solicitante_a = criar_usuario('52000000002', nome='Solicitante A')
        self.solicitante_b = criar_usuario('52000000003', nome='Solicitante B')
        self.responsavel = criar_usuario('52000000004', nome='Responsável Rel')
        self.token_operador = obter_tokens(self.operador)
        self.bloco_a = Bloco.objects.create(nome='Bloco Rel A')
        self.bloco_b = Bloco.objects.create(nome='Bloco Rel B')
        self.sala_a = Sala.objects.create(bloco=self.bloco_a, nome='Sala Rel A')
        self.sala_b = Sala.objects.create(bloco=self.bloco_b, nome='Sala Rel B')
        self.url_pdf = reverse('infraestrutura:emprestimos-relatorio-pdf')
        self.url_pessoas = reverse('infraestrutura:emprestimos-relatorio-pessoas')
        self._contador = 0

    def _recurso(self, *, tipo=TipoRecurso.CHAVE, sala=None, codigo=None):
        self._contador += 1
        return Recurso.objects.create(
            codigo=codigo or f'REL-{self._contador}',
            tipo=tipo,
            sala=sala if tipo == TipoRecurso.CHAVE else None,
        )

    def _retirada_em(self, dia: date, hora=10):
        return datetime.datetime.combine(dia, time(hora, 0), tzinfo=FUSO_HORARIO_EMPRESTIMOS)

    def _criar_emprestimo(
        self,
        *,
        dia,
        solicitante=None,
        responsavel=None,
        origem=None,
        recursos=None,
    ):
        solicitante = solicitante or self.solicitante_a
        responsavel = responsavel or self.responsavel
        emprestimo = Emprestimo.objects.create(
            solicitante=solicitante,
            responsavel=responsavel,
            retirada_em=self._retirada_em(dia),
            origem_conta_coletiva=origem,
        )
        for recurso in recursos or [self._recurso(sala=self.sala_a)]:
            ItemEmprestimo.objects.create(emprestimo=emprestimo, recurso=recurso)
        return emprestimo

    def _params_periodo(self, inicio='2026-03-01', fim='2026-03-31', **extra):
        return {'data_inicio': inicio, 'data_fim': fim, **extra}


class RelatorioEmprestimosAutenticacaoTest(RelatorioEmprestimosBaseTest):

    def test_pdf_401_sem_token(self):
        resposta = self.client.get(self.url_pdf, self._params_periodo())
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pessoas_401_sem_token(self):
        resposta = self.client.get(self.url_pessoas, {'papel': 'solicitante'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pdf_403_sem_operar(self):
        usuario = criar_usuario('52000000010')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(usuario)}')
        resposta = self.client.get(self.url_pdf, self._params_periodo())
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_pessoas_403_sem_operar(self):
        usuario = criar_usuario('52000000011')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(usuario)}')
        resposta = self.client.get(self.url_pessoas, {'papel': 'solicitante'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)


class RelatorioEmprestimosPdfValidacaoTest(RelatorioEmprestimosBaseTest):

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        self._criar_emprestimo(dia=date(2026, 3, 10))

    def test_pdf_200_operador(self):
        resposta = self.client.get(self.url_pdf, self._params_periodo())
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')
        self.assertTrue(resposta.content.startswith(b'%PDF-'))
        self.assertIn('relatorio-emprestimos_2026-03-01_a_2026-03-31.pdf', resposta['Content-Disposition'])
        self.assertEqual(resposta['Cache-Control'], 'no-store')

    def test_pdf_400_sem_datas(self):
        resposta = self.client.get(self.url_pdf, {})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pdf_400_inicio_maior_que_fim(self):
        resposta = self.client.get(
            self.url_pdf,
            {'data_inicio': '2026-03-10', 'data_fim': '2026-03-01'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pdf_400_31_dias(self):
        resposta = self.client.get(
            self.url_pdf,
            {'data_inicio': '2026-03-01', 'data_fim': '2026-04-01'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pdf_200_exatamente_30_dias(self):
        resposta = self.client.get(self.url_pdf, self._params_periodo('2026-03-01', '2026-03-31'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_pdf_200_virada_mes_30_dias(self):
        resposta = self.client.get(self.url_pdf, self._params_periodo('2026-03-20', '2026-04-19'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_pdf_400_sala_fora_do_bloco(self):
        resposta = self.client.get(
            self.url_pdf,
            self._params_periodo(bloco_id=self.bloco_a.pk, sala_id=self.sala_b.pk),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)


class RelatorioEmprestimosHelperQuerysetTest(RelatorioEmprestimosBaseTest):

    def setUp(self):
        super().setUp()
        self.chave_a = self._recurso(sala=self.sala_a)
        self.chave_b = self._recurso(sala=self.sala_b)
        self.midia = self._recurso(tipo=TipoRecurso.MIDIA)
        self.emp_a = self._criar_emprestimo(
            dia=date(2026, 3, 5),
            solicitante=self.solicitante_a,
            recursos=[self.chave_a],
        )
        self.emp_b = self._criar_emprestimo(
            dia=date(2026, 3, 8),
            solicitante=self.solicitante_b,
            responsavel=self.operador,
            recursos=[self.chave_b, self.midia],
        )
        self.emp_fora = self._criar_emprestimo(dia=date(2026, 4, 1), recursos=[self.chave_a])
        self.filtros_base = {'data_inicio': date(2026, 3, 1), 'data_fim': date(2026, 3, 31)}

    def _ids(self, **extra):
        filtros = {**self.filtros_base, **extra}
        qs = RelatorioEmprestimos().helper.listar_emprestimos(self.operador, filtros)
        return list(qs.values_list('pk', flat=True))

    def test_filtro_solicitante(self):
        ids = self._ids(solicitante_id=self.solicitante_a.pk)
        self.assertEqual(ids, [self.emp_a.pk])

    def test_filtro_responsavel(self):
        ids = self._ids(responsavel_id=self.operador.pk)
        self.assertEqual(ids, [self.emp_b.pk])

    def test_filtro_tipo_recurso_exclui_emprestimo_sem_item_casando(self):
        ids = self._ids(tipo_recurso=TipoRecurso.MIDIA)
        self.assertEqual(ids, [self.emp_b.pk])
        emp = RelatorioEmprestimos().helper.listar_emprestimos(
            self.operador,
            {**self.filtros_base, 'tipo_recurso': TipoRecurso.MIDIA},
        ).get(pk=self.emp_b.pk)
        tipos = [item.recurso.tipo for item in emp.itens.all()]
        self.assertEqual(tipos, [TipoRecurso.MIDIA])

    def test_filtro_sala_id(self):
        ids = self._ids(sala_id=self.sala_a.pk)
        self.assertEqual(ids, [self.emp_a.pk])

    def test_filtro_bloco_id(self):
        ids = self._ids(bloco_id=self.bloco_b.pk)
        self.assertEqual(ids, [self.emp_b.pk])

    def test_periodo_exclui_fora_do_intervalo(self):
        ids = self._ids()
        self.assertIn(self.emp_a.pk, ids)
        self.assertIn(self.emp_b.pk, ids)
        self.assertNotIn(self.emp_fora.pk, ids)


class RelatorioEmprestimosEscopoColetivoTest(RelatorioEmprestimosBaseTest):

    def _criar_conta_coletiva(self, cpf, nome, tipo, sigla):
        conta = Usuario.objects.create_user(
            cpf=cpf,
            password='Senha@123',
            nome=nome,
            usuario_coletivo=True,
            tipo_conta_coletiva=tipo,
        )
        PermissaoUsuarioInfraestrutura.objects.create(usuario=conta, operar=True)
        setor = Setor.objects.create(sigla=sigla, nome=nome)
        conta.setores_coletivo.add(setor)
        return conta

    def setUp(self):
        super().setUp()
        self.guarita = self._criar_conta_coletiva(
            '52000000020',
            'Guarita Rel',
            TipoContaColetiva.GUARITA,
            'GRL',
        )
        self.admin = Usuario.objects.create_user(
            cpf='52000000021',
            password='Senha@123',
            nome='Admin Rel',
            is_admin=True,
            is_staff=True,
        )
        chave = self._recurso(sala=self.sala_a)
        self.emp_guarita = self._criar_emprestimo(
            dia=date(2026, 3, 12),
            origem=OrigemContaColetiva.GUARITA,
            recursos=[chave],
        )
        self.emp_codis = self._criar_emprestimo(
            dia=date(2026, 3, 12),
            origem=OrigemContaColetiva.CODIS,
            recursos=[self._recurso(sala=self.sala_a)],
        )
        self.emp_null = self._criar_emprestimo(
            dia=date(2026, 3, 12),
            origem=None,
            recursos=[self._recurso(sala=self.sala_a)],
        )
        self.filtros = {'data_inicio': date(2026, 3, 1), 'data_fim': date(2026, 3, 31)}

    def _ids_para(self, usuario):
        qs = RelatorioEmprestimos().helper.listar_emprestimos(usuario, self.filtros)
        return set(qs.values_list('pk', flat=True))

    def test_guarita_nao_ve_codis_nem_null(self):
        ids = self._ids_para(self.guarita)
        self.assertIn(self.emp_guarita.pk, ids)
        self.assertNotIn(self.emp_codis.pk, ids)
        self.assertNotIn(self.emp_null.pk, ids)

    def test_admin_ve_todos(self):
        ids = self._ids_para(self.admin)
        self.assertIn(self.emp_guarita.pk, ids)
        self.assertIn(self.emp_codis.pk, ids)
        self.assertIn(self.emp_null.pk, ids)


class RelatorioEmprestimosPessoasTest(RelatorioEmprestimosBaseTest):

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        self.inativo = criar_usuario('52000000030', nome='Inativo Antigo')
        self.inativo.ativo = False
        self.inativo.save(update_fields=['ativo'])
        self._criar_emprestimo(dia=date(2026, 3, 7), solicitante=self.inativo)
        self._criar_emprestimo(dia=date(2026, 3, 8), solicitante=self.solicitante_a, responsavel=self.solicitante_b)

    def test_papel_obrigatorio(self):
        resposta = self.client.get(self.url_pessoas, {})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papel_solicitante(self):
        resposta = self.client.get(self.url_pessoas, {'papel': 'solicitante'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.inativo.pk, ids)
        self.assertIn(self.solicitante_a.pk, ids)
        self.assertNotIn(self.solicitante_b.pk, ids)

    def test_filtro_nome_icontains(self):
        resposta = self.client.get(self.url_pessoas, {'papel': 'solicitante', 'nome': 'inativo'})
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertEqual(ids, [self.inativo.pk])


class RelatorioEmprestimosRulesTest(APITestCase):

    def test_validar_periodo_inicio_maior(self):
        rules = RelatorioEmprestimos().rules
        with self.assertRaises(ValidationException):
            rules.validar_periodo(date(2026, 3, 10), date(2026, 3, 1))

    def test_validar_periodo_30_dias_ok(self):
        rules = RelatorioEmprestimos().rules
        self.assertTrue(rules.validar_periodo(date(2026, 3, 1), date(2026, 3, 31)))

    def test_validar_periodo_31_dias_falha(self):
        rules = RelatorioEmprestimos().rules
        with self.assertRaises(ValidationException):
            rules.validar_periodo(date(2026, 3, 1), date(2026, 4, 1))

    def test_validar_quantidade_limite(self):
        rules = RelatorioEmprestimos().rules
        self.assertTrue(rules.validar_quantidade(LIMITE_EMPRESTIMOS_RELATORIO))
        with self.assertRaises(ValidationException):
            rules.validar_quantidade(LIMITE_EMPRESTIMOS_RELATORIO + 1)

    def test_validar_quantidade_via_business_mock(self):
        operador = mock.Mock()
        operador.nome = 'Op'
        operador.usuario_coletivo = False
        from Infraestrutura.relatorios_emprestimos.helpers import RelatorioEmprestimosHelpers

        with mock.patch.object(
            RelatorioEmprestimosHelpers,
            'listar_emprestimos',
        ) as listar_mock:
            qs_mock = mock.Mock()
            qs_mock.count.return_value = LIMITE_EMPRESTIMOS_RELATORIO + 1
            listar_mock.return_value = qs_mock
            with self.assertRaises(ValidationException):
                RelatorioEmprestimos().business.gerar_pdf(
                    operador,
                    {'data_inicio': date(2026, 3, 1), 'data_fim': date(2026, 3, 2)},
                )