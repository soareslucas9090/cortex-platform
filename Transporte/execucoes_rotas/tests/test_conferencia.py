from datetime import timedelta
from unittest.mock import patch

from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Transporte.entradas_sem_ticket.models import EntradaSemTicket
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.rules import MENSAGEM_MONITORAMENTO_APOS_FINALIZAR
from Transporte.strikes.helpers import sincronizar_faltas_transporte
from Transporte.strikes.models import Strike
from Transporte.tests_utils import (
    criar_aluno,
    criar_aluno_pcd,
    criar_conferente,
    criar_execucao_hoje,
    criar_rota_e_execucao,
    criar_strike,
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
        agora = timezone.now()
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_reserva,
            status=StatusTicket.RESERVADO,
            posicao_reserva=1,
            reservado_em=agora,
        )
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_espera,
            status=StatusTicket.EM_ESPERA,
            entrou_em_espera_em=agora,
        )
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_extra,
            status=StatusTicket.EM_ESPERA,
            entrou_em_espera_em=agora,
        )
        self.execucao.quantidade_vagas = 2
        self.execucao.save(update_fields=['quantidade_vagas'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.conferente)}')

    def _entrar_na_janela_monitoramento(self):
        depois_do_t30 = self.execucao.data_hora_saida - timedelta(minutes=30) + timedelta(seconds=1)
        return patch(
            'Transporte.execucoes_rotas.rules.now',
            return_value=depois_do_t30,
        )

    def _iniciar_monitoramento(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )

    def _embarcar_ticket(self, ticket):
        return self.client.post(
            reverse(
                'transporte:conferencia-ticket-embarcar',
                kwargs={'pk': self.execucao.pk, 'codigo': str(ticket.codigo)},
            ),
            {},
            format='json',
        )

    def _ausentar_ticket(self, ticket):
        return self.client.post(
            reverse(
                'transporte:conferencia-ticket-ausentar',
                kwargs={'pk': self.execucao.pk, 'codigo': str(ticket.codigo)},
            ),
            {},
            format='json',
        )

    def _fechar_primeira_chamada(self):
        return self.client.post(
            reverse(
                'transporte:conferencia-fechar-primeira-chamada',
                kwargs={'pk': self.execucao.pk},
            ),
            {},
            format='json',
        )

    def _fechar_segunda_chamada(self):
        return self.client.post(
            reverse(
                'transporte:conferencia-fechar-segunda-chamada',
                kwargs={'pk': self.execucao.pk},
            ),
            {},
            format='json',
        )

    def _iniciar_e_finalizar_chamada(self, ausentes=None):
        ausentes = {str(codigo) for codigo in (ausentes or [])}
        self._iniciar_monitoramento()
        for ticket in Ticket.objects.filter(
            execucao_rota=self.execucao,
            status=StatusTicket.RESERVADO,
        ):
            if str(ticket.codigo) not in ausentes:
                self._embarcar_ticket(ticket)
        self._fechar_primeira_chamada()
        if ausentes:
            for ticket in Ticket.objects.filter(
                execucao_rota=self.execucao,
                status=StatusTicket.RESERVADO,
            ):
                self._ausentar_ticket(ticket)
            self._fechar_segunda_chamada()

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
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inicia_embarque_na_janela_e_lista_filas(self):
        with self._entrar_na_janela_monitoramento():
            resposta = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['status'], StatusExecucaoRota.EM_EMBARQUE)

        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(reservas.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(reservas.data['dados']['tickets']), 1)

        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._embarcar_ticket(ticket)
        chamada = self._fechar_primeira_chamada()
        self.assertEqual(chamada.status_code, status.HTTP_200_OK)
        with self.assertRaises(NoReverseMatch):
            reverse('transporte:conferencia-fila', kwargs={'pk': self.execucao.pk})

    def test_lista_monitoramento_indica_deficiencia(self):
        pcd = criar_aluno_pcd('21000000012', nome='Aluno PcD')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=pcd,
            status=StatusTicket.RESERVADO,
            posicao_reserva=2,
            reservado_em=timezone.now(),
        )
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(reservas.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['aluno']['nome'] for item in reservas.data['dados']['tickets']],
            ['Aluno PcD', 'Reservado'],
        )
        self.assertEqual(
            {item['aluno']['nome']: item['posicao']['atual'] for item in reservas.data['dados']['tickets']},
            {'Aluno PcD': 2, 'Reservado': 1},
        )
        por_nome = {item['aluno']['nome']: item['aluno'] for item in reservas.data['dados']['tickets']}
        self.assertTrue(por_nome['Aluno PcD']['tem_deficiencia'])
        self.assertFalse(por_nome['Reservado']['tem_deficiencia'])

    def test_ausente_gera_strike_ao_finalizar_e_demais_embarcam(self):
        segundo = criar_aluno('21000000011', nome='Segundo reservado')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=segundo,
            status=StatusTicket.RESERVADO,
            posicao_reserva=2,
            reservado_em=timezone.now(),
        )
        self._iniciar_monitoramento()
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        outro = Ticket.objects.get(aluno=segundo, execucao_rota=self.execucao)
        self._embarcar_ticket(outro)
        self._fechar_primeira_chamada()
        self._ausentar_ticket(ticket)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertFalse(Strike.objects.filter(ticket=ticket).exists())
        self._fechar_segunda_chamada()
        self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
            {},
            format='json',
        )
        ticket.refresh_from_db()
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        replay = self._fechar_segunda_chamada()
        self.assertEqual(replay.status_code, status.HTTP_200_OK)

    def test_dois_conferentes_ultima_marcacao_ganha(self):
        outro_conferente = criar_conferente(cpf='30000000088', nome='Segundo conferente')
        self._iniciar_monitoramento()
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._embarcar_ticket(ticket)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro_conferente)}')
        self.client.post(
            reverse(
                'transporte:conferencia-ticket-desfazer-presenca',
                kwargs={'pk': self.execucao.pk, 'codigo': str(ticket.codigo)},
            ),
            {},
            format='json',
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.RESERVADO)

    def test_fechar_primeira_pula_segunda_sem_reservados(self):
        self._iniciar_monitoramento()
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._embarcar_ticket(ticket)
        resposta = self._fechar_primeira_chamada()
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['segunda_chamada_pulada'])
        self.execucao.refresh_from_db()
        self.assertTrue(self.execucao.segunda_chamada_pulada)
        self.assertTrue(self.execucao.chamada_tickets_concluida)
        self.assertEqual(resposta.data['dados']['execucao']['fase_conferencia'], 'cpf')

    def test_fechar_segunda_com_reservado_retorna_400(self):
        segundo = criar_aluno('21000000013', nome='Ainda reservado')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=segundo,
            status=StatusTicket.RESERVADO,
            posicao_reserva=2,
            reservado_em=timezone.now(),
        )
        self._iniciar_monitoramento()
        self._fechar_primeira_chamada()
        resposta = self._fechar_segunda_chamada()
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restantes_faltaram_marca_somente_reservados(self):
        segundo = criar_aluno('21000000014', nome='Embarcado segunda')
        pendente = criar_aluno('21000000015', nome='Pendente segunda')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=segundo,
            status=StatusTicket.RESERVADO,
            posicao_reserva=2,
            reservado_em=timezone.now(),
        )
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=pendente,
            status=StatusTicket.RESERVADO,
            posicao_reserva=3,
            reservado_em=timezone.now(),
        )
        self._iniciar_monitoramento()
        self._embarcar_ticket(Ticket.objects.get(aluno=segundo, execucao_rota=self.execucao))
        self._fechar_primeira_chamada()
        resposta = self.client.post(
            reverse(
                'transporte:conferencia-restantes-faltaram',
                kwargs={'pk': self.execucao.pk},
            ),
            {},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Ticket.objects.get(aluno=segundo, execucao_rota=self.execucao).status,
            StatusTicket.EMBARCADO,
        )
        ticket_pendente = Ticket.objects.get(aluno=pendente, execucao_rota=self.execucao)
        self.assertEqual(ticket_pendente.status, StatusTicket.AUSENTE)
        self.assertFalse(Strike.objects.filter(ticket=ticket_pendente).exists())

    def test_rotas_da_fila_da_conferencia_foram_removidas(self):
        with self.assertRaises(NoReverseMatch):
            reverse('transporte:conferencia-fila', kwargs={'pk': self.execucao.pk})
        with self.assertRaises(NoReverseMatch):
            reverse(
                'transporte:conferencia-fila-remover',
                kwargs={'pk': self.execucao.pk, 'codigo': '00000000-0000-0000-0000-000000000000'},
            )

    def test_entrada_por_cpf_usa_vaga_mesmo_com_espera(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000004')
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(resposta.data['dados']['entrada'])
        self.assertTrue(
            EntradaSemTicket.objects.filter(
                aluno=outro,
                execucao_rota=self.execucao,
            ).exists()
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_varios_cpfs_um_a_um(self):
        self._iniciar_e_finalizar_chamada()
        primeiro = criar_aluno('21000000050')
        segunda_pessoa = criar_aluno('21000000051')
        url = reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk})
        self.assertEqual(
            self.client.post(url, {'cpf': primeiro.usuario.cpf}, format='json').status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.client.post(url, {'cpf': segunda_pessoa.usuario.cpf}, format='json').status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(EntradaSemTicket.objects.filter(execucao_rota=self.execucao).count(), 2)

    def test_cpf_repetido_retorna_replay(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000054')
        url = reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk})
        primeira = self.client.post(url, {'cpf': outro.usuario.cpf}, format='json')
        segunda = self.client.post(url, {'cpf': outro.usuario.cpf}, format='json')
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)

    def test_ausente_entra_por_cpf_embarca_sem_entrada_sem_ticket(self):
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._iniciar_e_finalizar_chamada(ausentes=[str(ticket.codigo)])
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': self.aluno_reserva.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.EMBARCADO)
        self.assertFalse(Strike.objects.filter(ticket=ticket).exists())
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_reserva,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_ausente_com_tres_strikes_entra_por_cpf(self):
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._iniciar_e_finalizar_chamada(ausentes=[str(ticket.codigo)])
        for indice in range(3):
            _, outra_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=8 + indice)
            outro_ticket = Ticket.objects.create(
                execucao_rota=outra_execucao,
                aluno=self.aluno_reserva,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            Strike.objects.create(ticket=outro_ticket)
        sincronizar_faltas_transporte(self.aluno_reserva)
        self.aluno_reserva.refresh_from_db()
        self.assertTrue(self.aluno_reserva.is_bloqueado)
        validar = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': self.aluno_reserva.usuario.cpf},
            format='json',
        )
        self.assertEqual(validar.status_code, status.HTTP_200_OK)
        self.assertTrue(validar.data['dados']['elegivel'])
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': self.aluno_reserva.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.EMBARCADO)
        self.assertFalse(Strike.objects.filter(ticket=ticket).exists())
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_reserva,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_bloqueado_sem_ticket_nesta_execucao_entra_por_cpf(self):
        walk_in = criar_aluno('21000000082', nome='Bloqueado walk-in')
        for indice in range(3):
            _, outra_execucao = criar_rota_e_execucao(vagas=1, dias_ate_execucao=30 + indice)
            outro_ticket = Ticket.objects.create(
                execucao_rota=outra_execucao,
                aluno=walk_in,
                status=StatusTicket.AUSENTE,
                ausente_em=timezone.now(),
            )
            criar_strike(outro_ticket)
        walk_in.refresh_from_db()
        self.assertTrue(walk_in.is_bloqueado)
        self.assertFalse(
            Ticket.objects.filter(aluno=walk_in, execucao_rota=self.execucao).exists()
        )
        self._iniciar_e_finalizar_chamada()
        validar = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': walk_in.usuario.cpf},
            format='json',
        )
        self.assertEqual(validar.status_code, status.HTTP_200_OK)
        self.assertTrue(validar.data['dados']['elegivel'])
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': walk_in.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EntradaSemTicket.objects.filter(
                aluno=walk_in,
                execucao_rota=self.execucao,
            ).exists()
        )
        self.assertFalse(
            Ticket.objects.filter(aluno=walk_in, execucao_rota=self.execucao).exists()
        )

    def test_cpf_inexistente_retorna_404(self):
        self._iniciar_e_finalizar_chamada()
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': '00000000000'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_finalizar_mantem_espera_como_desfecho_sem_lote(self):
        self._iniciar_e_finalizar_chamada()
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EMBARCADO)
        self.assertIsNotNone(self.execucao.embarcado_em)
        self.assertEqual(self.execucao.conferencia_finalizada_por_id, self.conferente.pk)
        self.assertIsNone(self.execucao.finalizada_em)
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        extra = Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao)
        self.assertEqual(espera.status, StatusTicket.EM_ESPERA)
        self.assertEqual(extra.status, StatusTicket.EM_ESPERA)
        self.assertNotEqual(espera.status, StatusTicket.CONTEMPLADO)
        self.assertFalse(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).exists()
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao).status,
            StatusTicket.EMBARCADO,
        )
        self.assertTrue(self.execucao.entradas_cpf_concluidas)

    def test_finalizar_nao_contempla_quem_embarcou_por_cpf(self):
        self._iniciar_e_finalizar_chamada()
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        self.assertEqual(
            self.client.post(
                reverse(
                    'transporte:conferencia-entrada-sem-ticket',
                    kwargs={'pk': self.execucao.pk},
                ),
                {'cpf': espera.aluno.usuario.cpf},
                format='json',
            ).status_code,
            status.HTTP_201_CREATED,
        )
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        espera.refresh_from_db()
        self.assertEqual(espera.status, StatusTicket.CONTEMPLADO)
        self.assertTrue(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_espera,
                execucao_rota=self.execucao,
            ).exists()
        )
        self.assertIsNone(espera.embarcado_em)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_extra,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_finalizar_mantem_ausente_e_espera(self):
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._iniciar_e_finalizar_chamada(ausentes=[str(ticket.codigo)])
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_cancelado_entra_por_cpf_sem_virar_contemplado(self):
        self.execucao.quantidade_vagas = 3
        self.execucao.save(update_fields=['quantidade_vagas'])
        aluno_cancelou = criar_aluno('21000000081')
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=aluno_cancelou,
            status=StatusTicket.CANCELADO,
            cancelado_em=timezone.now(),
        )
        self._iniciar_e_finalizar_chamada()
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': aluno_cancelou.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        ticket = Ticket.objects.get(aluno=aluno_cancelou, execucao_rota=self.execucao)
        self.assertEqual(ticket.status, StatusTicket.CANCELADO)
        self.assertNotEqual(ticket.status, StatusTicket.CONTEMPLADO)
        self.assertEqual(
            EntradaSemTicket.objects.filter(
                aluno=aluno_cancelou,
                execucao_rota=self.execucao,
            ).count(),
            1,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_terceirizado_com_funcao_confere(self):
        conferente = criar_conferente(cpf='30000000002', terceirizado=True)
        self.assertTrue(conferente.permissoes['transporte']['conferir'])

    def test_l3_possui_conferir_e_gerenciar(self):
        admin = criar_usuario('21000000099', admin=True)
        transporte = admin.permissoes['transporte']
        self.assertTrue(transporte['gerenciar'])
        self.assertTrue(transporte['conferir'])

    def test_nao_inicia_no_instante_exato_do_t30(self):
        with patch(
            'Transporte.execucoes_rotas.rules.now',
            return_value=self.execucao.data_hora_saida - timedelta(minutes=30),
        ):
            resposta = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inicia_depois_do_horario_de_saida_no_mesmo_dia(self):
        with patch(
            'Transporte.execucoes_rotas.rules.now',
            return_value=self.execucao.data_hora_saida + timedelta(minutes=5),
        ):
            resposta = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_l3_nao_opera_execucao_de_outro_dia(self):
        admin = criar_usuario('21000000098', admin=True)
        _, futura = criar_rota_e_execucao(vagas=1, dias_ate_execucao=7)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(
            reverse('transporte:conferencia-iniciar', kwargs={'pk': futura.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancelada_do_dia_retorna_404_na_conferencia(self):
        _, cancelada = criar_execucao_hoje(vagas=1)
        cancelada.status = StatusExecucaoRota.CANCELADA
        cancelada.save(update_fields=['status'])
        iniciar = self.client.post(
            reverse('transporte:conferencia-iniciar', kwargs={'pk': cancelada.pk}),
        )
        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': cancelada.pk}),
        )
        self.assertEqual(iniciar.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(reservas.status_code, status.HTTP_404_NOT_FOUND)

    def test_replay_finalizar_execucao_ja_finalizada(self):
        self._iniciar_e_finalizar_chamada()
        primeira = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        segunda = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EMBARCADO)
        self.assertIsNotNone(self.execucao.embarcado_em)
        self.assertEqual(self.execucao.conferencia_finalizada_por_id, self.conferente.pk)
        self.assertIsNone(self.execucao.finalizada_em)
        self.assertEqual(
            primeira.data['dados']['embarcado_em'],
            segunda.data['dados']['embarcado_em'],
        )
        outro = criar_conferente(cpf='30000000099', nome='Outro conferente')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro)}')
        replay_outro = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(replay_outro.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.conferencia_finalizada_por_id, self.conferente.pk)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_replay_nao_preenche_responsavel_legado(self):
        self._iniciar_e_finalizar_chamada()
        agora = timezone.now()
        self.execucao.status = StatusExecucaoRota.EMBARCADO
        self.execucao.embarcado_em = agora
        self.execucao.save(update_fields=['status', 'embarcado_em'])
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertIsNone(self.execucao.conferencia_finalizada_por_id)

    def _finalizar_conferencia_na_janela(self):
        self._iniciar_e_finalizar_chamada()
        finalizar = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(finalizar.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EMBARCADO)
        self.assertIsNotNone(self.execucao.embarcado_em)
        self.assertEqual(self.execucao.conferencia_finalizada_por_id, self.conferente.pk)
        self.assertIsNone(self.execucao.finalizada_em)

    def test_nao_inicia_apos_finalizar_conferencia(self):
        self._finalizar_conferencia_na_janela()
        with self._entrar_na_janela_monitoramento():
            resposta = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(MENSAGEM_MONITORAMENTO_APOS_FINALIZAR, str(resposta.data))

    def test_l3_nao_inicia_apos_finalizar_conferencia(self):
        self._finalizar_conferencia_na_janela()
        admin = criar_usuario('21000000096', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        with self._entrar_na_janela_monitoramento():
            resposta = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(MENSAGEM_MONITORAMENTO_APOS_FINALIZAR, str(resposta.data))

    def test_pode_monitorar_falso_quando_finalizada(self):
        self._finalizar_conferencia_na_janela()
        admin = criar_usuario('21000000095', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.get(
            reverse('transporte:execucao-rota-detalhe', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(resposta.data['dados']['pode_monitorar'])

    def test_lista_pode_monitorar_true_apos_t30(self):
        with self._entrar_na_janela_monitoramento():
            resposta = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        item = next(dado for dado in resposta.data['dados'] if dado['id'] == self.execucao.pk)
        self.assertTrue(item['pode_monitorar'])

    def test_lista_mostra_finalizada_e_oculta_cancelada_para_conferente(self):
        self._assert_lista_conferencia_mostra_finalizada_oculta_cancelada()

    def test_lista_mostra_finalizada_e_oculta_cancelada_para_l3(self):
        admin = criar_usuario('21000000097', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        self._assert_lista_conferencia_mostra_finalizada_oculta_cancelada()

    def _assert_lista_conferencia_mostra_finalizada_oculta_cancelada(self):
        _, fechada = criar_execucao_hoje(vagas=1)
        fechada.status = StatusExecucaoRota.FECHADA
        fechada.save(update_fields=['status'])
        _, em_embarque = criar_execucao_hoje(vagas=1)
        em_embarque.status = StatusExecucaoRota.EM_EMBARQUE
        em_embarque.save(update_fields=['status'])
        _, embarcada = criar_execucao_hoje(vagas=1)
        embarcada.status = StatusExecucaoRota.EMBARCADO
        embarcada.save(update_fields=['status'])
        _, iniciada = criar_execucao_hoje(vagas=1)
        iniciada.status = StatusExecucaoRota.INICIADA
        iniciada.save(update_fields=['status'])
        _, finalizada = criar_execucao_hoje(vagas=1)
        finalizada.status = StatusExecucaoRota.FINALIZADA
        finalizada.save(update_fields=['status'])
        _, cancelada = criar_execucao_hoje(vagas=1)
        cancelada.status = StatusExecucaoRota.CANCELADA
        cancelada.save(update_fields=['status'])
        resposta = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        por_id = {item['id']: item for item in resposta.data['dados']}
        self.assertIn(self.execucao.pk, por_id)
        self.assertIn(fechada.pk, por_id)
        self.assertIn(em_embarque.pk, por_id)
        self.assertIn(embarcada.pk, por_id)
        self.assertIn(iniciada.pk, por_id)
        self.assertIn(finalizada.pk, por_id)
        self.assertNotIn(cancelada.pk, por_id)
        self.assertFalse(por_id[embarcada.pk]['pode_monitorar'])
        self.assertFalse(por_id[iniciada.pk]['pode_monitorar'])
        self.assertFalse(por_id[finalizada.pk]['pode_monitorar'])

    def test_replay_iniciar_embarque_e_idempotente(self):
        with self._entrar_na_janela_monitoramento():
            primeira = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
            segunda = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(
            primeira.data['dados']['monitoramento_iniciado_em'],
            segunda.data['dados']['monitoramento_iniciado_em'],
        )

    def test_fechar_primeira_chamada_replay_idempotente(self):
        self._iniciar_monitoramento()
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._embarcar_ticket(ticket)
        primeira = self._fechar_primeira_chamada()
        segunda = self._fechar_primeira_chamada()
        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)

    def test_cpf_de_espera_contempla_e_cria_entrada(self):
        self._iniciar_e_finalizar_chamada()
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': espera.aluno.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(resposta.data['dados']['entrada'])
        espera.refresh_from_db()
        self.assertEqual(espera.status, StatusTicket.CONTEMPLADO)
        self.assertIsNone(espera.embarcado_em)
        self.assertEqual(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_espera,
                execucao_rota=self.execucao,
            ).count(),
            1,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        replay = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': espera.aluno.usuario.cpf},
            format='json',
        )
        self.assertEqual(replay.status_code, status.HTTP_200_OK)
        self.assertTrue(replay.data['dados']['replay'])
        self.assertEqual(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_espera,
                execucao_rota=self.execucao,
            ).count(),
            1,
        )

    def test_post_validar_cpf_antes_de_gravar(self):
        self._iniciar_e_finalizar_chamada()
        pcd = criar_aluno_pcd('21000000044', nome='Walk-in PcD')
        resposta = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': pcd.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['elegivel'])
        aluno = resposta.data['dados']['aluno']
        self.assertEqual(aluno['nome'], 'Walk-in PcD')
        self.assertTrue(aluno['tem_deficiencia'])
        self.assertFalse(
            EntradaSemTicket.objects.filter(aluno=pcd, execucao_rota=self.execucao).exists()
        )

    def test_validar_cpf_depois_da_conferencia_finalizada_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        url_validar = reverse(
            'transporte:conferencia-entrada-sem-ticket-validar',
            kwargs={'pk': self.execucao.pk},
        )
        self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        walk_in = criar_aluno('21000000069')
        resposta = self.client.post(
            url_validar,
            {'cpf': walk_in.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=walk_in,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_validar_cpf_de_espera_e_reservado(self):
        self._iniciar_e_finalizar_chamada()
        espera = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': self.aluno_espera.usuario.cpf},
            format='json',
        )
        self.assertEqual(espera.status_code, status.HTTP_200_OK)
        reservado = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': self.aluno_reserva.usuario.cpf},
            format='json',
        )
        self.assertEqual(reservado.status_code, status.HTTP_200_OK)

    def test_aluno_nao_matriculado_nao_entra_por_cpf(self):
        from Academico.alunos.choices import SituacaoAluno

        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000045', situacao=SituacaoAluno.FORMADO)
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permissao_direta_por_usuario_confere(self):
        from Transporte.tests_utils import criar_conferente_por_usuario

        conferente = criar_conferente_por_usuario()
        self.assertTrue(conferente.permissoes['transporte']['conferir'])
        self.assertFalse(conferente.permissoes['transporte']['gerenciar'])

    def test_or_funcao_e_usuario(self):
        conferente = criar_conferente(cpf='30000000012')
        from Transporte.permissoes.models import PermissaoUsuarioTransporte
        PermissaoUsuarioTransporte().business.criar_permissao(conferente.pk, conferir=True)
        self.assertTrue(conferente.permissoes['transporte']['conferir'])

    def test_replay_lote_cpf_mesmo_conjunto_retorna_200(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000060')
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        payload = {'cpf': outro.usuario.cpf}
        primeira = self.client.post(url, payload, format='json')
        segunda = self.client.post(url, payload, format='json')
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertTrue(segunda.data['dados']['replay'])
        self.assertEqual(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).count(),
            1,
        )

    def test_replay_lote_cpf_aceita_mesmo_conjunto_formatado(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000070')
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        primeira = self.client.post(url, {'cpf': outro.usuario.cpf}, format='json')
        segunda = self.client.post(
            url,
            {'cpf': '210.000.000-70'},
            format='json',
        )
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).count(),
            1,
        )

    def test_l3_nao_cancela_execucao_em_embarque(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        admin = criar_usuario('30000000099', nome='Admin transporte', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(
            reverse('transporte:execucao-rota-cancelar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EM_EMBARQUE)

    def test_l3_nao_cancela_execucao_embarcada(self):
        self._finalizar_conferencia_na_janela()
        admin = criar_usuario('30000000098', nome='Admin embarcado', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(
            reverse('transporte:execucao-rota-cancelar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EMBARCADO)

    def test_chamada_e_cpf_bloqueados_apos_embarcado(self):
        self._finalizar_conferencia_na_janela()
        chamada = self.client.post(
            reverse('transporte:conferencia-fechar-primeira-chamada', kwargs={'pk': self.execucao.pk}),
            {'ausentes': []},
            format='json',
        )
        cpf = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': criar_aluno('21000000077').usuario.cpf},
            format='json',
        )
        self.assertEqual(chamada.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cpf.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consulta_conferencia_apos_embarcado_no_mesmo_dia(self):
        self._finalizar_conferencia_na_janela()
        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
        )
        lista = self.client.get(reverse('transporte:conferencia-execucao-list'))
        self.assertEqual(reservas.status_code, status.HTTP_200_OK)
        self.assertEqual(lista.status_code, status.HTTP_200_OK)
        item = next(dado for dado in lista.data['dados'] if dado['id'] == self.execucao.pk)
        self.assertEqual(item['status'], StatusExecucaoRota.EMBARCADO)
        self.assertIsNotNone(item['embarcado_em'])
        self.assertIsNone(item['finalizada_em'])

    def test_consulta_reservas_antes_de_iniciar_embarque_retorna_400(self):
        resposta = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nao_finaliza_conferencia_sem_chamada(self):
        with self._entrar_na_janela_monitoramento():
            iniciar = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(iniciar.status_code, status.HTTP_200_OK)
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EM_EMBARQUE)
        self.assertIsNone(self.execucao.embarcado_em)

    def test_pk_inexistente_na_conferencia_retorna_404(self):
        resposta = self.client.post(
            reverse('transporte:conferencia-iniciar', kwargs={'pk': 999999}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_fechar_reservas_em_embarque_retorna_400(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        admin = criar_usuario('30000000097', nome='Admin fechar embarque', admin=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(admin)}')
        resposta = self.client.post(
            reverse('transporte:execucao-rota-fechar-reservas', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EM_EMBARQUE)

    def test_lote_excedente_desfaz_contemplado_e_entradas(self):
        self._iniciar_e_finalizar_chamada()
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        resposta = self.client.post(
            url,
            {
                'cpfs': [
                    self.aluno_espera.usuario.cpf,
                    self.aluno_extra.usuario.cpf,
                ],
            },
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertFalse(EntradaSemTicket.objects.filter(execucao_rota=self.execucao).exists())

    def test_ocupacao_nao_soma_contemplado_duas_vezes(self):
        self.execucao.quantidade_vagas = 3
        self.execucao.save(update_fields=['quantidade_vagas'])
        self._iniciar_e_finalizar_chamada()
        walk_in = criar_aluno('21000000080')
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        self.assertEqual(
            self.client.post(url, {'cpf': self.aluno_espera.usuario.cpf}, format='json').status_code,
            status.HTTP_201_CREATED,
        )
        resposta = self.client.post(url, {'cpf': walk_in.usuario.cpf}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.helper.contar_vagas_ocupadas(), 3)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.CONTEMPLADO,
        )
        self.assertEqual(
            Ticket.objects.filter(
                execucao_rota=self.execucao,
                status=StatusTicket.EMBARCADO,
            ).count(),
            1,
        )

    def test_lote_nao_altera_ticket_de_outra_execucao(self):
        _, outra = criar_execucao_hoje(vagas=2)
        Ticket.objects.create(
            execucao_rota=outra,
            aluno=self.aluno_extra,
            status=StatusTicket.EM_ESPERA,
            entrou_em_espera_em=timezone.now(),
        )
        self._iniciar_e_finalizar_chamada()
        resposta = self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'cpf': self.aluno_espera.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=outra).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
