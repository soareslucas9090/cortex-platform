from AppCore.core.rules.rules import ModelInstanceRules

from .choices import StatusJustificativa


class JustificativaRules(ModelInstanceRules):

    def validar_texto(self, texto) -> bool:
        if not texto or len(texto.strip()) < 10:
            self.return_exception('A justificativa deve possuir pelo menos 10 caracteres.')
        return True

    def validar_pendente(self) -> bool:
        if self.object_instance.status != StatusJustificativa.PENDENTE:
            self.return_exception('Somente uma justificativa pendente pode ser analisada.')
        return True

    def validar_aluno_bloqueado(self, aluno) -> bool:
        if not aluno.is_bloqueado:
            self.return_exception('Somente um aluno bloqueado pode enviar justificativa.')
        return True

    def validar_sem_pendente(self, aluno) -> bool:
        from .models import Justificativa

        if Justificativa.objects.filter(
            aluno=aluno,
            status=StatusJustificativa.PENDENTE,
        ).exists():
            self.return_exception('Já existe uma justificativa pendente de análise.')
        return True
