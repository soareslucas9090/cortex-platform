from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.conf import settings
from django.utils import timezone
from rest_framework.test import APITestCase

from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.execucoes_rotas.tasks import gerar_execucoes_rotas_automaticas_task
from Transporte.percursos.models import Percurso
from Transporte.rotas.choices import DiaSemana
from Transporte.rotas.models import Rota


class GeracaoAutomaticaExecucoesTestCase(APITestCase):
    data_segunda = date(2026, 8, 3)

    def criar_rota(
        self,
        apelido,
        horario_saida=time(12, 0),
        dia_semana=DiaSemana.SEGUNDA,
        rota_ativa=True,
        percurso_ativo=True,
        vagas=40,
    ):
        percurso = Percurso.objects.create(
            apelido=apelido,
            descricao=f'Percurso {apelido}',
            ativo=percurso_ativo,
        )
        return Rota.objects.create(
            percurso=percurso,
            horario_saida=horario_saida,
            dia_semana=dia_semana,
            quantidade_vagas=vagas,
            ativo=rota_ativa,
        )

    def instante(self, data_execucao, horario):
        return timezone.make_aware(
            datetime.combine(data_execucao, horario),
            timezone.get_current_timezone(),
        )

    def test_gera_rotas_ativas_do_dia_com_snapshot(self):
        rota = self.criar_rota('Centro', horario_saida=time(7, 30), vagas=42)

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(self.data_segunda, time(0, 0)),
        )

        execucao = ExecucaoRota.objects.get(rota=rota, data_execucao=self.data_segunda)
        self.assertEqual(resultado['criadas'], 1)
        self.assertEqual(execucao.status, StatusExecucaoRota.ABERTA)
        self.assertEqual(execucao.quantidade_vagas, 42)
        self.assertEqual(timezone.localtime(execucao.data_hora_saida).time(), time(7, 30))

    def test_ignora_fim_de_semana(self):
        data_sabado = self.data_segunda + timedelta(days=5)
        self.criar_rota('Sábado', dia_semana=DiaSemana.SABADO)

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(data_sabado, time(0, 0)),
        )

        self.assertEqual(resultado['criadas'], 0)
        self.assertFalse(resultado['dia_operacional'])
        self.assertFalse(ExecucaoRota.objects.exists())

    def test_feriado_bloqueia_geracao_em_dia_util(self):
        data_feriado = date(2026, 9, 7)
        self.criar_rota('Feriado', dia_semana=DiaSemana.SEGUNDA)

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(data_feriado, time(0, 0)),
        )

        self.assertEqual(resultado['criadas'], 0)
        self.assertFalse(resultado['dia_operacional'])
        self.assertFalse(ExecucaoRota.objects.exists())

    def test_sabado_letivo_gera_somente_rotas_de_sabado(self):
        data_sabado = date(2026, 9, 5)
        rota_sabado = self.criar_rota(
            'Sábado letivo',
            dia_semana=DiaSemana.SABADO,
        )
        self.criar_rota('Sexta-feira', dia_semana=DiaSemana.SEXTA)

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(data_sabado, time(0, 0)),
        )

        self.assertTrue(resultado['dia_operacional'])
        self.assertEqual(resultado['criadas'], 1)
        self.assertTrue(
            ExecucaoRota.objects.filter(
                rota=rota_sabado,
                data_execucao=data_sabado,
            ).exists(),
        )

    def test_dia_nao_operacional_sinaliza_execucao_manual_existente(self):
        data_feriado = date(2026, 9, 7)
        rota = self.criar_rota('Contingência', dia_semana=DiaSemana.SEGUNDA)
        execucao = ExecucaoRota().business.criar_execucao(rota.pk, data_feriado)

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(data_feriado, time(0, 0)),
        )

        self.assertEqual(
            resultado['conflitos_execucoes_existentes'],
            [execucao.pk],
        )
        execucao.refresh_from_db()
        self.assertEqual(execucao.status, StatusExecucaoRota.ABERTA)

    def test_ignora_rota_inativa_percurso_inativo_e_outro_dia(self):
        self.criar_rota('Rota inativa', rota_ativa=False)
        self.criar_rota('Percurso inativo', percurso_ativo=False)
        self.criar_rota('Terça-feira', dia_semana=DiaSemana.TERCA)

        ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(self.data_segunda, time(0, 0)),
        )

        self.assertFalse(ExecucaoRota.objects.exists())

    def test_limite_exato_t30_gera_execucao(self):
        rota = self.criar_rota('Limite exato', horario_saida=time(8, 0))

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(self.data_segunda, time(7, 30)),
        )

        self.assertEqual(resultado['criadas'], 1)
        self.assertTrue(
            ExecucaoRota.objects.filter(rota=rota, data_execucao=self.data_segunda).exists(),
        )

    def test_depois_de_t30_nao_gera_execucao(self):
        self.criar_rota('Prazo encerrado', horario_saida=time(8, 0))

        resultado = ExecucaoRota().business.gerar_execucoes_automaticas(
            self.instante(self.data_segunda, time(7, 30, 0, 1)),
        )

        self.assertEqual(resultado['fora_do_prazo'], 1)
        self.assertFalse(ExecucaoRota.objects.exists())

    def test_reexecucao_e_execucao_manual_existente_sao_idempotentes(self):
        rota = self.criar_rota('Idempotente')
        instante = self.instante(self.data_segunda, time(0, 0))
        ExecucaoRota().business.criar_execucao(rota.pk, self.data_segunda)

        primeiro = ExecucaoRota().business.gerar_execucoes_automaticas(instante)
        segundo = ExecucaoRota().business.gerar_execucoes_automaticas(instante)

        self.assertEqual(primeiro['existentes'], 1)
        self.assertEqual(segundo['existentes'], 1)
        self.assertEqual(ExecucaoRota.objects.filter(rota=rota).count(), 1)

    def test_edicao_da_rota_nao_altera_snapshot_existente(self):
        rota = self.criar_rota('Snapshot', horario_saida=time(9, 0), vagas=20)
        instante = self.instante(self.data_segunda, time(0, 0))
        ExecucaoRota().business.gerar_execucoes_automaticas(instante)

        rota.horario_saida = time(10, 0)
        rota.quantidade_vagas = 50
        rota.save(update_fields=['horario_saida', 'quantidade_vagas'])
        ExecucaoRota().business.gerar_execucoes_automaticas(instante)

        execucao = ExecucaoRota.objects.get(rota=rota)
        self.assertEqual(execucao.quantidade_vagas, 20)
        self.assertEqual(timezone.localtime(execucao.data_hora_saida).time(), time(9, 0))

    def test_task_delega_geracao_ao_business(self):
        resultado = {
            'data_execucao': self.data_segunda.isoformat(),
            'criadas': 2,
            'existentes': 1,
            'fora_do_prazo': 0,
            'dia_operacional': True,
            'conflitos_execucoes_existentes': [],
        }
        with patch(
            'Transporte.execucoes_rotas.business.ExecucaoRotaBusiness.gerar_execucoes_automaticas',
            return_value=resultado,
        ) as gerar:
            retorno = gerar_execucoes_rotas_automaticas_task()

        gerar.assert_called_once_with()
        self.assertEqual(retorno, resultado)

    def test_agendamento_esta_configurado_para_todos_os_dias(self):
        agendamento = settings.CELERY_BEAT_SCHEDULE[
            'gerar-execucoes-rotas-pelo-calendario'
        ]

        self.assertEqual(
            agendamento['task'],
            'Transporte.execucoes_rotas.tasks.gerar_execucoes_rotas_automaticas_task',
        )
        self.assertEqual(agendamento['schedule'].minute, set(range(0, 60, 5)))
        self.assertEqual(agendamento['schedule'].day_of_week, set(range(7)))
