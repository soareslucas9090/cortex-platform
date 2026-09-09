from AppCore.core.rules.rules import ModelInstanceRules

from .choices import TIPOS_OPERACIONAIS, TipoDiaCalendario


class DiaCalendarioTransporteRules(ModelInstanceRules):

    def permite_operacao_na_data(self, data, tipo_excecao=None) -> bool:
        if tipo_excecao is None:
            return data.weekday() < 5
        return tipo_excecao in TIPOS_OPERACIONAIS

    def validar_dados(self, descricao, tipo) -> bool:
        if not str(descricao).strip():
            self.return_exception('Informe a descrição do dia do calendário.')
        if tipo not in TipoDiaCalendario.values:
            self.return_exception('O tipo informado para o dia do calendário é inválido.')
        return True
