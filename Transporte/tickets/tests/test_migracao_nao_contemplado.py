import importlib

from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao
from Transporte.tickets.choices import STATUS_NAO_CONTEMPLADO_LEGADO, StatusTicket
from Transporte.tickets.models import Ticket

migracao = importlib.import_module(
    'Transporte.tickets.migrations.0002_contemplado_e_espera_legado',
)


class MigracaoNaoContempladoTestCase(TestCase):

    def test_legado_sem_embarque_vira_espera_nao_contemplado(self):
        _, execucao = criar_rota_e_execucao(vagas=2)
        aluno = criar_aluno('21000000090')
        ticket = Ticket.objects.create(
            execucao_rota=execucao,
            aluno=aluno,
            status=STATUS_NAO_CONTEMPLADO_LEGADO,
            entrou_em_espera_em=timezone.now(),
        )

        migracao.migrar_nao_contemplado_para_espera(apps, None)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.EM_ESPERA)
        self.assertNotEqual(ticket.status, StatusTicket.CONTEMPLADO)
