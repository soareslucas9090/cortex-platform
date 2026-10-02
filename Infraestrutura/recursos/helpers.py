from django.apps import apps
from django.db.models import Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import EstadoRecurso


class RecursoHelpers(ModelInstanceHelpers):

    def listar_com_filtros(
        self,
        *,
        ativo=None,
        codigo=None,
        busca=None,
        tipo=None,
        sala_id=None,
    ):
        """Lista recursos aplicando filtros opcionais sobre o catálogo autenticado."""
        from .models import Recurso

        qs = Recurso.objects.select_related('sala', 'sala__bloco').all()
        if ativo is not None:
            qs = qs.filter(ativo=ativo)
        if codigo:
            qs = qs.filter(codigo__unaccent__icontains=codigo)
        if busca:
            qs = qs.filter(
                Q(codigo__unaccent__icontains=busca)
                | Q(sala__nome__unaccent__icontains=busca)
                | Q(sala__bloco__nome__unaccent__icontains=busca),
            )
        if tipo:
            qs = qs.filter(tipo=tipo)
        if sala_id is not None:
            qs = qs.filter(sala_id=sala_id)
        return qs

    def obter_estado_derivado(self) -> str:
        """
        Prioridade: avaria → emprestado → reservado → disponível.
        Reservado permanece falso na v1 (sem app de reservas).
        """
        recurso = self.object_instance
        if recurso.em_avaria:
            return EstadoRecurso.AVARIA
        if self.esta_emprestado(recurso):
            return EstadoRecurso.EMPRESTADO
        if self.esta_reservado(recurso):
            return EstadoRecurso.RESERVADO
        return EstadoRecurso.DISPONIVEL

    def esta_emprestado(self, recurso) -> bool:
        """Verifica empréstimo aberto; integra com app emprestimos quando existir."""
        try:
            ItemEmprestimo = apps.get_model('emprestimos', 'ItemEmprestimo')
        except LookupError:
            return False
        return ItemEmprestimo.objects.filter(
            recurso=recurso,
            devolvido_em__isnull=True,
        ).exists()

    def esta_reservado(self, recurso) -> bool:
        """Reservas não implementadas na v1."""
        return False

    def listar_ativos(self):
        """Retorna todos os recursos ativos."""
        from .models import Recurso
        return Recurso.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os recursos inativos."""
        from .models import Recurso
        return Recurso.objects.filter(ativo=False)

    def listar_por_tipo(self, tipo: str):
        """Retorna recursos ativos de um tipo."""
        from .models import Recurso
        return Recurso.objects.filter(ativo=True, tipo=tipo)

    def listar_por_sala(self, sala_id: int):
        """Retorna recursos ativos vinculados a uma sala."""
        from .models import Recurso
        return Recurso.objects.filter(ativo=True, sala_id=sala_id)

    def obter_por_pk_com_sala(self, pk: int):
        """Retorna o recurso com sala pré-carregada para serialização."""
        from .models import Recurso
        return Recurso.objects.select_related('sala', 'sala__bloco').get(pk=pk)
