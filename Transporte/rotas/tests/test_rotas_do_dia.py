from datetime import time

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Identidade.usuarios.models import Usuario
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.motoristas.models import Motorista
from Transporte.percursos.models import Percurso
from Transporte.rotas.choices import DiaSemana, dia_semana_da_data
from Transporte.rotas.models import Rota
from Transporte.tests_utils import criar_aluno
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


def criar_usuario(cpf, nome, **kwargs):
    return Usuario.objects.create_user(
        cpf=cpf,
        nome=nome,
        password='Senha@123',
        **kwargs,
    )


def criar_motorista(cpf, nome):
    usuario = criar_usuario(cpf, nome)
    motorista = Motorista.objects.create(usuario=usuario)
    return usuario, motorista


def criar_rota(horario_saida, *, dia_semana=None, ativo=True, percurso_ativo=True):
    percurso = Percurso.objects.create(
        apelido=f'Percurso {horario_saida:%H%M}',
        descricao=f'IFPI – Parada {horario_saida:%H:%M}',
        ativo=percurso_ativo,
    )
    return Rota.objects.create(
        percurso=percurso,
        horario_saida=horario_saida,
        dia_semana=dia_semana or dia_semana_da_data(timezone.localdate()),
        quantidade_vagas=84,
        ativo=ativo,
    )


