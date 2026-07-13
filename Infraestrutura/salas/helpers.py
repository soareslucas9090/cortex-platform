from AppCore.core.helpers.helpers import ModelInstanceHelpers


class SalaHelpers(ModelInstanceHelpers):

    def listar_ativas(self):
        """Retorna todas as salas ativas."""
        from .models import Sala
        return Sala.objects.filter(ativo=True)

    def listar_inativas(self):
        """Retorna todas as salas inativas."""
        from .models import Sala
        return Sala.objects.filter(ativo=False)


class SalaSetorHelpers(ModelInstanceHelpers):

    def listar_por_sala(self, sala_id):
        """Retorna vínculos sala–setor de uma sala."""
        from .models import SalaSetor
        return SalaSetor.objects.filter(sala_id=sala_id)

    def listar_por_setor(self, setor_id):
        """Retorna vínculos sala–setor de um setor."""
        from .models import SalaSetor
        return SalaSetor.objects.filter(setor_id=setor_id)
