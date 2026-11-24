from datetime import date

from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules

from .constantes import INTERVALO_MAXIMO_DIAS, LIMITE_EMPRESTIMOS_RELATORIO


class RelatorioEmprestimosRules(ModelInstanceRules):

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
        return True

    def validar_quantidade(self, total: int):
        if total > LIMITE_EMPRESTIMOS_RELATORIO:
            self.return_exception(
                f'O relatório encontrou {total} empréstimos, acima do limite de '
                f'{LIMITE_EMPRESTIMOS_RELATORIO}. Refine os filtros para reduzir o volume.',
                type_exception=ValidationException,
            )
        return True

    def validar_sala_no_bloco(self, pertence: bool):
        if not pertence:
            self.return_exception(
                'A sala informada não pertence ao bloco selecionado.',
                type_exception=ValidationException,
            )
        return True