class RotasDoDiaAPITestCase(APITestCase):

    def setUp(self):
        self.usuario_motorista, self.motorista = criar_motorista(
            '71000000001',
            'Motorista Um',
        )
        self.outro_usuario_motorista, _ = criar_motorista(
            '71000000002',
            'Motorista Dois',
        )
        self.usuario_comum = criar_usuario('71000000003', 'Usuário Comum')
        self.usuario_ti = criar_usuario('71000000004', 'Pessoa TI', is_staff=True)
        self.rota = criar_rota(time(12, 0))
        self.url_lista = reverse('transporte:motorista-rotas-do-dia')

    def autenticar(self, usuario):
        self.client.force_authenticate(usuario)

    def test_motorista_ve_informacoes_das_rotas_do_dia(self):
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertNotIn('count', resposta.data)
        self.assertEqual(len(resposta.data['dados']), 1)
        item = resposta.data['dados'][0]
        self.assertEqual(
            set(item),
            {
                'id',
                'data',
                'horario',
                'dia_semana',
                'dia_semana_display',
                'capacidade',
                'percurso',
                'percurso_apelido',
                'execucao_id',
                'status_execucao',
                'status_execucao_display',
                'tickets_solicitados',
            },
        )
        self.assertEqual(item['id'], self.rota.pk)
        self.assertEqual(item['data'], timezone.localdate().isoformat())
        self.assertEqual(item['horario'], '12:00')
        self.assertEqual(item['capacidade'], 84)
        self.assertEqual(item['percurso'], self.rota.percurso.descricao)
        self.assertEqual(item['percurso_apelido'], self.rota.percurso.apelido)
        self.assertEqual(item['dia_semana'], dia_semana_da_data(timezone.localdate()))
        self.assertIsNone(item['execucao_id'])
        self.assertIsNone(item['status_execucao'])
        self.assertIsNone(item['status_execucao_display'])
        self.assertEqual(item['tickets_solicitados'], 0)

    def test_motorista_ve_status_capacidade_e_tickets_reais_da_execucao(self):
        execucao = ExecucaoRota().business.criar_execucao(
            self.rota.pk,
            timezone.localdate(),
        )
        execucao.quantidade_vagas = 80
        execucao.status = StatusExecucaoRota.FECHADA
        execucao.save(update_fields=['quantidade_vagas', 'status'])

        reservado = criar_aluno('71000000005', nome='Aluno Reservado')
        embarcado = criar_aluno('71000000006', nome='Aluno Embarcado')
        em_espera = criar_aluno('71000000007', nome='Aluno em Espera')
        cancelado = criar_aluno('71000000008', nome='Aluno Cancelado')
        Ticket.objects.create(
            execucao_rota=execucao,
            aluno=reservado,
            status=StatusTicket.RESERVADO,
        )
        Ticket.objects.create(
            execucao_rota=execucao,
            aluno=embarcado,
            status=StatusTicket.EMBARCADO,
        )
        Ticket.objects.create(
            execucao_rota=execucao,
            aluno=em_espera,
            status=StatusTicket.EM_ESPERA,
        )
        Ticket.objects.create(
            execucao_rota=execucao,
            aluno=cancelado,
            status=StatusTicket.CANCELADO,
        )
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        item = resposta.data['dados'][0]
        self.assertEqual(item['execucao_id'], execucao.pk)
        self.assertEqual(item['status_execucao'], StatusExecucaoRota.FECHADA)
        self.assertEqual(item['status_execucao_display'], 'Reservas fechadas')
        self.assertEqual(item['capacidade'], 80)
        self.assertEqual(item['tickets_solicitados'], 2)

    def test_todos_os_motoristas_veem_todas_as_rotas(self):
        outra_rota = criar_rota(time(18, 0))
        self.autenticar(self.outro_usuario_motorista)

        resposta = self.client.get(self.url_lista)

        ids = {item['id'] for item in resposta.data['dados']}
        self.assertEqual(ids, {self.rota.pk, outra_rota.pk})

    def test_listagem_ordena_por_horario(self):
        rota_mais_cedo = criar_rota(time(6, 0))
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(
            [item['id'] for item in resposta.data['dados']],
            [rota_mais_cedo.pk, self.rota.pk],
        )

    def test_horarios_iguais_ordenam_pelo_apelido_do_percurso(self):
        percurso = Percurso.objects.create(
            apelido='A - Primeiro percurso',
            descricao='IFPI – Primeira parada',
        )
        rota_primeiro_percurso = Rota.objects.create(
            percurso=percurso,
            horario_saida=self.rota.horario_saida,
            dia_semana=self.rota.dia_semana,
            quantidade_vagas=84,
        )
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(
            [item['id'] for item in resposta.data['dados']],
            [rota_primeiro_percurso.pk, self.rota.pk],
        )

    def test_dia_sem_rotas_retorna_lista_vazia(self):
        self.rota.ativo = False
        self.rota.save(update_fields=['ativo'])
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])

    def test_oculta_rota_inativa_percurso_inativo_e_outro_dia(self):
        criar_rota(time(13, 0), ativo=False)
        criar_rota(time(14, 0), percurso_ativo=False)
        outro_dia = (
            DiaSemana.TERCA
            if dia_semana_da_data(timezone.localdate()) != DiaSemana.TERCA
            else DiaSemana.QUARTA
        )
        criar_rota(time(15, 0), dia_semana=outro_dia)
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual([item['id'] for item in resposta.data['dados']], [self.rota.pk])

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_comum_retorna_403(self):
        self.autenticar(self.usuario_comum)
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_ti_sem_perfil_motorista_retorna_403(self):
        self.autenticar(self.usuario_ti)
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_motorista_inativo_retorna_403(self):
        self.motorista.ativo = False
        self.motorista.save(update_fields=['ativo'])
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_conta_do_motorista_inativa_retorna_403(self):
        self.usuario_motorista.ativo = False
        self.usuario_motorista.save(update_fields=['ativo'])
        self.autenticar(self.usuario_motorista)

        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_endpoint_aceita_somente_get(self):
        self.autenticar(self.usuario_motorista)

        resposta = self.client.post(self.url_lista, {})

        self.assertEqual(resposta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_motorista_recebe_capacidade_no_payload(self):
        self.assertEqual(
            self.usuario_motorista.permissoes['transporte'],
            {'gerenciar': False, 'motorista': True, 'reservar': False},
        )
        self.assertEqual(
            self.usuario_ti.permissoes['transporte'],
            {'gerenciar': True, 'motorista': False, 'reservar': False},
        )
