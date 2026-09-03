from datetime import date, timedelta

from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules

INTERVALO_MAXIMO_DIAS = 366


class RelatorioAlunosRules(ModelInstanceRules):

    def validar_periodo(self, data_inicio: date, data_fim: date):
        if data_inicio > data_fim:
            self.return_exception(
                'A data de início deve ser anterior ou igual à data de fim.',
                type_exception=ValidationException,
            )
        if (data_fim - data_inicio).days > INTERVALO_MAXIMO_DIAS:
            self.return_exception(
                f'O intervalo máximo permitido é de {INTERVALO_MAXIMO_DIAS} dias.',
                type_exception=ValidationException,
            )

    def validar_categoria(self, categoria: str):
        from .choices import CategoriaRelatorioAluno

        valores = {item.value for item in CategoriaRelatorioAluno}
        if categoria not in valores:
            self.return_exception(
                'Categoria inválida. Use: presentes, ausencias, bloqueios ou sem_ticket.',
                type_exception=ValidationException,
            )
