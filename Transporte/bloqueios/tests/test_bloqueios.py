from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Academico.aluno_cursos.models import AlunoCurso
from Academico.cursos.models import Curso
from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_strike, criar_usuario, obter_token
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


def criar_curso(nome='Tecnologia em Análise e Desenvolvimento de Sistemas', codigo='TADS'):
    return Curso.objects.create(nome=nome, codigo_curso=codigo)


class BloqueioTestCase(APITestCase):

    def setUp(self):
        self.aluno = criar_aluno('40000000001', nome='Mateus Rodrigues')
        self.admin = criar_usuario('40000000002', admin=True)
        self.outro = criar_usuario('40000000003')
        self.curso = criar_curso()
        AlunoCurso.objects.create(aluno=self.aluno, curso=self.curso)
        self.strikes_criados = []
        for indice in range(3):
            _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=7 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            self.strikes_criados.append(criar_strike(ticket))
        self.aluno.refresh_from_db()

    def test_l3_lista_bloqueados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(reverse('transporte:bloqueio-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
        item = resposta.data['dados'][0]
        self.assertEqual(item['aluno_pk'], self.aluno.pk)
        self.assertEqual(item['faltas'], 3)
        self.assertEqual(item['ausencias'], 3)
        self.assertEqual(item['bloqueios'], 1)
        self.assertTrue(item['is_bloqueado'])
        self.assertEqual(item['curso_nome'], self.curso.nome)
        self.assertIsNotNone(item['data_bloqueio'])

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
        dados = resposta.data['dados']
        self.assertEqual(dados['ausencias'], 3)
        self.assertEqual(dados['bloqueios'], 1)
        self.assertFalse(dados['tem_justificativa_pendente'])

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

    def test_lista_filtra_por_busca_nome(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(reverse('transporte:bloqueio-list'), {'busca': 'Mateus'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

        resposta = self.client.get(reverse('transporte:bloqueio-list'), {'busca': 'Inexistente'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 0)

    def test_lista_filtra_por_curso_id(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(
            reverse('transporte:bloqueio-list'),
            {'curso_id': self.curso.pk},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

        outro_curso = criar_curso('Outro Curso', 'OUTRO')
        resposta = self.client.get(
            reverse('transporte:bloqueio-list'),
            {'curso_id': outro_curso.pk},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 0)

    def test_lista_filtra_por_tem_justificativa(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')

        resposta_sem = self.client.get(
            reverse('transporte:bloqueio-list'),
            {'tem_justificativa': 'false'},
        )
        self.assertEqual(resposta_sem.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta_sem.data['dados']), 1)

        Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Justificativa pendente para filtro.',
        )

        resposta_com = self.client.get(
            reverse('transporte:bloqueio-list'),
            {'tem_justificativa': 'true'},
        )
        self.assertEqual(resposta_com.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta_com.data['dados']), 1)

        resposta_sem_apos = self.client.get(
            reverse('transporte:bloqueio-list'),
            {'tem_justificativa': 'false'},
        )
        self.assertEqual(resposta_sem_apos.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta_sem_apos.data['dados']), 0)

    def test_quantidade_bloqueios_incrementa_no_primeiro_bloqueio(self):
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_quantidade_bloqueios_nao_incrementa_na_quarta_falta(self):
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)
        _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=30)
        ticket = Ticket.objects.create(
            execucao_rota=execucao,
            aluno=self.aluno,
            status=StatusTicket.AUSENTE,
            ausente_em=timezone.now(),
        )
        criar_strike(ticket)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.faltas, 4)
        self.assertTrue(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_quantidade_bloqueios_mantem_apos_aprovacao(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        justificativa.business.analisar(True, self.admin, 'Documento conferido.')
        self.aluno.refresh_from_db()
        self.assertFalse(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 1)

    def test_quantidade_bloqueios_incrementa_no_segundo_ciclo(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        justificativa.business.analisar(True, self.admin, 'Documento conferido.')
        for indice in range(3):
            _, execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=40 + indice)
            ticket = Ticket.objects.create(
                execucao_rota=execucao,
                aluno=self.aluno,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            criar_strike(ticket)
        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.is_bloqueado)
        self.assertEqual(self.aluno.quantidade_bloqueios, 2)

    def test_detalhe_exibe_itens_ausencia_na_justificativa_pendente(self):
        justificativa = Justificativa().business.criar_justificativa(
            self.aluno.usuario,
            'Estava em atendimento médico emergencial.',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(
            reverse('transporte:bloqueio-detalhe', kwargs={'aluno_pk': self.aluno.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        pendente = resposta.data['dados']['justificativa_pendente']
        self.assertEqual(pendente['id'], justificativa.pk)
        self.assertEqual(len(pendente['itens_ausencia']), 3)
        self.assertEqual(pendente['itens_ausencia'][0]['justificativa'], justificativa.texto)
        self.assertIn('horario', pendente['itens_ausencia'][0])
        self.assertIn('data_ausencia', pendente['itens_ausencia'][0])
        self.assertIn('strike_id', pendente['itens_ausencia'][0])
        self.assertEqual(len(pendente['strikes_cobertos']), 3)
