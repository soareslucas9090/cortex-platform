from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules

from .choices import CANAIS_DISPONIVEIS


class NotificacaoRules(ModelInstanceRules):

    def validar_disparo(self, destinatario_id, tipo, titulo, corpo, canais) -> bool:
        if not destinatario_id:
            self.return_exception(
                'Informe o destinatário da notificação.',
                type_exception=ValidationException,
            )
        if not (tipo or '').strip():
            self.return_exception(
                'Informe o tipo da notificação.',
                type_exception=ValidationException,
            )
        if not (titulo or '').strip():
            self.return_exception(
                'Informe o título da notificação.',
                type_exception=ValidationException,
            )
        if not (corpo or '').strip():
            self.return_exception(
                'Informe o corpo da notificação.',
                type_exception=ValidationException,
            )
        if canais is None or not hasattr(canais, '__iter__'):
            self.return_exception(
                'Informe ao menos um canal de envio.',
                type_exception=ValidationException,
            )
        canais_lista = list(canais)
        if not canais_lista:
            self.return_exception(
                'Informe ao menos um canal de envio.',
                type_exception=ValidationException,
            )
        for canal in canais_lista:
            if canal not in CANAIS_DISPONIVEIS:
                self.return_exception(
                    f'Canal de envio inválido: {canal}.',
                    type_exception=ValidationException,
                )
        return True
