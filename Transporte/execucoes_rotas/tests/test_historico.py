from datetime import time, timedelta

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import AuthorizationException
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor
from Transporte.entradas_sem_ticket.models import EntradaSemTicket
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.motoristas.models import Motorista
from Transporte.tests_utils import (
    criar_aluno,
    criar_aluno_pcd,
    criar_conferente,
    criar_rota_e_execucao,
    criar_usuario,
)
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class HistoricoConferenciaAPITestCase(APITestCase):
    def setUp(self):
        self.conferente = criar_conferente()
        self.admin = criar_usuario('74000000002', 'Administrador', admin=True)
        self.rota, self.execucao = criar_rota_e_execucao(vagas=84, dias_ate_execucao=-2)
        self.rota.percurso.apelido = 'Rota Pontões'
        self.rota.percurso.save()
        self.execucao.status = StatusExecucaoRota.FINALIZADA
        self.execucao.embarcado_em = self.execucao.data_hora_saida
        self.execucao.rota_iniciada_em = self.execucao.data_hora_saida
        self.execucao.rota_finalizada_em = self.execucao.data_hora_saida + timedelta(minutes=42, seconds=17)
        self.execucao.conferencia_finalizada_por = self.conferente
        self.execucao.save()
        self.lista = reverse('transporte:execucao-rota-historico-list')
        self.percursos = reverse('transporte:execucao-rota-historico-percursos-list')
        self.detalhe = reverse('transporte:execucao-rota-historico-detail', args=[self.execucao.pk])
        self.client.force_authenticate(self.conferente)

    def criar_passageiros(self):
        presentes = [
            criar_aluno('74100000000', nome='Presente A'),
            criar_aluno_pcd('74100000001', nome='Presente PcD'),
            criar_aluno('74100000002', nome='Presente C'),
        ]
        for aluno in presentes:
            Ticket.objects.create(
                execucao_rota=self.execucao, aluno=aluno, status=StatusTicket.EMBARCADO,
            )
        for indice in range(2):
            aluno = criar_aluno(f'7410000001{indice}', nome=f'Ausente {indice}')
            Ticket.objects.create(
                execucao_rota=self.execucao, aluno=aluno, status=StatusTicket.AUSENTE,
            )
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=criar_aluno('74100000020', nome='Cancelado'),
            status=StatusTicket.CANCELADO,
        )
        contemplado = criar_aluno('74100000021', nome='Contemplado')
        Ticket.objects.create(
            execucao_rota=self.execucao, aluno=contemplado, status=StatusTicket.CONTEMPLADO,
        )
        EntradaSemTicket.objects.create(
            execucao_rota=self.execucao, aluno=contemplado, cpf=contemplado.usuario.cpf,
            data_hora_entrada=self.execucao.data_hora_saida,
        )
        walkin = criar_aluno('74200000000', nome='Sem ticket 0')
        EntradaSemTicket.objects.create(
            execucao_rota=self.execucao, aluno=walkin, cpf=walkin.usuario.cpf,
            data_hora_entrada=self.execucao.data_hora_saida,
        )

    def test_contagens_e_filtros_iguais_ao_motorista(self):
        self.criar_passageiros()
        resposta = self.client.get(self.lista)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 1)
        item = resposta.data['dados'][0]
        self.assertEqual((item['presentes'], item['ausentes'], item['sem_ticket']), (3, 2, 2))
        self.assertNotIn('conferencia_finalizada_por', item)
        outra_rota, outra = criar_rota_e_execucao(dias_ate_execucao=-1, horario_saida=time(8))
        outra.status = StatusExecucaoRota.FINALIZADA
        outra.rota_iniciada_em = outra.data_hora_saida
        outra.rota_finalizada_em = outra.data_hora_saida + timedelta(minutes=20)
        outra.save()
        self.assertEqual(self.client.get(self.lista).data['dados'][0]['id'], outra.pk)
        for filtro in (
            {'busca': 'pontões'},
            {'data': self.execucao.data_execucao.isoformat()},
            {'percurso_id': self.rota.percurso_id},
        ):
            with self.subTest(filtro=filtro):
                filtrada = self.client.get(self.lista, filtro)
                self.assertEqual(filtrada.status_code, 200)
                self.assertEqual([item['id'] for item in filtrada.data['dados']], [self.execucao.pk])

    def test_detalhe_traz_conferente_e_dados_do_aluno(self):
        self.criar_passageiros()
        resposta = self.client.get(self.detalhe)
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.data['dados']
        self.assertEqual(dados['conferencia_finalizada_por']['id'], self.conferente.pk)
        self.assertEqual(dados['conferencia_finalizada_por']['nome'], self.conferente.nome)
        self.assertIsNotNone(dados['conferencia_finalizada_em'])
        self.assertEqual(len(dados['tickets_presentes']), dados['presentes'])
        self.assertEqual(len(dados['tickets_ausentes']), dados['ausentes'])
        self.assertEqual(len(dados['passageiros_sem_ticket']), dados['sem_ticket'])
        pcd = next(item for item in dados['tickets_presentes'] if item['nome'] == 'Presente PcD')
        self.assertTrue(pcd['tem_deficiencia'])
        self.assertTrue(pcd['cpf'])
        self.assertEqual(set(pcd), {'id', 'nome', 'cpf', 'tem_deficiencia'})

    def test_embarcado_sem_viagem_nao_entra_e_detalhe_404(self):
        self.execucao.status = StatusExecucaoRota.EMBARCADO
        self.execucao.rota_finalizada_em = None
        self.execucao.save()
        self.assertEqual(self.client.get(self.lista).data['count'], 0)
        self.assertEqual(self.client.get(self.detalhe).status_code, 404)
        self.assertEqual(self.client.get(self.percursos).data['count'], 0)

    def test_l3_acessa_e_perfis_sem_conferir_recebem_403(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.lista).status_code, 200)
        self.assertEqual(self.client.get(self.detalhe).status_code, 200)
        aluno = criar_aluno('74000000004')
        comum = criar_usuario('74000000005')
        motorista = criar_usuario('74000000006', 'Motorista sem conferir')
        Motorista.objects.create(usuario=motorista)
        l2 = criar_usuario('74000000007', 'Servidor L2')
        cargo = Cargo.objects.create(nome='Sem conferir historico')
        Servidor.objects.create(usuario=l2, cargo=cargo, categoria=1, ativo=True)
        for usuario in (aluno.usuario, comum, motorista, l2, None):
            self.client.force_authenticate(usuario)
            for url in (self.lista, self.percursos, self.detalhe):
                with self.subTest(usuario=usuario, url=url):
                    resposta = self.client.get(url)
                    self.assertEqual(resposta.status_code, 401 if usuario is None else 403)
        with self.assertRaises(AuthorizationException):
            ExecucaoRota().business.listar_historico_conferencia(comum)

    def test_id_inexistente_retorna_404(self):
        inexistente = reverse('transporte:execucao-rota-historico-detail', args=[999999999])
        self.assertEqual(self.client.get(inexistente).status_code, 404)
