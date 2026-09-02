from AppCore.core.rules.rules import ModelInstanceRules

from .choices import StatusStrike


class StrikeRules(ModelInstanceRules):

    def validar_dono(self, usuario) -> bool:
        if self.object_instance.ticket.aluno.usuario != usuario:
            self.return_not_allowed('Você não pode justificar o strike de outro aluno.')
        return True

    def validar_ativo(self) -> bool:
        if self.object_instance.status != StatusStrike.ATIVO:
            self.return_exception('Somente um strike ativo pode receber justificativa.')
        return True
