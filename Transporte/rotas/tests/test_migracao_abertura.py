from datetime import time

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class MigracaoAberturaRotaTestCase(TransactionTestCase):
    def test_preserva_abertura_antiga_em_rotas_e_historicos(self):
        anterior = [('rotas', '0002_initial')]
        destino = [('rotas', '0005_remover_antecedencia_abertura')]
        executor = MigrationExecutor(connection)
        executor.migrate(anterior)
        try:
            apps = executor.loader.project_state(anterior).apps
            percurso = apps.get_model('percursos', 'Percurso').objects.create(
                apelido='Legado', descricao='Migração',
            )
            rota = apps.get_model('rotas', 'Rota').objects.create(
                percurso_id=percurso.pk, horario_saida=time(7), dia_semana='segunda', quantidade_vagas=40,
            )
            historico = apps.get_model('rotas', 'HistoricalRota').objects.create(
                id=rota.pk, percurso_id=percurso.pk, horario_saida=time(7), dia_semana='segunda',
                quantidade_vagas=40, ativo=True, created_at=timezone.now(), updated_at=timezone.now(),
                history_date=timezone.now(), history_type='+',
            )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(destino)
        apps = executor.loader.project_state(destino).apps
        for registro in (
            apps.get_model('rotas', 'Rota').objects.get(pk=rota.pk),
            apps.get_model('rotas', 'HistoricalRota').objects.get(pk=historico.pk),
        ):
            self.assertEqual(registro.horario_abertura_solicitacoes, time(19))
            self.assertEqual(registro.quantidade_vagas, 40)
