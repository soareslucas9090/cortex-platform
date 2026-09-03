from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Academico.aluno_cursos.models import AlunoCurso
from Academico.cursos.models import Curso
from Identidade.matriculas.models import Matricula
from Transporte.strikes.models import Strike
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_usuario, obter_token
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class RelatorioAlunosApiTestCase(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('10000000001', nome='Admin', admin=True)
        self.aluno_presente = criar_aluno('20000000001', nome='Aluno Presente')
        self.aluno_ausente = criar_aluno('20000000002', nome='Aluno Ausente')
        self.aluno_sem_ticket = criar_aluno('20000000003', nome='Aluno Sem Ticket')

        self.hoje = timezone.localdate()
        self.data_inicio = (self.hoje - timedelta(days=7)).isoformat()
        self.data_fim = self.hoje.isoformat()

        self.rota, self.execucao = criar_rota_e_execucao(vagas=5, dias_ate_execucao=0)
        self.execucao.data_execucao = self.hoje
        self.execucao.save(update_fields=['data_execucao'])

        instante_aberto = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=1, minute=0, second=0, microsecond=0,
        )
        self.patcher = patch('Transporte.tickets.rules.now', return_value=instante_aberto)
        self.patcher.start()

        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_presente,
            status=StatusTicket.EMBARCADO,
            embarcado_em=timezone.now(),
        )
        ticket_ausente = Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_ausente,
            status=StatusTicket.AUSENTE,
            ausente_em=timezone.now(),
        )
        Strike.objects.create(ticket=ticket_ausente)

        curso = Curso.objects.create(nome='TADS Mód. V', codigo_curso='TADS')
        AlunoCurso.objects.create(aluno=self.aluno_presente, curso=curso)
        Matricula.objects.create(usuario=self.aluno_presente.usuario, matricula='2023114TADS')

    def tearDown(self):
        self.patcher.stop()

    def _url_dashboard(self):
        return reverse('transporte:relatorio-alunos-dashboard')

    def _url_detalhes(self):
        return reverse('transporte:relatorio-alunos-detalhes')

    def test_l3_obtem_dashboard_com_resumo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        dados = resposta.data['dados']
        self.assertEqual(dados['resumo']['presentes'], 1)
        self.assertEqual(dados['resumo']['ausentes'], 1)
        self.assertGreaterEqual(dados['resumo']['sem_ticket'], 1)
        self.assertTrue(len(dados['por_horario']) >= 1)

    def test_l1_recebe_403_no_dashboard(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno_presente.usuario)}',
        )
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_intervalo_invalido_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_fim,
            'data_fim': self.data_inicio,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhes_presentes_com_busca(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'presentes',
            'busca': 'Presente',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['categoria'], 'presentes')
        self.assertEqual(resposta.data['count'], 1)
        aluno = resposta.data['dados'][0]
        self.assertEqual(aluno['nome'], 'Aluno Presente')
        self.assertEqual(aluno['turma'], 'TADS Mód. V')
        self.assertEqual(aluno['matricula'], '2023114TADS')

    def test_detalhes_sem_ticket(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'sem_ticket',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        nomes = [item['nome'] for item in resposta.data['dados']]
        self.assertIn('Aluno Sem Ticket', nomes)

    def test_detalhes_categoria_invalida_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'invalida',
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhes_paginacao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'sem_ticket',
            'paginacao': 1,
            'page': 1,
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
