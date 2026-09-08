from datetime import time, timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.rotas.tests.test_rotas_do_dia import criar_motorista, criar_rota, criar_usuario
from Transporte.tests_utils import criar_conferente


class ViagemMotoristaAPITestCase(APITestCase):
    def setUp(self):
        self.usuario, self.motorista = criar_motorista('72000000001', 'Motorista')
        self.outro, _ = criar_motorista('72000000002', 'Outro motorista')
        self.admin = criar_usuario('72000000003', 'Administrador', is_staff=True)
        self.rota = criar_rota(time(12))
        self.execucao = ExecucaoRota().business.criar_execucao(self.rota.pk, timezone.localdate())
        self.inicio = reverse('transporte:motorista-iniciar-rota', args=[self.execucao.pk])
        self.fim = reverse('transporte:motorista-finalizar-rota', args=[self.execucao.pk])
        self.lista = reverse('transporte:motorista-rotas-do-dia')
        self.client.force_authenticate(self.usuario)

    def liberar(self):
        self.execucao.status = StatusExecucaoRota.FINALIZADA
        self.execucao.chamada_tickets_concluida = True
        self.execucao.finalizada_em = timezone.now()
        self.execucao.save()

    def test_conferencia_libera_viagem_e_duracao_persiste(self):
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 400)
        self.execucao.status = StatusExecucaoRota.EM_EMBARQUE
        self.execucao.save()
        self.client.force_authenticate(criar_conferente())
        chamada = reverse('transporte:conferencia-finalizar-chamada', args=[self.execucao.pk])
        conferencia = reverse('transporte:conferencia-finalizar', args=[self.execucao.pk])
        self.assertEqual(self.client.post(chamada, {'ausentes': []}, format='json').status_code, 200)
        self.assertEqual(self.client.post(conferencia, {}).status_code, 200)
        self.client.force_authenticate(self.usuario)
        self.assertTrue(self.client.get(self.lista).data['dados'][0]['viagem']['pode_iniciar_rota'])
        agora = timezone.now()
        with patch('django.utils.timezone.now', return_value=agora):
            resposta = self.client.post(self.inicio, {'rota_iniciada_em': '2000-01-01T00:00:00Z'})
        self.assertEqual(resposta.status_code, 200)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.rota_iniciada_em, agora)
        self.assertEqual(self.execucao.rota_iniciada_por_id, self.usuario.pk)
        self.assertTrue(resposta.data['dados']['pode_finalizar_rota'])
        with patch('django.utils.timezone.now', return_value=agora + timedelta(minutes=42, seconds=17)):
            resposta = self.client.post(self.fim, {})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['dados']['duracao_rota_segundos'], 2537)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.duracao_rota_segundos, 2537)
        viagem = self.client.get(self.lista).data['dados'][0]['viagem']
        self.assertEqual(viagem['duracao_rota_segundos'], 2537)
        self.assertFalse(viagem['pode_iniciar_rota'])
        self.assertFalse(viagem['pode_finalizar_rota'])
        self.assertEqual(self.execucao.status, StatusExecucaoRota.FINALIZADA)

    def test_reenvios_preservam_horarios_e_nao_reinicia_concluida(self):
        self.liberar()
        inicio = self.client.post(self.inicio, {}).data['dados']['rota_iniciada_em']
        repetida = self.client.post(self.inicio, {})
        self.assertEqual(repetida.status_code, 200)
        self.assertEqual(repetida.data['dados']['rota_iniciada_em'], inicio)
        fim = self.client.post(self.fim, {}).data['dados']
        repetida = self.client.post(self.fim, {})
        self.assertEqual(repetida.status_code, 200)
        self.assertEqual(repetida.data['dados']['rota_finalizada_em'], fim['rota_finalizada_em'])
        self.assertEqual(repetida.data['dados']['duracao_rota_segundos'], fim['duracao_rota_segundos'])
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 400)

    def test_bloqueia_estados_anteriores_e_cancelada(self):
        for estado in (StatusExecucaoRota.ABERTA, StatusExecucaoRota.FECHADA,
                       StatusExecucaoRota.EM_EMBARQUE, StatusExecucaoRota.CANCELADA):
            with self.subTest(estado=estado):
                self.execucao.status = estado
                self.execucao.save()
                self.assertEqual(self.client.post(self.inicio, {}).status_code, 400)
                self.assertFalse(self.client.get(self.lista).data['dados'][0]['viagem']['pode_iniciar_rota'])

    def test_nao_finaliza_sem_inicio(self):
        self.liberar()
        self.assertEqual(self.client.post(self.fim, {}).status_code, 400)

    def test_outro_motorista_nao_sobrescreve_viagem_e_admin_pode_finalizar(self):
        self.liberar()
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 200)
        self.client.force_authenticate(self.outro)
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 403)
        self.assertEqual(self.client.post(self.fim, {}).status_code, 403)
        self.assertFalse(self.client.get(self.lista).data['dados'][0]['viagem']['pode_finalizar_rota'])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(self.fim, {}).status_code, 200)

    def test_permissoes_de_operacao(self):
        self.liberar()
        for usuario in (None, criar_conferente(), criar_usuario('72000000004', 'Comum')):
            self.client.force_authenticate(usuario)
            for url in (self.inicio, self.fim):
                self.assertEqual(self.client.post(url, {}).status_code, 401 if usuario is None else 403)
        self.client.force_authenticate(self.usuario)
        self.motorista.ativo = False
        self.motorista.save()
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 403)

    def test_viagem_atravessa_meia_noite_e_permanece_na_tela(self):
        self.liberar()
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 200)
        self.execucao.refresh_from_db()
        ontem = timezone.localdate() - timedelta(days=1)
        self.execucao.data_execucao = ontem
        self.execucao.rota_iniciada_em = timezone.now() - timedelta(hours=2)
        self.execucao.save()
        # Mesmo se o cadastro for desativado durante a viagem, é possível encerrá-la.
        self.rota.ativo = False
        self.rota.save()
        item = self.client.get(self.lista).data['dados'][0]
        self.assertEqual(item['data'], ontem.isoformat())
        self.assertTrue(item['viagem']['pode_finalizar_rota'])
        self.assertEqual(self.client.post(self.fim, {}).status_code, 200)
        self.execucao.refresh_from_db()
        self.assertGreaterEqual(self.execucao.duracao_rota_segundos, 7200)

    def test_nao_inicia_rota_inativa_ou_de_outro_dia(self):
        self.liberar()
        self.rota.ativo = False
        self.rota.save()
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 400)
        self.rota.ativo = True
        self.rota.save()
        self.execucao.data_execucao -= timedelta(days=1)
        self.execucao.save()
        self.assertEqual(self.client.post(self.inicio, {}).status_code, 400)
