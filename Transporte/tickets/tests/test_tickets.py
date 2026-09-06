from datetime import timedelta
from unittest.mock import patch

from django.core import signing
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Academico.alunos.choices import SituacaoAluno
from AppCore.core.exceptions.exceptions import BusinessRuleException
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.strikes.helpers import sincronizar_faltas_transporte
from Transporte.strikes.models import Strike
from Transporte.tests_utils import (
    criar_aluno,
    criar_aluno_pcd,
    criar_rota_e_execucao,
    criar_strike,
    criar_usuario,
    obter_token,
)
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket
from Transporte.tickets.helpers import SALT_QR_TICKET
from Transporte.tickets.serializers import TicketSerializer
from Transporte.tickets.state import TicketCanceladoState


class TicketBusinessTestCase(APITestCase):

    def setUp(self):
        _, self.execucao = criar_rota_e_execucao(vagas=1)
        self.aluno = criar_aluno('20000000001', nome='Aluno comum')
        instante_aberto = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        patcher = patch('Transporte.tickets.rules.now', return_value=instante_aberto)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_solicitacoes_abrem_a_meia_noite_do_dia_da_execucao(self):
        abertura = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        antes_da_abertura = abertura - timedelta(microseconds=1)
        with patch('Transporte.tickets.rules.now', return_value=antes_da_abertura):
            with self.assertRaises(BusinessRuleException):
                Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)

        with patch('Transporte.tickets.rules.now', return_value=abertura):
            ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        self.assertEqual(ticket.status, StatusTicket.RESERVADO)

    def test_limite_exato_permite_reserva_e_entrada_na_fila(self):
        limite = self.execucao.data_hora_saida - timedelta(minutes=30)
        with patch('Transporte.tickets.rules.now', return_value=limite):
            Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
            outro = criar_aluno('20000000017')
            espera = Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)
        self.assertEqual(espera.status, StatusTicket.EM_ESPERA)

    def test_depois_do_limite_bloqueia_reserva_e_entrada_na_fila(self):
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        outro = criar_aluno('20000000018')
        depois_limite = self.execucao.data_hora_saida - timedelta(minutes=30) + timedelta(
            microseconds=1,
        )
        with patch('Transporte.tickets.rules.now', return_value=depois_limite):
            with self.assertRaises(BusinessRuleException):
                Ticket().business.solicitar_reserva(self.execucao.pk, outro.usuario)
            with self.assertRaises(BusinessRuleException):
                Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)

    def test_fim_de_semana_bloqueia_reserva(self):
        dias_ate_sabado = (5 - timezone.localdate().weekday()) % 7
        if dias_ate_sabado == 0:
            dias_ate_sabado = 7
        _, execucao = criar_rota_e_execucao(
            vagas=1,
            dias_ate_execucao=dias_ate_sabado,
        )
        instante = timezone.localtime(execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        with patch('Transporte.tickets.rules.now', return_value=instante):
            with self.assertRaises(BusinessRuleException):
                Ticket().business.solicitar_reserva(execucao.pk, self.aluno.usuario)

    def test_reserva_e_lotacao_exige_fila_explicita(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        self.assertEqual(ticket.status, StatusTicket.RESERVADO)

        outro = criar_aluno('20000000002')
        with self.assertRaises(BusinessRuleException) as contexto:
            Ticket().business.solicitar_reserva(self.execucao.pk, outro.usuario)
        self.assertIn('fila de espera', str(contexto.exception))

        espera = Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)
        self.assertEqual(espera.status, StatusTicket.EM_ESPERA)

    def test_nao_entra_na_fila_quando_ha_vaga(self):
        with self.assertRaises(BusinessRuleException):
            Ticket().business.entrar_fila(self.execucao.pk, self.aluno.usuario)

    def test_apenas_aluno_ativo_e_matriculado_reserva(self):
        self.aluno.situacao = SituacaoAluno.TRANCADO
        self.aluno.save(update_fields=['situacao'])
        with self.assertRaises(BusinessRuleException):
            Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)

    def test_apenas_aluno_ativo_e_matriculado_entra_fila(self):
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        outro = criar_aluno('20000000019', situacao=SituacaoAluno.TRANCADO)
        with self.assertRaises(BusinessRuleException):
            Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)

    def test_fila_prioriza_pcd_sem_deslocar_reserva(self):
        reservado = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        comum = criar_aluno('20000000003')
        pcd = criar_aluno_pcd('20000000004')
        ticket_comum = Ticket().business.entrar_fila(self.execucao.pk, comum.usuario)
        ticket_pcd = Ticket().business.entrar_fila(self.execucao.pk, pcd.usuario)

        self.assertEqual(ticket_pcd.business.obter_posicao_fila(), 1)
        self.assertEqual(ticket_comum.business.obter_posicao_fila(), 2)
        reservado.refresh_from_db()
        self.assertEqual(reservado.status, StatusTicket.RESERVADO)

    def test_reservas_expoem_posicao_com_prioridade_pcd_e_capacidade_total(self):
        _, execucao = criar_rota_e_execucao(vagas=3)
        comum = criar_aluno('20000000010')
        pcd = criar_aluno_pcd('20000000011')

        ticket_comum = Ticket().business.solicitar_reserva(execucao.pk, comum.usuario)
        ticket_pcd = Ticket().business.solicitar_reserva(execucao.pk, pcd.usuario)

        self.assertEqual(
            ticket_pcd.business.obter_posicao(),
            {'tipo': 'RESERVA', 'atual': 1, 'total': 3},
        )
        self.assertEqual(
            ticket_comum.business.obter_posicao(),
            {'tipo': 'RESERVA', 'atual': 2, 'total': 3},
        )
        self.assertIsNone(ticket_comum.business.obter_posicao_fila())

    def test_alterar_deficiencia_reposiciona_reservas_confirmadas(self):
        _, execucao = criar_rota_e_execucao(vagas=2)
        primeiro = criar_aluno('20000000012')
        segundo = criar_aluno('20000000013')
        ticket_primeiro = Ticket().business.solicitar_reserva(execucao.pk, primeiro.usuario)
        ticket_segundo = Ticket().business.solicitar_reserva(execucao.pk, segundo.usuario)
        self.assertEqual(ticket_segundo.business.obter_posicao()['atual'], 2)

        segundo.usuario.deficiencia = 'deficiencia_fisica'
        segundo.usuario.save(update_fields=['deficiencia'])

        self.assertEqual(ticket_segundo.business.obter_posicao()['atual'], 1)
        self.assertEqual(ticket_primeiro.business.obter_posicao()['atual'], 2)

    def test_posicao_de_espera_informa_quantidade_total_na_fila(self):
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        comum = criar_aluno('20000000014')
        pcd = criar_aluno_pcd('20000000015')
        ticket_comum = Ticket().business.entrar_fila(self.execucao.pk, comum.usuario)
        ticket_pcd = Ticket().business.entrar_fila(self.execucao.pk, pcd.usuario)

        self.assertEqual(
            ticket_pcd.business.obter_posicao(),
            {'tipo': 'ESPERA', 'atual': 1, 'total': 2},
        )
        self.assertEqual(
            ticket_comum.business.obter_posicao(),
            {'tipo': 'ESPERA', 'atual': 2, 'total': 2},
        )
        self.assertEqual(ticket_pcd.business.obter_posicao_fila(), 1)

    def test_alterar_deficiencia_reposiciona_fila(self):
        titular = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        primeiro = criar_aluno('20000000005')
        segundo = criar_aluno('20000000006')
        ticket_primeiro = Ticket().business.entrar_fila(self.execucao.pk, primeiro.usuario)
        ticket_segundo = Ticket().business.entrar_fila(self.execucao.pk, segundo.usuario)
        self.assertEqual(ticket_segundo.business.obter_posicao_fila(), 2)

        segundo.usuario.deficiencia = 'deficiencia_fisica'
        segundo.usuario.save(update_fields=['deficiencia'])
        self.assertEqual(ticket_segundo.business.obter_posicao_fila(), 1)
        self.assertEqual(ticket_primeiro.business.obter_posicao_fila(), 2)
        self.assertEqual(titular.status, StatusTicket.RESERVADO)

    def test_cancelamento_promove_primeiro_da_fila(self):
        reservado = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        comum = criar_aluno('20000000007')
        pcd = criar_aluno_pcd('20000000008')
        Ticket().business.entrar_fila(self.execucao.pk, comum.usuario)
        ticket_pcd = Ticket().business.entrar_fila(self.execucao.pk, pcd.usuario)

        _, promovido = reservado.business.cancelar(self.aluno.usuario)
        ticket_pcd.refresh_from_db()
        self.assertEqual(promovido.pk, ticket_pcd.pk)
        self.assertEqual(ticket_pcd.status, StatusTicket.RESERVADO)
        self.assertEqual(
            ticket_pcd.business.obter_posicao(),
            {'tipo': 'RESERVA', 'atual': 1, 'total': 1},
        )
        self.assertIsNone(ticket_pcd.business.obter_posicao_fila())

    def test_transicao_atualiza_timestamp_e_estado_em_cache(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        estado_reservado = ticket.state

        ticket, _ = ticket.business.cancelar(self.aluno.usuario)

        self.assertIsNotNone(ticket.cancelado_em)
        self.assertIsNot(ticket.state, estado_reservado)
        self.assertIsInstance(ticket.state, TicketCanceladoState)
        with self.assertRaises(BusinessRuleException):
            ticket.state.atualizar_status(StatusTicket.RESERVADO)

    def test_embarcado_conserva_posicao_de_reserva_e_cancelado_nao_tem_posicao(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        codigo_qr = ticket.business.gerar_codigo_qr()
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])

        ticket, _ = Ticket().business.validar_qr(codigo_qr)
        self.assertEqual(
            ticket.business.obter_posicao(),
            {'tipo': 'RESERVA', 'atual': 1, 'total': 1},
        )

        _, outra_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=21)
        outro = criar_aluno('20000000016')
        instante_aberto = timezone.localtime(outra_execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        with patch('Transporte.tickets.rules.now', return_value=instante_aberto):
            cancelado = Ticket().business.solicitar_reserva(outra_execucao.pk, outro.usuario)
            cancelado, _ = cancelado.business.cancelar(outro.usuario)
        self.assertIsNone(cancelado.business.obter_posicao())

    def test_limite_exato_de_trinta_minutos_permite_cancelar(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        instante_limite = self.execucao.data_hora_saida - timedelta(minutes=30)
        with patch('Transporte.tickets.rules.now', return_value=instante_limite):
            ticket.business.cancelar(self.aluno.usuario)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.CANCELADO)

    def test_depois_do_limite_nao_cancela(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        depois_limite = self.execucao.data_hora_saida - timedelta(minutes=29)
        with patch('Transporte.tickets.rules.now', return_value=depois_limite):
            with self.assertRaises(BusinessRuleException):
                ticket.business.cancelar(self.aluno.usuario)

    def test_nao_cancela_com_execucao_fechada(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        self.execucao.status = StatusExecucaoRota.FECHADA
        self.execucao.save(update_fields=['status'])

        with self.assertRaises(BusinessRuleException):
            ticket.business.cancelar(self.aluno.usuario)

    def test_nao_sai_da_fila_com_execucao_fechada(self):
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        outro = criar_aluno('20000000019')
        espera = Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)
        self.execucao.status = StatusExecucaoRota.FECHADA
        self.execucao.save(update_fields=['status'])

        with self.assertRaises(BusinessRuleException):
            espera.business.sair_fila(outro.usuario)

    def test_tres_strikes_bloqueiam_nova_reserva_sem_cancelar_existente(self):
        ticket_existente = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        for indice in range(3):
            _, outra_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=14 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=outra_execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            Strike.objects.create(ticket=ticket)
            sincronizar_faltas_transporte(self.aluno)

        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.is_bloqueado)
        _, nova_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=21)
        with self.assertRaises(BusinessRuleException):
            Ticket().business.solicitar_reserva(nova_execucao.pk, self.aluno.usuario)
        ticket_existente.refresh_from_db()
        self.assertEqual(ticket_existente.status, StatusTicket.RESERVADO)

    def test_tres_strikes_bloqueiam_entrada_na_fila_sem_cancelar_existente(self):
        ticket_existente = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        for indice in range(3):
            _, outra_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=22 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=outra_execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            Strike.objects.create(ticket=ticket)

        _, nova_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=25)
        ocupante = criar_aluno('20000000020')
        instante = timezone.localtime(nova_execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        with patch('Transporte.tickets.rules.now', return_value=instante):
            Ticket().business.solicitar_reserva(nova_execucao.pk, ocupante.usuario)
            with self.assertRaises(BusinessRuleException):
                Ticket().business.entrar_fila(nova_execucao.pk, self.aluno.usuario)
        ticket_existente.refresh_from_db()
        self.assertEqual(ticket_existente.status, StatusTicket.RESERVADO)

    def test_marcar_ausente_cria_um_strike(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])
        ticket, strike = ticket.business.marcar_ausente()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertEqual(strike.ticket_id, ticket.pk)
        self.assertEqual(Strike.objects.filter(ticket=ticket).count(), 1)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 1)
        self.assertFalse(self.aluno.is_bloqueado)
        with self.assertRaises(BusinessRuleException):
            ticket.business.marcar_ausente()

    def test_qr_valido_e_segunda_leitura_idempotente(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        codigo_qr = ticket.business.gerar_codigo_qr()
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])

        validado, repetido = Ticket().business.validar_qr(codigo_qr)
        self.assertFalse(repetido)
        self.assertEqual(validado.status, StatusTicket.EMBARCADO)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.helper.contar_vagas_ocupadas(), 1)
        self.assertEqual(self.execucao.helper.quantidade_vagas_disponiveis(), 0)
        _, repetido = Ticket().business.validar_qr(codigo_qr)
        self.assertTrue(repetido)

    def test_serializacao_reutiliza_consultas_de_posicao_por_execucao(self):
        _, execucao = criar_rota_e_execucao(vagas=3)
        alunos = [criar_aluno(f'2000000002{indice}') for indice in range(3)]
        for aluno in alunos:
            Ticket().business.solicitar_reserva(execucao.pk, aluno.usuario)
        tickets = list(Ticket.objects.filter(execucao_rota=execucao).select_related(
            'execucao_rota',
            'execucao_rota__rota',
            'execucao_rota__rota__percurso',
            'aluno',
            'aluno__usuario',
        ))

        with CaptureQueriesContext(connection) as consultas:
            TicketSerializer(tickets, many=True).data

        self.assertLessEqual(len(consultas), 3)

    def test_qr_adulterado_e_rejeitado(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        codigo_qr = ticket.business.gerar_codigo_qr()
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])
        with self.assertRaises(BusinessRuleException):
            Ticket().business.validar_qr(f'{codigo_qr}adulterado')

    def test_qr_de_ticket_cancelado_e_rejeitado(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        codigo_qr = ticket.business.gerar_codigo_qr()
        ticket.business.cancelar(self.aluno.usuario)
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])
        with self.assertRaises(BusinessRuleException):
            Ticket().business.validar_qr(codigo_qr)

    def test_qr_de_ticket_em_espera_e_rejeitado(self):
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        outro = criar_aluno('20000000009')
        ticket = Ticket().business.entrar_fila(self.execucao.pk, outro.usuario)
        codigo_qr = ticket.business.gerar_codigo_qr()
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])
        with self.assertRaises(BusinessRuleException):
            Ticket().business.validar_qr(codigo_qr)

    def test_qr_assinado_com_execucao_incorreta_e_rejeitado(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        codigo_qr = signing.dumps(
            {'ticket': str(ticket.codigo), 'execucao': self.execucao.pk + 999},
            salt=SALT_QR_TICKET,
            compress=True,
        )
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save(update_fields=['status'])
        with self.assertRaises(BusinessRuleException):
            Ticket().business.validar_qr(codigo_qr)


class TicketApiTestCase(APITestCase):

    def setUp(self):
        _, self.execucao = criar_rota_e_execucao(vagas=1)
        self.aluno = criar_aluno('21000000001')
        instante_aberto = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        patcher = patch('Transporte.tickets.rules.now', return_value=instante_aberto)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')

    def test_fluxo_reserva_listagem_detalhe(self):
        resposta = self.client.post(
            reverse('transporte:ticket-reservar', kwargs={'pk': self.execucao.pk}),
            {},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['codigo_qr'])
        self.assertEqual(
            resposta.data['dados']['posicao'],
            {'tipo': 'RESERVA', 'atual': 1, 'total': 1},
        )
        self.assertIsNone(resposta.data['dados']['posicao_fila'])
        codigo = resposta.data['dados']['codigo']

        listagem = self.client.get(reverse('transporte:ticket-list'))
        self.assertEqual(len(listagem.data['dados']), 1)
        detalhe = self.client.get(
            reverse('transporte:ticket-detalhe', kwargs={'codigo': codigo}),
        )
        self.assertEqual(detalhe.status_code, status.HTTP_200_OK)

    def test_outro_aluno_nao_ve_ticket(self):
        ticket = Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno.usuario)
        outro = criar_aluno('21000000002')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro.usuario)}')
        resposta = self.client.get(
            reverse('transporte:ticket-detalhe', kwargs={'codigo': ticket.codigo}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_validacao_qr_exige_l3(self):
        resposta = self.client.post(
            reverse('transporte:ticket-validar-qr'),
            {'codigo_qr': 'qualquer'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

        admin = criar_usuario('21000000003', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(
            reverse('transporte:ticket-validar-qr'),
            {'codigo_qr': 'invalido'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
