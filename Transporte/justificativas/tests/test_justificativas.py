from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.strikes.choices import StatusStrike
from Transporte.strikes.helpers import sincronizar_faltas_transporte
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_strike, criar_usuario, obter_token
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class JustificativaTestCase(APITestCase):

    def setUp(self):
        self.aluno = criar_aluno('30000000001')
        self.admin = criar_usuario('30000000002', admin=True)
        self.strikes = []
        for indice in range(3):
            _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=7 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            self.strikes.append(criar_strike(ticket))
        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.is_bloqueado)

    def test_aluno_bloqueado_envia_e_admin_aprova(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        justificativa.business.analisar(True, self.admin, 'Documento conferido.')
        justificativa.refresh_from_db()
        self.strikes[0].refresh_from_db()
        self.aluno.refresh_from_db()
        self.assertEqual(justificativa.status, StatusJustificativa.APROVADA)
        self.assertEqual(self.strikes[0].status, StatusStrike.JUSTIFICADO)
        self.assertFalse(self.aluno.is_bloqueado)

    def test_rejeicao_mantem_strike_ativo(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Justificativa válida para análise inicial.',
        )
        justificativa.business.analisar(False, self.admin, 'Documento insuficiente.')
        self.strikes[0].refresh_from_db()
        self.aluno.refresh_from_db()
        self.assertEqual(self.strikes[0].status, StatusStrike.ATIVO)
        self.assertTrue(self.aluno.is_bloqueado)

    def test_aprovar_justificativa_com_novos_strikes_posteriores_mantem_bloqueio(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        for indice in range(3):
            _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=20 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            criar_strike(ticket)
        justificativa.business.analisar(True, self.admin)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 3)
        self.assertTrue(self.aluno.is_bloqueado)

    def test_outro_aluno_nao_justifica(self):
        outro = criar_aluno('30000000003')
        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                outro.usuario,
                'Tentativa de justificar bloqueio de outra pessoa.',
            )

    def test_nao_bloqueado_nao_envia_justificativa(self):
        self.aluno.faltas = 1
        self.aluno.is_bloqueado = False
        self.aluno.save(update_fields=['faltas', 'is_bloqueado'])
        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.aluno.usuario,
                'Tentativa de justificar sem estar bloqueado.',
            )

    def test_nao_envia_duas_justificativas_pendentes(self):
        Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Primeira justificativa enviada para análise.',
        )
        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.aluno.usuario,
                'Segunda justificativa pendente.',
            )

    def test_business_rejeita_texto_muito_curto(self):
        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.aluno.usuario,
                'curto',
            )

    def test_fluxo_api(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.post(
            reverse('transporte:bloqueio-justificativa-criar'),
            {'texto': 'Estava em atendimento médico emergencial.'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        justificativa_id = resposta.data['dados']['id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.post(
            reverse('transporte:justificativa-aprovar', kwargs={'pk': justificativa_id}),
            {'observacao_analise': 'Documento aceito.'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['status'], StatusJustificativa.APROVADA)

    def test_aluno_detalha_justificativa_propria(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.get(
            reverse('transporte:justificativa-detalhe', kwargs={'pk': justificativa.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], justificativa.pk)

    def test_justificativa_cobre_todos_strikes_ativos(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Justificativa cobrindo todos os strikes ativos.',
        )
        self.assertEqual(justificativa.strikes_cobertos.count(), 3)

    def test_outro_aluno_nao_detalha_e_l3_detalha(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        outro = criar_aluno('30000000004')
        url = reverse('transporte:justificativa-detalhe', kwargs={'pk': justificativa.pk})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro.usuario)}')
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
