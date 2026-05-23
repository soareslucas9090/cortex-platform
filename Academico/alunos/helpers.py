from AppCore.core.helpers.helpers import ModelInstanceHelpers


class AlunoHelpers(ModelInstanceHelpers):
    
    def obter_por_cpf(self, cpf):
        from .models import Aluno
        return Aluno.objects.filter(usuario__cpf=cpf).first()
