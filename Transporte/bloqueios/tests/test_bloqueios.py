from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_strike, criar_usuario, obter_token
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class BloqueioTestCase(APITestCase):

    def setUp(self):
        self.aluno = criar_aluno('40000000001')
        self.admin = criar_usuario('40000000002', admin=True)
        self.outro = criar_usuario('40000000003')
        for indice in range(3):
            _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=7 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            criar_strike(ticket)
        self.aluno.refresh_from_db()

    def test_l3_lista_bloqueados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(reverse('transporte:bloqueio-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['aluno_pk'], self.aluno.pk)
        self.assertEqual(resposta.data['dados'][0]['faltas'], 3)
        self.assertTrue(resposta.data['dados'][0]['is_bloqueado'])

    def test_aluno_comum_nao_lista_bloqueados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.get(reverse('transporte:bloqueio-list'))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l3_detalha_bloqueio(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(
            reverse('transporte:bloqueio-detalhe', kwargs={'aluno_pk': self.aluno.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']['strikes']), 3)
        self.assertFalse(resposta.data['dados']['tem_justificativa_pendente'])

    def test_bloqueado_envia_justificativa_via_endpoint(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno.usuario)}')
        resposta = self.client.post(
            reverse('transporte:bloqueio-justificativa-criar'),
            {'texto': 'Estava em atendimento médico emergencial.'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Justificativa.objects.filter(
                aluno=self.aluno,
                status=StatusJustificativa.PENDENTE,
            ).count(),
            1,
        )

    def test_detalhe_exibe_justificativa_pendente(self):
        Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Justificativa pendente para análise administrativa.',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(
            reverse('transporte:bloqueio-detalhe', kwargs={'aluno_pk': self.aluno.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['tem_justificativa_pendente'])
        self.assertIsNotNone(resposta.data['dados']['justificativa_pendente'])
