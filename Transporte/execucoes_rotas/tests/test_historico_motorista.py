from datetime import time, timedelta

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import AuthorizationException
from Transporte.entradas_sem_ticket.models import EntradaSemTicket
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.motoristas.models import Motorista
from Transporte.tests_utils import criar_aluno, criar_conferente, criar_rota_e_execucao, criar_usuario
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class HistoricoMotoristaAPITestCase(APITestCase):
    def setUp(self):
        self.usuario = criar_usuario('73000000001', 'Motorista')
        self.motorista = Motorista.objects.create(usuario=self.usuario)
        self.admin = criar_usuario('73000000002', 'Administrador', admin=True)
        self.rota, self.execucao = criar_rota_e_execucao(vagas=84, dias_ate_execucao=-2)
        self.rota.percurso.apelido = 'Rota Pontões'
        self.rota.percurso.save()
        self.execucao.status = StatusExecucaoRota.FINALIZADA
        self.execucao.rota_iniciada_em = self.execucao.data_hora_saida
        self.execucao.rota_finalizada_em = self.execucao.data_hora_saida + timedelta(minutes=42, seconds=17)
        self.execucao.rota_iniciada_por = self.usuario
        self.execucao.save()
        self.lista = reverse('transporte:motorista-historico-rotas-list')
        self.percursos = reverse('transporte:motorista-historico-percursos-list')
        self.detalhe = reverse('transporte:motorista-historico-rotas-detail', args=[self.execucao.pk])
        self.client.force_authenticate(self.usuario)

    def criar_passageiros(self):
        for indice, estado in enumerate([
            StatusTicket.EMBARCADO, StatusTicket.EMBARCADO, StatusTicket.EMBARCADO,
            StatusTicket.AUSENTE, StatusTicket.AUSENTE, StatusTicket.CANCELADO,
            StatusTicket.NAO_CONTEMPLADO,
        ]):
            aluno = criar_aluno(f'731000000{indice:02d}', nome=f'Passageiro {indice}')
            Ticket.objects.create(execucao_rota=self.execucao, aluno=aluno, status=estado)
        for indice in range(2):
            aluno = criar_aluno(f'732000000{indice:02d}', nome=f'Sem ticket {indice}')
            EntradaSemTicket.objects.create(
                execucao_rota=self.execucao, aluno=aluno, cpf=aluno.usuario.cpf,
                data_hora_entrada=self.execucao.data_hora_saida,
            )

    def test_contagens_reais_sem_multiplicar_joins(self):
        self.criar_passageiros()
        resposta = self.client.get(self.lista)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 1)
        item = resposta.data['dados'][0]
        self.assertEqual((item['presentes'], item['ausentes'], item['sem_ticket']), (3, 2, 2))
        self.assertEqual(item['duracao_rota_segundos'], 2537)
        self.assertEqual(item['horario'], '12:00')
        self.assertEqual(item['data'], self.execucao.data_execucao.isoformat())

    def test_detalhes_coerentes_e_sem_dados_sensiveis(self):
        self.criar_passageiros()
        resposta = self.client.get(self.detalhe)
        self.assertEqual(resposta.status_code, 200)
        item = resposta.data['dados']
        self.assertEqual(item['motorista_nome'], 'Motorista')
        self.assertEqual(len(item['tickets_presentes']), item['presentes'])
        self.assertEqual(len(item['tickets_ausentes']), item['ausentes'])
        self.assertEqual(len(item['passageiros_sem_ticket']), item['sem_ticket'])
        for passageiro in item['tickets_presentes'] + item['tickets_ausentes'] + item['passageiros_sem_ticket']:
            self.assertEqual(set(passageiro), {'nome'})

    def test_so_aparece_depois_de_finalizar_viagem(self):
        self.execucao.rota_finalizada_em = None
        self.execucao.save()
        self.assertEqual(self.client.get(self.lista).data['count'], 0)
        self.assertEqual(self.client.get(self.detalhe).status_code, 404)
        self.assertEqual(self.client.get(self.percursos).data['count'], 0)
        finalizar = reverse('transporte:motorista-finalizar-rota', args=[self.execucao.pk])
        self.assertEqual(self.client.post(finalizar, {}).status_code, 200)
        self.assertEqual(self.client.get(self.lista).data['count'], 1)
        self.assertEqual(self.client.get(self.detalhe).status_code, 200)

    def test_conferencia_finalizada_sem_viagem_nao_entra(self):
        self.execucao.rota_iniciada_em = None
        self.execucao.rota_finalizada_em = None
        self.execucao.save()
        self.assertEqual(self.client.get(self.lista).data['count'], 0)
        self.assertEqual(self.client.get(self.detalhe).status_code, 404)

    def test_busca_filtro_data_percurso_e_ordenacao(self):
        outra_rota, outra = criar_rota_e_execucao(dias_ate_execucao=-1, horario_saida=time(8))
        outra.status = StatusExecucaoRota.FINALIZADA
        outra.rota_iniciada_em = outra.data_hora_saida
        outra.rota_finalizada_em = outra.data_hora_saida + timedelta(minutes=20)
        outra.save()
        self.assertEqual(self.client.get(self.lista).data['dados'][0]['id'], outra.pk)
        self.assertEqual(self.client.get(self.lista, {'ordenacao': 'horario'}).data['dados'][0]['id'], outra.pk)
        for filtro in (
            {'busca': 'pontões'}, {'busca': 'pontOes'},
            {'busca': self.execucao.data_execucao.strftime('%d/%m/%Y')},
            {'data': self.execucao.data_execucao.isoformat()},
            {'percurso_id': self.rota.percurso_id},
        ):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(self.lista, filtro)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual([item['id'] for item in resposta.data['dados']], [self.execucao.pk])
        self.assertEqual(self.client.get(self.lista, {'busca': 'não existe'}).data['count'], 0)
        filtros = {'percurso_id': outra_rota.percurso_id, 'data': self.execucao.data_execucao.isoformat()}
        self.assertEqual(self.client.get(self.lista, filtros).data['count'], 0)

    def test_filtros_invalidos_nao_quebram_nem_ampliam_escopo(self):
        resposta = self.client.get(self.lista, {'data': 'invalida', 'ordenacao': '__dict__', 'percurso_id': 'abc'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 1)
        self.assertEqual(self.client.get(self.lista, {'percurso_id': '9' * 500}).status_code, 200)

    def test_paginacao_estavel_e_percursos_sem_duplicata(self):
        for indice in range(1, 7):
            ExecucaoRota.objects.create(
                rota=self.rota, data_execucao=self.execucao.data_execucao - timedelta(days=7 * indice),
                data_hora_saida=self.execucao.data_hora_saida - timedelta(days=7 * indice),
                quantidade_vagas=84, status=StatusExecucaoRota.FINALIZADA,
                rota_iniciada_em=self.execucao.rota_iniciada_em - timedelta(days=7 * indice),
                rota_finalizada_em=self.execucao.rota_finalizada_em - timedelta(days=7 * indice),
            )
        primeira = self.client.get(self.lista, {'paginacao': 5}).data
        segunda = self.client.get(self.lista, {'paginacao': 5, 'page': 2}).data
        self.assertEqual(primeira['count'], 7)
        self.assertEqual(len(primeira['dados']), 5)
        self.assertEqual(len(segunda['dados']), 2)
        self.assertFalse({item['id'] for item in primeira['dados']} & {item['id'] for item in segunda['dados']})
        self.assertEqual(self.client.get(self.percursos).data['count'], 1)

    def test_historico_preserva_rota_percurso_e_motorista_desativados(self):
        self.rota.ativo = False
        self.rota.save()
        self.rota.percurso.ativo = False
        self.rota.percurso.save()
        self.motorista.ativo = False
        self.motorista.save()
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.lista).data['count'], 1)
        self.assertEqual(self.client.get(self.percursos).data['count'], 1)
        self.assertEqual(self.client.get(self.detalhe).status_code, 200)

    def test_outro_motorista_ativo_e_admin_acessam(self):
        outro = criar_usuario('73000000003', 'Outro motorista')
        Motorista.objects.create(usuario=outro)
        for usuario in (outro, self.admin):
            self.client.force_authenticate(usuario)
            for url in (self.lista, self.percursos, self.detalhe):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_aluno_conferente_usuario_comum_e_anonimo_nao_acessam(self):
        aluno = criar_aluno('73000000004')
        comum = criar_usuario('73000000005')
        conferente = criar_conferente()
        for usuario in (aluno.usuario, comum, conferente, None):
            self.client.force_authenticate(usuario)
            for url in (self.lista, self.percursos, self.detalhe):
                with self.subTest(usuario=usuario, url=url):
                    resposta = self.client.get(url, {'percurso_id': self.rota.percurso_id})
                    self.assertEqual(resposta.status_code, 401 if usuario is None else 403)
        with self.assertRaises(AuthorizationException):
            ExecucaoRota().business.listar_historico(comum)

    def test_motorista_ou_conta_inativos_nao_acessam(self):
        self.motorista.ativo = False
        self.motorista.save()
        for url in (self.lista, self.percursos, self.detalhe):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.motorista.ativo = True
        self.motorista.save()
        self.usuario.ativo = False
        self.usuario.save()
        for url in (self.lista, self.percursos, self.detalhe):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_detalhes_carregam_passageiros_sem_query_por_pessoa(self):
        self.criar_passageiros()
        with CaptureQueriesContext(connection) as consultas:
            resposta = self.client.get(self.detalhe)
        self.assertEqual(resposta.status_code, 200)
        self.assertLessEqual(len(consultas), 6)

    def test_endpoints_sao_somente_leitura_e_id_inexistente_retorna_404(self):
        for url in (self.lista, self.percursos, self.detalhe):
            self.assertEqual(self.client.post(url, {}).status_code, 405)
        inexistente = reverse('transporte:motorista-historico-rotas-detail', args=[999999999])
        self.assertEqual(self.client.get(inexistente).status_code, 404)
