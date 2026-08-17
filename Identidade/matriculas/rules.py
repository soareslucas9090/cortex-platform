from AppCore.core.rules.rules import ModelInstanceRules


class MatriculaRules(ModelInstanceRules):
    """
    Regras de negócio do domínio Matrículas.
    O object_instance é o Usuario dono das matrículas.
    Chamada exclusivamente pela camada Business.
    """

    def matricula_nao_duplicada(self, numero_matricula: str, excluir_id=None) -> bool:
        """Valida que o número de matrícula não está duplicado globalmente."""
        from .models import Matricula
        qs = Matricula.objects.filter(matricula=numero_matricula)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um usuário cadastrado com esta matrícula.')
        return True
