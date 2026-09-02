from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.strikes.models import Strike
from Transporte.tests_utils import (
    criar_aluno,
    criar_conferente,
    criar_execucao_hoje,
    criar_rota_e_execucao,
    criar_usuario,
    obter_token,
)
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class ConferenciaTransporteTestCase(APITestCase):

    def setUp(self):
        self.conferente = criar_conferente()
        _, self.execucao = criar_execucao_hoje(vagas=1)
        self.aluno_reserva = criar_aluno('21000000001', nome='Reservado')
        self.aluno_espera = criar_aluno('21000000002', nome='Espera')
        self.aluno_extra = criar_aluno('21000000003', nome='Extra')
        instante_reserva = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        )
        patcher = patch('Transporte.tickets.rules.now', return_value=instante_reserva)
        patcher.start()
        self.addCleanup(patcher.stop)
        Ticket().business.solicitar_reserva(self.execucao.pk, self.aluno_reserva.usuario)
        Ticket().business.entrar_fila(self.execucao.pk, self.aluno_espera.usuario)
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_extra,
            status=StatusTicket.EM_ESPERA,
            entrou_em_espera_em=timezone.now(),
        )
        self.execucao.quantidade_vagas = 2
        self.execucao.save(update_fields=['quantidade_vagas'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.conferente)}')

    def _entrar_na_janela_monitoramento(self):
        return patch(
            'Transporte.execucoes_rotas.rules.now',
            return_value=self.execucao.data_hora_saida - timedelta(minutes=30),
        )

    def test_payload_conferente_tipico(self):
        transporte = self.conferente.permissoes['transporte']
        self.assertFalse(transporte['gerenciar'])
        self.assertFalse(transporte['reservar'])
        self.assertTrue(transporte['conferir'])

    def test_aluno_recebe_403_na_lista_do_dia(self):
        aluno = criar_aluno('21000000009')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(aluno.usuario)}')
        resposta = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l2_sem_funcao_recebe_403(self):
        servidor = criar_usuario('21000000010')
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.servidores.models import Servidor

        cargo = Cargo.objects.create(nome='Sem conferir')
        Servidor.objects.create(usuario=servidor, cargo=cargo, categoria=1, ativo=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(servidor)}')
        resposta = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_lista_somente_execucoes_do_dia(self):
        criar_rota_e_execucao(vagas=1, dias_ate_execucao=7)
        resposta = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertEqual(ids, [self.execucao.pk])

    def test_data_diferente_de_hoje_retorna_vazio(self):
        amanha = (timezone.localdate() + timedelta(days=1)).isoformat()
        resposta = self.client.get(
            reverse('transporte:conferencia-execucao-list'),
            {'data': amanha},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])

    def test_nao_inicia_antes_do_t30(self):
        with patch(
            'Transporte.execucoes_rotas.rules.now',
            return_value=self.execucao.data_hora_saida - timedelta(minutes=31),
        ):
            resposta = self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inicia_embarque_na_janela_e_lista_filas(self):
        with self._entrar_na_janela_monitoramento():
            resposta = self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['status'], StatusExecucaoRota.EM_EMBARQUE)

        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(reservas.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(reservas.data['dados']), 1)

        chamada = self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': []},
            format='json',
        )
        self.assertEqual(chamada.status_code, status.HTTP_200_OK)
        fila = self.client.get(reverse('transporte:conferencia-fila', kwargs={'pk': self.execucao.pk}))
        self.assertEqual(fila.status_code, status.HTTP_200_OK)

    def test_lote_ausente_gera_strike_e_demais_embarcam(self):
        segundo = criar_aluno('21000000011', nome='Segundo reservado')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=segundo,
            status=StatusTicket.RESERVADO,
            reservado_em=timezone.now(),
        )
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        ticket = Ticket.objects.get(
            aluno=self.aluno_reserva,
            execucao_rota=self.execucao,
        )
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': [str(ticket.codigo)]},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        outro = Ticket.objects.get(aluno=segundo, execucao_rota=self.execucao)
        outro.refresh_from_db()
        self.assertEqual(outro.status, StatusTicket.EMBARCADO)

        segunda = self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': [str(ticket.codigo)]},
            format='json',
        )
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)

    def test_remover_espera_nao_gera_strike(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': []},
            format='json',
        )
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        resposta = self.client.post(
            reverse(
                'transporte:conferencia-fila-remover',
                kwargs={'pk': self.execucao.pk, 'codigo': espera.codigo},
            ),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        espera.refresh_from_db()
        self.assertEqual(espera.status, StatusTicket.CANCELADO)
        self.assertFalse(Strike.objects.filter(ticket=espera).exists())

    def test_entrada_sem_ticket_exige_fila_vazia(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': []},
            format='json',
        )
        outro = criar_aluno('21000000004')
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

        for aluno in (self.aluno_espera, self.aluno_extra):
            ticket_espera = Ticket.objects.get(aluno=aluno, execucao_rota=self.execucao)
            self.client.post(
                reverse(
                    'transporte:conferencia-fila-remover',
                    kwargs={'pk': self.execucao.pk, 'codigo': ticket_espera.codigo},
                ),
            )
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_cpf_inexistente_retorna_404(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': []},
            format='json',
        )
        for aluno in (self.aluno_espera, self.aluno_extra):
            ticket_espera = Ticket.objects.get(aluno=aluno, execucao_rota=self.execucao)
            self.client.post(
                reverse(
                    'transporte:conferencia-fila-remover',
                    kwargs={'pk': self.execucao.pk, 'codigo': ticket_espera.codigo},
                ),
            )
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': '00000000000'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_finalizar_promove_espera_e_cancela_excedentes(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:execucao-rota-iniciar-embarque', kwargs={'pk': self.execucao.pk}),
            )
        ticket_ausente = Ticket.objects.get(
            aluno=self.aluno_reserva,
            execucao_rota=self.execucao,
        )
        self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': [str(ticket_ausente.codigo)]},
            format='json',
        )
        resposta = self.client.post(
            reverse('transporte:execucao-rota-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.FINALIZADA)
        espera_promovida = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        self.assertEqual(espera_promovida.status, StatusTicket.EMBARCADO)
        espera_cancelada = Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao)
        self.assertEqual(espera_cancelada.status, StatusTicket.CANCELADO)
        self.assertFalse(Strike.objects.filter(ticket=espera_cancelada).exists())

    def test_terceirizado_com_funcao_confere(self):
        conferente = criar_conferente(cpf='30000000002', terceirizado=True)
        self.assertTrue(conferente.permissoes['transporte']['conferir'])

    def test_l3_possui_conferir_e_gerenciar(self):
        admin = criar_usuario('21000000099', admin=True)
        transporte = admin.permissoes['transporte']
        self.assertTrue(transporte['gerenciar'])
        self.assertTrue(transporte['conferir'])
