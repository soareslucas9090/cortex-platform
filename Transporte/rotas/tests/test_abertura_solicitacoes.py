from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.rotas.admin import RotaAdmin
from Transporte.rotas.choices import DiaSemana
from Transporte.rotas.models import Rota
from Transporte.tests_utils import criar_aluno, criar_usuario, obter_token
from Transporte.percursos.models import Percurso
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class AberturaSolicitacoesTestCase(APITestCase):
    data = date(2026, 8, 3)

    def setUp(self):
        self.admin = criar_usuario('51000000001', admin=True)
        self.aluno = criar_aluno('51000000002')
        self.outro_aluno = criar_aluno('51000000003')
        self.percurso = Percurso.objects.create(apelido='Abertura', descricao='Teste')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')

    def instante(self, dia, horario):
        return timezone.make_aware(datetime.combine(dia, horario))

    def criar_rota(self, abertura=time(8), saida=time(12), vagas=1):
        return Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=saida,
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=vagas,
            horario_abertura_solicitacoes=abertura,
        )

    def payload(self, **alteracoes):
        dados = {
            'percurso_id': self.percurso.pk,
            'horario_saida': '12:00',
            'dia_semana': DiaSemana.SEGUNDA,
            'quantidade_vagas': 40,
            'horario_abertura_solicitacoes': '08:15:30',
        }
        dados.update(alteracoes)
        return dados

    def test_api_cadastra_consulta_e_edita_abertura(self):
        resposta = self.client.post(reverse('transporte:rotas'), self.payload(), format='json')
        self.assertEqual(resposta.status_code, 201)
        dados = resposta.data['dados']
        self.assertEqual(dados['horario_abertura_solicitacoes'], '08:15:30')
        rota = Rota.objects.get(pk=dados['id'])
        self.assertEqual(rota.history.first().horario_abertura_solicitacoes, time(8, 15, 30))
        url = reverse('transporte:rota-detalhe', kwargs={'pk': rota.pk})
        self.assertEqual(
            self.client.get(reverse('transporte:rotas')).data['dados'][0]['horario_abertura_solicitacoes'],
            '08:15:30',
        )
        resposta = self.client.patch(url, {
            'horario_abertura_solicitacoes': '22:00',
        }, format='json')
        self.assertEqual(resposta.status_code, 200)
        rota.refresh_from_db()
        self.assertEqual(rota.horario_abertura_solicitacoes, time(22))

    def test_api_rejeita_horario_de_abertura_ausente(self):
        payload = self.payload()
        del payload['horario_abertura_solicitacoes']
        resposta = self.client.post(reverse('transporte:rotas'), payload, format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_api_rejeita_horarios_e_antecedencias_invalidos(self):
        for alteracoes in (
            {'horario_abertura_solicitacoes': '25:00'},
            {'horario_abertura_solicitacoes': None},
            {'horario_abertura_solicitacoes': '11:30:01'},
        ):
            with self.subTest(alteracoes=alteracoes):
                resposta = self.client.post(
                    reverse('transporte:rotas'), self.payload(**alteracoes), format='json',
                )
                self.assertEqual(resposta.status_code, 400)
        self.assertFalse(Rota.objects.exists())

    def test_api_aluno_nao_pode_configurar_abertura(self):
        rota = self.criar_rota()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        self.assertEqual(self.client.post(
            reverse('transporte:rotas'), self.payload(), format='json',
        ).status_code, 403)
        self.assertEqual(self.client.patch(
            reverse('transporte:rota-detalhe', kwargs={'pk': rota.pk}),
            {'horario_abertura_solicitacoes': '07:00'}, format='json',
        ).status_code, 403)

    def test_admin_persiste_campos_na_criacao(self):
        rota = Rota(
            percurso=self.percurso, horario_saida=time(12), dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=10, horario_abertura_solicitacoes=time(9),
        )
        RotaAdmin(Rota, AdminSite()).save_model(None, rota, SimpleNamespace(), False)
        rota.refresh_from_db()
        self.assertEqual(rota.horario_abertura_solicitacoes, time(9))

    def test_validacao_reavalia_combinacao_em_patch_parcial(self):
        rota = self.criar_rota(abertura=time(11))
        with self.assertRaises(BusinessRuleException):
            rota.business.atualizar_dados({'horario_saida': time(11, 15)})
        rota.refresh_from_db()
        self.assertEqual(rota.horario_saida, time(12))
        rota = self.criar_rota(abertura=time(23), saida=time(13))
        with self.assertRaises(BusinessRuleException):
            rota.business.atualizar_dados({'horario_saida': time(12, 30)})

    def test_abertura_no_limite_e_viagem_apos_meia_noite(self):
        self.criar_rota(abertura=time(11, 30))
        self.criar_rota(abertura=time(23, 40), saida=time(0, 10))
        with self.assertRaises(BusinessRuleException):
            self.criar_rota(abertura=time(23, 40, 1), saida=time(0, 10))
        with self.assertRaises(BusinessRuleException):
            self.criar_rota(abertura=time(0), saida=time(0, 10))

    def test_reserva_fila_cancelamento_e_saida_respeitam_abertura_exata(self):
        for abertura, saida, antecedencia in ((time(8, 15, 30), time(12), 0), (time(22, 15, 30), time(12), 1)):
            with self.subTest(dia_abertura=antecedencia):
                rota = self.criar_rota(abertura=abertura, saida=saida)
                execucao = ExecucaoRota().business.criar_execucao(rota.pk, self.data)
                abertura = self.instante(
                    self.data - timedelta(days=antecedencia),
                    abertura.time() if hasattr(abertura, 'time') else abertura,
                )
                with patch('Transporte.tickets.rules.now', return_value=abertura - timedelta(microseconds=1)):
                    for acao in ('solicitar_reserva', 'entrar_fila'):
                        with self.assertRaises(BusinessRuleException):
                            getattr(Ticket().business, acao)(execucao.pk, self.aluno.usuario)
                with patch('Transporte.tickets.rules.now', return_value=abertura):
                    reserva = Ticket().business.solicitar_reserva(execucao.pk, self.aluno.usuario)
                    espera = Ticket().business.entrar_fila(execucao.pk, self.outro_aluno.usuario)
                with patch('Transporte.tickets.rules.now', return_value=abertura - timedelta(microseconds=1)):
                    with self.assertRaises(BusinessRuleException):
                        reserva.business.cancelar(self.aluno.usuario)
                    with self.assertRaises(BusinessRuleException):
                        espera.business.sair_fila(self.outro_aluno.usuario)
                with patch('Transporte.tickets.rules.now', return_value=abertura):
                    espera.business.sair_fila(self.outro_aluno.usuario)
                    reserva.business.cancelar(self.aluno.usuario)
                reserva.refresh_from_db()
                espera.refresh_from_db()
                self.assertEqual(reserva.status, StatusTicket.CANCELADO)
                self.assertEqual(espera.status, StatusTicket.CANCELADO)

    def test_limite_final_independe_da_abertura_personalizada(self):
        rota = self.criar_rota()
        execucao = ExecucaoRota().business.criar_execucao(rota.pk, self.data)
        limite = execucao.data_hora_saida - timedelta(minutes=30)
        with patch('Transporte.tickets.rules.now', return_value=limite):
            reserva = Ticket().business.solicitar_reserva(execucao.pk, self.aluno.usuario)
            espera = Ticket().business.entrar_fila(execucao.pk, self.outro_aluno.usuario)
        with patch('Transporte.tickets.rules.now', return_value=limite + timedelta(microseconds=1)):
            with self.assertRaises(BusinessRuleException):
                reserva.business.cancelar(self.aluno.usuario)
            with self.assertRaises(BusinessRuleException):
                espera.business.sair_fila(self.outro_aluno.usuario)
            with self.assertRaises(BusinessRuleException):
                Ticket().business.solicitar_reserva(execucao.pk, self.outro_aluno.usuario)

    def test_listagem_filtra_abertura_por_rota_e_preserva_acesso_admin(self):
        anterior = self.criar_rota(abertura=time(22), saida=time(10))
        mesmo_dia = self.criar_rota(abertura=time(8), saida=time(11))
        exec_anterior = ExecucaoRota().business.criar_execucao(anterior.pk, self.data)
        exec_mesmo_dia = ExecucaoRota().business.criar_execucao(mesmo_dia.pk, self.data)
        cenarios = (
            (self.instante(self.data - timedelta(days=1), time(21, 59, 59)), []),
            (self.instante(self.data - timedelta(days=1), time(22)), [exec_anterior.pk]),
            (self.instante(self.data, time(7, 59, 59)), [exec_anterior.pk]),
            (self.instante(self.data, time(8)), [exec_anterior.pk, exec_mesmo_dia.pk]),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        for instante, esperados in cenarios:
            with self.subTest(instante=instante), patch(
                'Transporte.execucoes_rotas.business.timezone.now', return_value=instante,
            ), patch('Transporte.execucoes_rotas.helpers.now', return_value=instante):
                resposta = self.client.get(reverse('transporte:execucao-rota-list'))
                self.assertEqual(resposta.status_code, 200)
                self.assertCountEqual([dado['id'] for dado in resposta.data['dados']], esperados)
                self.assertEqual(ExecucaoRota().business.listar_para_usuario(self.admin).count(), 2)

    def test_geracao_automatica_individualizada_e_idempotente(self):
        anterior = self.criar_rota(abertura=time(10), saida=time(11))
        mesmo_dia = self.criar_rota(abertura=time(8), saida=time(12))
        business = ExecucaoRota().business
        business.gerar_execucoes_automaticas(self.instante(self.data - timedelta(days=1), time(9, 59, 59)))
        self.assertFalse(ExecucaoRota.objects.exists())
        business.gerar_execucoes_automaticas(self.instante(self.data - timedelta(days=1), time(10)))
        self.assertEqual(list(ExecucaoRota.objects.values_list('rota_id', flat=True)), [anterior.pk])
        business.gerar_execucoes_automaticas(self.instante(self.data, time(7, 59, 59)))
        self.assertFalse(ExecucaoRota.objects.filter(rota=mesmo_dia).exists())
        for _ in range(2):
            business.gerar_execucoes_automaticas(self.instante(self.data, time(8)))
        self.assertEqual(ExecucaoRota.objects.count(), 2)

    def test_edicao_da_abertura_afeta_execucao_aberta_sem_apagar_ticket(self):
        rota = self.criar_rota()
        execucao = ExecucaoRota().business.criar_execucao(rota.pk, self.data)
        with patch('Transporte.tickets.rules.now', return_value=self.instante(self.data, time(8))):
            ticket = Ticket().business.solicitar_reserva(execucao.pk, self.aluno.usuario)
        rota.business.atualizar_dados({'horario_abertura_solicitacoes': time(9)})
        with patch('Transporte.tickets.rules.now', return_value=self.instante(self.data, time(8, 30))):
            with self.assertRaises(BusinessRuleException):
                Ticket().business.entrar_fila(execucao.pk, self.outro_aluno.usuario)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.RESERVADO)
        with patch('Transporte.tickets.rules.now', return_value=self.instante(self.data, time(9))):
            espera = Ticket().business.entrar_fila(execucao.pk, self.outro_aluno.usuario)
        self.assertEqual(espera.status, StatusTicket.EM_ESPERA)
