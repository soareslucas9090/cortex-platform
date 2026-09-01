from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import AuthorizationException, BusinessRuleException
from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.justificativas.serializers import JustificativaSerializer
from Transporte.strikes.choices import StatusStrike
from Transporte.strikes.models import Strike
from Transporte.strikes.serializers import StrikeSerializer
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_usuario, obter_token
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
            self.strikes.append(Strike.objects.create(ticket=ticket))

    def test_aluno_bloqueado_envia_e_admin_aprova(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Estava em atendimento médico emergencial.',
            self.aluno.usuario,
        )
        justificativa.business.analisar(True, self.admin, 'Documento conferido.')
        justificativa.refresh_from_db()
        self.strikes[0].refresh_from_db()
        self.assertEqual(justificativa.status, StatusJustificativa.APROVADA)
        self.assertEqual(self.strikes[0].status, StatusStrike.JUSTIFICADO)
        self.assertFalse(self.strikes[0].helper.aluno_esta_bloqueado())

    def test_rejeicao_mantem_strike_ativo(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Justificativa válida para análise inicial.',
            self.aluno.usuario,
        )
        justificativa.business.analisar(False, self.admin, 'Documento insuficiente.')
        self.strikes[0].refresh_from_db()
        self.assertEqual(self.strikes[0].status, StatusStrike.ATIVO)
        self.assertTrue(self.strikes[0].helper.aluno_esta_bloqueado())

    def test_aprovar_um_de_quatro_strikes_mantem_bloqueio(self):
        _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=20)
        ticket = Ticket.objects.create(
            execucao_rota=execucao,
            aluno=self.aluno,
            status=StatusTicket.AUSENTE,
            ausente_em=timezone.now(),
        )
        Strike.objects.create(ticket=ticket)
        justificativa = Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Estava em atendimento médico emergencial.',
            self.aluno.usuario,
        )
        justificativa.business.analisar(True, self.admin)
        self.assertTrue(self.strikes[1].helper.aluno_esta_bloqueado())

    def test_outro_aluno_nao_justifica_strike(self):
        outro = criar_aluno('30000000003')
        with self.assertRaises(AuthorizationException):
            Justificativa().business.criar_justificativa(
                self.strikes[0].pk,
                'Tentativa de justificar strike de outra pessoa.',
                outro.usuario,
            )

    def test_justifica_com_apenas_um_strike_ativo(self):
        self.strikes[1].status = StatusStrike.JUSTIFICADO
        self.strikes[1].save(update_fields=['status'])
        self.strikes[2].status = StatusStrike.JUSTIFICADO
        self.strikes[2].save(update_fields=['status'])

        justificativa = Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Justificativa enviada antes de qualquer bloqueio.',
            self.aluno.usuario,
        )

        self.assertEqual(justificativa.status, StatusJustificativa.PENDENTE)
        self.assertEqual(justificativa.strike_id, self.strikes[0].pk)

    def test_nao_justifica_strike_que_deixou_de_ser_ativo(self):
        self.strikes[0].status = StatusStrike.JUSTIFICADO
        self.strikes[0].save(update_fields=['status'])

        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.strikes[0].pk,
                'Tentativa de justificar um strike já justificado.',
                self.aluno.usuario,
            )

    def test_nao_envia_duas_justificativas_para_o_mesmo_strike(self):
        Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Primeira justificativa enviada para análise.',
            self.aluno.usuario,
        )

        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.strikes[0].pk,
                'Segunda justificativa para o mesmo strike.',
                self.aluno.usuario,
            )

    def test_business_rejeita_texto_muito_curto(self):
        with self.assertRaises(BusinessRuleException):
            Justificativa().business.criar_justificativa(
                self.strikes[0].pk,
                'curto',
                self.aluno.usuario,
            )

    def test_fluxo_api(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.post(
            reverse('transporte:justificativa-criar', kwargs={'pk': self.strikes[0].pk}),
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
            self.strikes[0].pk,
            'Estava em atendimento médico emergencial.',
            self.aluno.usuario,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.get(
            reverse('transporte:justificativa-detalhe', kwargs={'pk': justificativa.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], justificativa.pk)

    def test_listagens_usam_quantidade_de_strikes_anotada(self):
        for strike in self.strikes:
            Justificativa().business.criar_justificativa(
                strike.pk,
                'Justificativa para validar a listagem otimizada.',
                self.aluno.usuario,
            )

        strikes = list(Strike().business.listar_para_usuario(self.aluno.usuario))
        justificativas = list(
            Justificativa().business.listar_para_usuario(self.aluno.usuario),
        )
        self.assertTrue(all(hasattr(strike, 'quantidade_strikes_ativos') for strike in strikes))
        self.assertTrue(
            all(hasattr(justificativa, 'quantidade_strikes_ativos') for justificativa in justificativas),
        )

        with patch(
            'Transporte.strikes.helpers.StrikeHelpers.aluno_esta_bloqueado',
        ) as contar_ativos:
            StrikeSerializer(strikes, many=True).data
            JustificativaSerializer(justificativas, many=True).data

        contar_ativos.assert_not_called()

    def test_outro_aluno_nao_detalha_e_l3_detalha(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.strikes[0].pk,
            'Estava em atendimento médico emergencial.',
            self.aluno.usuario,
        )
        outro = criar_aluno('30000000004')
        url = reverse('transporte:justificativa-detalhe', kwargs={'pk': justificativa.pk})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro.usuario)}')
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
