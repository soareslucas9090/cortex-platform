from datetime import date

from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException

from ..choices import TipoDiaCalendario
from ..models import DiaCalendarioTransporte


class CalendarioOperacionalTestCase(APITestCase):

    def test_regra_padrao_permite_dia_util_e_bloqueia_fim_de_semana(self):
        calendario = DiaCalendarioTransporte()

        self.assertTrue(
            calendario.rules.permite_operacao_na_data(date(2026, 8, 3)),
        )
        self.assertFalse(
            calendario.rules.permite_operacao_na_data(date(2026, 8, 8)),
        )

    def test_excecao_letiva_libera_sabado(self):
        calendario = DiaCalendarioTransporte()

        self.assertTrue(
            calendario.rules.permite_operacao_na_data(
                date(2026, 9, 5),
                TipoDiaCalendario.REPOSICAO,
            ),
        )

    def test_feriado_bloqueia_dia_util(self):
        calendario = DiaCalendarioTransporte()

        self.assertFalse(
            calendario.rules.permite_operacao_na_data(
                date(2026, 9, 7),
                TipoDiaCalendario.FERIADO,
            ),
        )

    def test_carga_inicial_contem_excecoes_aprovadas(self):
        self.assertEqual(
            DiaCalendarioTransporte.objects.get(data=date(2026, 9, 5)).tipo,
            TipoDiaCalendario.REPOSICAO,
        )
        self.assertEqual(
            DiaCalendarioTransporte.objects.get(data=date(2026, 10, 28)).tipo,
            TipoDiaCalendario.PONTO_FACULTATIVO,
        )
        self.assertEqual(
            DiaCalendarioTransporte.objects.get(data=date(2027, 1, 31)).tipo,
            TipoDiaCalendario.FERIAS,
        )

    def test_nao_permite_duas_configuracoes_para_mesma_data(self):
        with self.assertRaises(BusinessRuleException):
            DiaCalendarioTransporte().business.criar_dia(
                data=date(2026, 9, 7),
                descricao='Duplicado',
                tipo=TipoDiaCalendario.FERIADO,
            )
