from datetime import time, timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.percursos.models import Percurso
from Transporte.rotas.models import Rota
from Transporte.tests_utils import DIAS_POR_WEEKDAY, criar_aluno, criar_usuario, obter_token


class ExecucaoRotaTestCase(APITestCase):

    def setUp(self):
        self.data = timezone.localdate() + timedelta(days=7)
        self.percurso = Percurso.objects.create(apelido='Campus Centro', descricao='Teste')
        self.rota = Rota.objects.create(
            percurso=self.percurso,
            horario_saida=time(7, 0),
            dia_semana=DIAS_POR_WEEKDAY[self.data.weekday()],
            quantidade_vagas=20,
        )

    def test_cria_snapshot_de_horario_e_vagas(self):
        execucao = ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        self.assertEqual(execucao.quantidade_vagas, 20)
        self.assertEqual(timezone.localtime(execucao.data_hora_saida).time(), time(7, 0))

        self.rota.quantidade_vagas = 30
        self.rota.horario_saida = time(8, 0)
        self.rota.save()
        execucao.refresh_from_db()
        self.assertEqual(execucao.quantidade_vagas, 20)
        self.assertEqual(timezone.localtime(execucao.data_hora_saida).time(), time(7, 0))

    def test_nao_duplica_mesma_rota_na_mesma_data(self):
        ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        with self.assertRaises(BusinessRuleException):
            ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)

    def test_regra_de_unicidade_recebe_resultado_da_consulta(self):
        ExecucaoRota().rules.validar_execucao_unica(False)
        with self.assertRaises(BusinessRuleException):
            ExecucaoRota().rules.validar_execucao_unica(True)

    def test_permite_mesmo_percurso_data_com_horarios_diferentes(self):
        outra_rota = Rota.objects.create(
            percurso=self.percurso,
            horario_saida=time(12, 0),
            dia_semana=self.rota.dia_semana,
            quantidade_vagas=20,
        )
        primeira = ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        segunda = ExecucaoRota().business.criar_execucao(outra_rota.pk, self.data)
        self.assertNotEqual(primeira.rota_id, segunda.rota_id)

    def test_rejeita_data_em_dia_diferente_da_rota(self):
        with self.assertRaises(BusinessRuleException):
            ExecucaoRota().business.criar_execucao(
                self.rota.pk,
                self.data + timedelta(days=1),
            )

    def test_fluxo_de_status(self):
        execucao = ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        execucao.business.alterar_status(StatusExecucaoRota.FECHADA)
        execucao.business.alterar_status(StatusExecucaoRota.EM_EMBARQUE)
        execucao.business.alterar_status(StatusExecucaoRota.FINALIZADA)
        execucao.refresh_from_db()
        self.assertEqual(execucao.status, StatusExecucaoRota.FINALIZADA)
        with self.assertRaises(BusinessRuleException):
            execucao.business.alterar_status(StatusExecucaoRota.ABERTA)

    def test_api_admin_cria_e_aluno_lista_abertas(self):
        admin = criar_usuario('10000000001', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(reverse('transporte:execucao-rota-list'), {
            'rota_id': self.rota.pk,
            'data_execucao': self.data.isoformat(),
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

        aluno = criar_aluno('10000000002')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(aluno.usuario)}')
        execucao = ExecucaoRota.objects.get(rota=self.rota, data_execucao=self.data)
        instante_aberto = timezone.localtime(execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        with patch(
            'Transporte.execucoes_rotas.helpers.now',
            return_value=instante_aberto,
        ):
            resposta = self.client.get(reverse('transporte:execucao-rota-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listagem_disponivel_respeita_abertura_e_limite_exato(self):
        execucao = ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        abertura = timezone.localtime(execucao.data_hora_saida).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        limite = execucao.data_hora_saida - timedelta(minutes=30)

        with patch(
            'Transporte.execucoes_rotas.helpers.now',
            return_value=abertura - timedelta(microseconds=1),
        ):
            self.assertFalse(ExecucaoRota().helper.listar_disponiveis_para_aluno().exists())

        with patch(
            'Transporte.execucoes_rotas.helpers.now',
            return_value=abertura,
        ):
            self.assertTrue(ExecucaoRota().helper.listar_disponiveis_para_aluno().exists())

        with patch(
            'Transporte.execucoes_rotas.helpers.now',
            return_value=limite,
        ):
            self.assertTrue(ExecucaoRota().helper.listar_disponiveis_para_aluno().exists())

        with patch(
            'Transporte.execucoes_rotas.helpers.now',
            return_value=limite + timedelta(microseconds=1),
        ):
            self.assertFalse(ExecucaoRota().helper.listar_disponiveis_para_aluno().exists())

    def test_aluno_nao_cria_execucao(self):
        aluno = criar_aluno('10000000003')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(aluno.usuario)}')
        resposta = self.client.post(reverse('transporte:execucao-rota-list'), {
            'rota_id': self.rota.pk,
            'data_execucao': self.data.isoformat(),
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtro_de_data_invalido_e_ignorado(self):
        ExecucaoRota().business.criar_execucao(self.rota.pk, self.data)
        admin = criar_usuario('10000000004', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.get(
            reverse('transporte:execucao-rota-list'),
            {'data': 'data-invalida'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
