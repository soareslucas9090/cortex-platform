from datetime import timedelta
from unittest.mock import patch

from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Transporte.entradas_sem_ticket.models import EntradaSemTicket
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.rules import (
    MENSAGEM_MONITORAMENTO_APOS_FINALIZAR,
    MENSAGEM_RASCUNHO_CPF_ABERTO,
)
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

    def _classificar_rascunho(self, codigo, classificacao):
        return self.client.post(
            reverse(
                'transporte:conferencia-reserva-rascunho',
                kwargs={'pk': self.execucao.pk, 'codigo': codigo},
            ),
            {'classificacao': classificacao},
            format='json',
        )

    def _versao_chamada(self):
        self.execucao.refresh_from_db()
        return self.execucao.versao_chamada

    def _versao_cpf(self):
        self.execucao.refresh_from_db()
        return self.execucao.versao_cpf

    def _finalizar_chamada(self, versao=None):
        if versao is None:
            versao = self._versao_chamada()
        return self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'versao': versao},
            format='json',
        )

    def _iniciar_e_finalizar_chamada(self, ausentes=None):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        for codigo in ausentes or []:
            self._classificar_rascunho(codigo, 'ausente')
        return self._finalizar_chamada()

    def _adicionar_cpf_rascunho(self, cpf):
        return self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': cpf},
            format='json',
        )

    def _remover_cpf_rascunho(self, cpf):
        return self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho-remover',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': cpf},
            format='json',
        )

    def _registrar_lote_cpf(self, versao=None):
        if versao is None:
            versao = self._versao_cpf()
        return self.client.post(
            reverse('transporte:conferencia-entrada-sem-ticket', kwargs={'pk': self.execucao.pk}),
            {'versao': versao},
            format='json',
        )

    def _adicionar_cpfs_e_registrar(self, cpfs):
        ultima = None
        for cpf in cpfs:
            ultima = self._adicionar_cpf_rascunho(cpf)
            if ultima.status_code >= 400:
                return ultima
        return self._registrar_lote_cpf()

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
        self.assertGreaterEqual(len(reservas.data['dados']), 1)

        chamada = self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'versao': self._versao_chamada()},
            format='json',
        )
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
            [item['aluno']['nome'] for item in reservas.data['dados']],
            ['Aluno PcD', 'Reservado'],
        )
        self.assertEqual(
            {item['aluno']['nome']: item['posicao']['atual'] for item in reservas.data['dados']},
            {'Aluno PcD': 2, 'Reservado': 1},
        )
        por_nome = {item['aluno']['nome']: item['aluno'] for item in reservas.data['dados']}
        self.assertTrue(por_nome['Aluno PcD']['tem_deficiencia'])
        self.assertFalse(por_nome['Reservado']['tem_deficiencia'])

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
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        ticket = Ticket.objects.get(
            aluno=self.aluno_reserva,
            execucao_rota=self.execucao,
        )
        self._classificar_rascunho(ticket.codigo, 'ausente')
        resposta = self._finalizar_chamada()
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        outro = Ticket.objects.get(aluno=segundo, execucao_rota=self.execucao)
        outro.refresh_from_db()
        self.assertEqual(outro.status, StatusTicket.EMBARCADO)

        segunda = self._finalizar_chamada()
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)

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
        resposta = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.data['dados']), 1)
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

    def test_lote_de_cpfs_grava_varios_e_rejeita_acima_das_vagas(self):
        self.execucao.quantidade_vagas = 4
        self.execucao.save(update_fields=['quantidade_vagas'])
        self._iniciar_e_finalizar_chamada()
        primeiro = criar_aluno('21000000050')
        segunda_pessoa = criar_aluno('21000000051')
        terceira_pessoa = criar_aluno('21000000052')
        quarta_pessoa = criar_aluno('21000000053')
        primeira = self._adicionar_cpfs_e_registrar(
            [primeiro.usuario.cpf, segunda_pessoa.usuario.cpf],
        )
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(primeira.data['dados']), 2)
        segunda = self._adicionar_cpfs_e_registrar(
            [terceira_pessoa.usuario.cpf, quarta_pessoa.usuario.cpf],
        )
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=terceira_pessoa,
                execucao_rota=self.execucao,
            ).exists()
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_lote_com_cpfs_duplicados_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000054')
        self._adicionar_cpf_rascunho(outro.usuario.cpf)
        resposta = self._adicionar_cpf_rascunho(outro.usuario.cpf)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=outro,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_ausente_entra_por_cpf_mantendo_strike(self):
        self.execucao.quantidade_vagas = 3
        self.execucao.save(update_fields=['quantidade_vagas'])
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._iniciar_e_finalizar_chamada(ausentes=[str(ticket.codigo)])
        resposta = self._adicionar_cpfs_e_registrar([self.aluno_reserva.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        self.assertTrue(
            EntradaSemTicket.objects.filter(
                aluno=self.aluno_reserva,
                execucao_rota=self.execucao,
            ).exists()
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_ausente_com_tres_strikes_entra_por_cpf(self):
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._iniciar_e_finalizar_chamada(ausentes=[str(ticket.codigo)])
        for indice in range(2):
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
        resposta = self._adicionar_cpfs_e_registrar([self.aluno_reserva.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)
        self.assertTrue(Strike.objects.filter(ticket=ticket).exists())
        self.assertTrue(
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
        resposta = self._adicionar_cpfs_e_registrar([walk_in.usuario.cpf])
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
        resposta = self._adicionar_cpfs_e_registrar(['00000000000'])
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
        self.assertFalse(self.execucao.entradas_cpf_concluidas)

    def test_finalizar_com_rascunho_cpf_aberto_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000093')
        self.assertEqual(
            self._adicionar_cpf_rascunho(outro.usuario.cpf).status_code,
            status.HTTP_200_OK,
        )
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(MENSAGEM_RASCUNHO_CPF_ABERTO, str(resposta.data))
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EM_EMBARQUE)
        self.assertFalse(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).exists()
        )

    def test_finalizar_apos_esvaziar_rascunho_cpf(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000102')
        self._adicionar_cpf_rascunho(outro.usuario.cpf)
        self.assertEqual(
            self._remover_cpf_rascunho(outro.usuario.cpf).status_code,
            status.HTTP_200_OK,
        )
        resposta = self.client.post(
            reverse('transporte:conferencia-finalizar', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.execucao.refresh_from_db()
        self.assertEqual(self.execucao.status, StatusExecucaoRota.EMBARCADO)
        self.assertFalse(self.execucao.entradas_cpf_concluidas)
        self.assertFalse(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).exists()
        )

    def test_finalizar_nao_contempla_quem_embarcou_por_cpf(self):
        self._iniciar_e_finalizar_chamada()
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        self.assertEqual(
            self._adicionar_cpfs_e_registrar([espera.aluno.usuario.cpf]).status_code,
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
        resposta = self._adicionar_cpfs_e_registrar([aluno_cancelou.usuario.cpf])
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
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'versao': self._versao_chamada()},
            format='json',
        )
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
        with self._entrar_na_janela_monitoramento():
            iniciar = self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self.assertEqual(iniciar.status_code, status.HTTP_200_OK)
        chamada = self.client.post(
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'versao': self._versao_chamada()},
            format='json',
        )
        self.assertEqual(chamada.status_code, status.HTTP_200_OK)
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

    def test_replay_chamada_com_ausentes_diferentes_retorna_400(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        self._finalizar_chamada()
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        classificacao = self._classificar_rascunho(ticket.codigo, 'ausente')
        self.assertEqual(classificacao.status_code, status.HTTP_400_BAD_REQUEST)
        resposta = self._finalizar_chamada(versao=self._versao_chamada() + 1)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ausentes_duplicados_retornam_400(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        primeira = self._classificar_rascunho(ticket.codigo, 'ausente')
        segunda = self._classificar_rascunho(ticket.codigo, 'ausente')
        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(
            primeira.data['dados']['versao_chamada'],
            segunda.data['dados']['versao_chamada'],
        )

    def test_cpf_de_espera_contempla_e_cria_entrada(self):
        self._iniciar_e_finalizar_chamada()
        espera = Ticket.objects.get(aluno=self.aluno_espera, execucao_rota=self.execucao)
        resposta = self._adicionar_cpfs_e_registrar([espera.aluno.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.data['dados']), 1)
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
        replay = self._registrar_lote_cpf()
        self.assertEqual(replay.status_code, status.HTTP_200_OK)
        self.assertEqual(len(replay.data['dados']), 1)
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

    def test_validar_cpf_depois_do_lote_concluido_retorna_400(self):
        self.execucao.quantidade_vagas = 3
        self.execucao.save(update_fields=['quantidade_vagas'])
        self._iniciar_e_finalizar_chamada()
        url_lote = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        url_validar = reverse(
            'transporte:conferencia-entrada-sem-ticket-validar',
            kwargs={'pk': self.execucao.pk},
        )
        incluido = criar_aluno('21000000067')
        self.assertEqual(
            self._adicionar_cpfs_e_registrar([incluido.usuario.cpf]).status_code,
            status.HTTP_201_CREATED,
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

    def test_validar_cpf_depois_do_lote_vazio_continua_elegivel(self):
        self._iniciar_e_finalizar_chamada()
        url_lote = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        self.assertEqual(
            self._registrar_lote_cpf().status_code,
            status.HTTP_201_CREATED,
        )
        walk_in = criar_aluno('21000000068')
        resposta = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': walk_in.usuario.cpf},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['elegivel'])

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
        self.assertEqual(reservado.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aluno_nao_matriculado_nao_entra_por_cpf(self):
        from Academico.alunos.choices import SituacaoAluno

        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000045', situacao=SituacaoAluno.FORMADO)
        resposta = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
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

    def test_replay_chamada_com_mesmo_conjunto_retorna_200(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        self._classificar_rascunho(ticket.codigo, 'ausente')
        primeira = self._finalizar_chamada()
        segunda = self._finalizar_chamada()
        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)

    def test_replay_chamada_nao_quebra_quando_rascunho_cpf_avanca(self):
        versao_chamada = self._iniciar_e_finalizar_chamada().data['dados']['versao_chamada']
        outro = criar_aluno('21000000093')
        self._adicionar_cpf_rascunho(outro.usuario.cpf)
        self.assertNotEqual(self._versao_cpf(), 0)
        replay = self._finalizar_chamada(versao=versao_chamada)
        self.assertEqual(replay.status_code, status.HTTP_200_OK)

    def test_replay_lote_cpf_mesmo_conjunto_retorna_200(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000060')
        primeira = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
        segunda = self._registrar_lote_cpf()
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(primeira.data['dados'], segunda.data['dados'])
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
        primeira = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
        segunda = self._registrar_lote_cpf()
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).count(),
            1,
        )

    def test_replay_lote_cpf_conjunto_diferente_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        primeiro = criar_aluno('21000000061')
        segundo = criar_aluno('21000000062')
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        primeira = self._adicionar_cpfs_e_registrar([primeiro.usuario.cpf])
        segunda = self._adicionar_cpf_rascunho(segundo.usuario.cpf)
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            EntradaSemTicket.objects.filter(
                aluno=segundo,
                execucao_rota=self.execucao,
            ).exists()
        )

    def test_lote_vazio_nao_conclui_e_permite_persistir_depois(self):
        self._iniciar_e_finalizar_chamada()
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        vazio = self._registrar_lote_cpf()
        self.assertEqual(vazio.status_code, status.HTTP_201_CREATED)
        self.assertEqual(vazio.data['dados'], [])
        self.execucao.refresh_from_db()
        self.assertFalse(self.execucao.entradas_cpf_concluidas)
        segundo_vazio = self._registrar_lote_cpf()
        self.assertEqual(segundo_vazio.status_code, status.HTTP_201_CREATED)
        self.execucao.refresh_from_db()
        self.assertFalse(self.execucao.entradas_cpf_concluidas)
        omitido = self._registrar_lote_cpf()
        self.assertEqual(omitido.status_code, status.HTTP_201_CREATED)
        outro = criar_aluno('21000000063')
        persistido = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
        self.assertEqual(persistido.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(persistido.data['dados']), 1)

    def test_lote_vazio_depois_do_lote_real_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        url = reverse(
            'transporte:conferencia-entrada-sem-ticket',
            kwargs={'pk': self.execucao.pk},
        )
        outro = criar_aluno('21000000064')
        primeira = self._adicionar_cpfs_e_registrar([outro.usuario.cpf])
        vazio = self._registrar_lote_cpf(versao=self._versao_cpf() + 1)
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(vazio.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lote_maior_que_vagas_no_primeiro_envio_retorna_400(self):
        self._iniciar_e_finalizar_chamada()
        primeiro = criar_aluno('21000000065')
        segundo = criar_aluno('21000000066')
        resposta = self._adicionar_cpfs_e_registrar([primeiro.usuario.cpf, segundo.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            EntradaSemTicket.objects.filter(execucao_rota=self.execucao).exists()
        )
        self.execucao.refresh_from_db()
        self.assertFalse(self.execucao.entradas_cpf_concluidas)

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
            reverse('transporte:conferencia-finalizar-chamada', kwargs={'pk': self.execucao.pk}),
            {'versao': self._versao_chamada()},
            format='json',
        )
        cpf = self._adicionar_cpfs_e_registrar([criar_aluno('21000000077').usuario.cpf])
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
        resposta = self._adicionar_cpfs_e_registrar(
            [self.aluno_espera.usuario.cpf, self.aluno_extra.usuario.cpf],
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
        resposta = self._adicionar_cpfs_e_registrar([self.aluno_espera.usuario.cpf, walk_in.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.data['dados']), 2)
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
        resposta = self._adicionar_cpfs_e_registrar([self.aluno_espera.usuario.cpf])
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=outra).status,
            StatusTicket.EM_ESPERA,
        )
        self.assertEqual(
            Ticket.objects.get(aluno=self.aluno_extra, execucao_rota=self.execucao).status,
            StatusTicket.EM_ESPERA,
        )

    def test_rascunho_presente_e_ausente_aparecem_no_snapshot(self):
        segundo = criar_aluno('21000000090', nome='Segundo reservado')
        ticket_presente = Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=segundo,
            status=StatusTicket.RESERVADO,
            posicao_reserva=2,
            reservado_em=timezone.now(),
        )
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        ticket_ausente = Ticket.objects.get(
            aluno=self.aluno_reserva,
            execucao_rota=self.execucao,
        )
        outro_conferente = criar_conferente(cpf='21000000091')
        self._classificar_rascunho(ticket_ausente.codigo, 'ausente')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(outro_conferente)}')
        self._classificar_rascunho(ticket_presente.codigo, 'presente')
        rascunho = self.client.get(
            reverse('transporte:conferencia-chamada-rascunho', kwargs={'pk': self.execucao.pk}),
        )
        self.assertEqual(rascunho.status_code, status.HTTP_200_OK)
        dados = rascunho.data['dados']
        self.assertEqual(dados['ausentes'], [str(ticket_ausente.codigo)])
        self.assertEqual(dados['presentes'], [str(ticket_presente.codigo)])
        self.assertGreaterEqual(dados['versao'], 2)
        reservas = self.client.get(
            reverse('transporte:conferencia-reservas', kwargs={'pk': self.execucao.pk}),
            {'paginacao': 100},
        )
        self.assertEqual(reservas.status_code, status.HTTP_200_OK)
        por_codigo = {item['codigo']: item for item in reservas.data['dados']}
        self.assertIn(str(ticket_ausente.codigo), por_codigo)
        self.assertIn(str(ticket_presente.codigo), por_codigo)
        self.assertNotIn('classificacao_rascunho', por_codigo[str(ticket_ausente.codigo)])
        self.assertNotIn('versao_chamada', por_codigo[str(ticket_ausente.codigo)])
        self.assertNotIn('classificacao_rascunho', por_codigo[str(ticket_presente.codigo)])
        self.assertNotIn('versao_chamada', por_codigo[str(ticket_presente.codigo)])
        self.assertEqual(por_codigo[str(ticket_ausente.codigo)]['status'], StatusTicket.RESERVADO)
        self.assertEqual(por_codigo[str(ticket_presente.codigo)]['status'], StatusTicket.RESERVADO)
        limpar = self._classificar_rascunho(ticket_ausente.codigo, None)
        self.assertEqual(limpar.status_code, status.HTTP_200_OK)
        rascunho = self.client.get(
            reverse('transporte:conferencia-chamada-rascunho', kwargs={'pk': self.execucao.pk}),
        )
        self.assertNotIn(str(ticket_ausente.codigo), rascunho.data['dados']['ausentes'])
        self.assertIn(str(ticket_ausente.codigo), rascunho.data['dados']['nao_classificados'])

    def test_finalizar_chamada_rejeita_versao_desatualizada(self):
        with self._entrar_na_janela_monitoramento():
            self.client.post(
                reverse('transporte:conferencia-iniciar', kwargs={'pk': self.execucao.pk}),
            )
        ticket = Ticket.objects.get(aluno=self.aluno_reserva, execucao_rota=self.execucao)
        versao_antiga = self._versao_chamada()
        self._classificar_rascunho(ticket.codigo, 'ausente')
        resposta = self._finalizar_chamada(versao=versao_antiga)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.RESERVADO)
        resposta = self._finalizar_chamada()
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, StatusTicket.AUSENTE)

    def test_rascunho_cpf_aparece_no_get_e_some_ao_remover(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000092')
        validar = self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-validar',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        self.assertEqual(validar.status_code, status.HTTP_200_OK)
        listagem = self.client.get(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho',
                kwargs={'pk': self.execucao.pk},
            ),
        )
        self.assertEqual(listagem.status_code, status.HTTP_200_OK)
        self.assertEqual(listagem.data['dados']['alunos'], [])
        self.assertFalse(listagem.data['dados']['concluido'])
        self._adicionar_cpf_rascunho(outro.usuario.cpf)
        listagem = self.client.get(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho',
                kwargs={'pk': self.execucao.pk},
            ),
        )
        self.assertEqual(len(listagem.data['dados']['alunos']), 1)
        self.assertFalse(listagem.data['dados']['concluido'])
        self.client.post(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho-remover',
                kwargs={'pk': self.execucao.pk},
            ),
            {'cpf': outro.usuario.cpf},
            format='json',
        )
        listagem = self.client.get(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho',
                kwargs={'pk': self.execucao.pk},
            ),
        )
        self.assertEqual(listagem.data['dados']['alunos'], [])
        self.assertFalse(listagem.data['dados']['concluido'])

    def test_rascunho_cpf_depois_do_lote_vem_vazio_e_concluido(self):
        self._iniciar_e_finalizar_chamada()
        outro = criar_aluno('21000000103')
        self.assertEqual(
            self._adicionar_cpfs_e_registrar([outro.usuario.cpf]).status_code,
            status.HTTP_201_CREATED,
        )
        listagem = self.client.get(
            reverse(
                'transporte:conferencia-entrada-sem-ticket-rascunho',
                kwargs={'pk': self.execucao.pk},
            ),
        )
        self.assertEqual(listagem.status_code, status.HTTP_200_OK)
        self.assertEqual(listagem.data['dados']['alunos'], [])
        self.assertTrue(listagem.data['dados']['concluido'])
        self.execucao.refresh_from_db()
        self.assertTrue(self.execucao.entradas_cpf_concluidas)
        self.assertEqual(len(self.execucao.entradas_cpf_rascunho or []), 1)
