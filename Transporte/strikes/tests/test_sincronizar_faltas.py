from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from Transporte.justificativas.models import Justificativa
from Transporte.strikes.models import Strike
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_usuario
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class SincronizarFaltasTransporteTestCase(APITestCase):

    def setUp(self):
        self.aluno = criar_aluno('30000000001', nome='Aluno Bloqueios')
        self.admin = criar_usuario('30000000002', nome='Admin', admin=True)

    def _criar_strike_ativo(self, indice=0):
        _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=7 + indice)
        execucao.data_execucao = timezone.localdate() + timedelta(days=7 + indice)
        execucao.save(update_fields=['data_execucao'])
        ticket = Ticket.objects.create(
            execucao_rota=execucao,
            aluno=self.aluno,
            status=StatusTicket.AUSENTE,
            ausente_em=timezone.now(),
        )
        Strike().business.criar_para_ticket(ticket)
        return ticket

    def _aprovar_strike(self, ticket):
        justificativa = Justificativa.objects.create(
            strike=ticket.strike,
            texto='Justificativa de teste.',
        )
        justificativa.business.analisar(aprovar=True, usuario=self.admin)

    def test_terceiro_strike_incrementa_quantidade_bloqueios(self):
        for indice in range(3):
            self._criar_strike_ativo(indice)

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 3)
        self.assertTrue(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_quarto_strike_no_mesmo_ciclo_nao_incrementa_historico(self):
        for indice in range(4):
            self._criar_strike_ativo(indice)

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 4)
        self.assertTrue(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_aprovacao_mantem_quantidade_bloqueios_historica(self):
        tickets = [self._criar_strike_ativo(indice) for indice in range(3)]
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

        for ticket in tickets:
            self._aprovar_strike(ticket)

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 0)
        self.assertFalse(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_novo_ciclo_incrementa_quantidade_bloqueios_novamente(self):
        tickets_primeiro_ciclo = [self._criar_strike_ativo(indice) for indice in range(3)]
        for ticket in tickets_primeiro_ciclo:
            self._aprovar_strike(ticket)

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

        for indice in range(3, 6):
            self._criar_strike_ativo(indice)

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 3)
        self.assertTrue(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 2)
