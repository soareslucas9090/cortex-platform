from datetime import datetime

from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.utils import timezone

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class EventoAcessoHelpers(ModelInstanceHelpers):

    def listar_representantes(self):
        from .models import EventoAcesso

        eventos_grupo = EventoAcesso.objects.filter(grupo_portaria_id=OuterRef("grupo_portaria_id"))
        primeiro_id = eventos_grupo.order_by("id").values("id")[:1]
        totais = eventos_grupo.values("grupo_portaria_id").annotate(total=Count("id")).values("total")[:1]
        registrados = (
            eventos_grupo.filter(registro__isnull=False)
            .values("grupo_portaria_id")
            .annotate(total=Count("id"))
            .values("total")[:1]
        )
        expirados = (
            eventos_grupo.filter(expirado_em__isnull=False)
            .values("grupo_portaria_id")
            .annotate(total=Count("id"))
            .values("total")[:1]
        )
        return (
            EventoAcesso.objects.filter(id=Subquery(primeiro_id))
            .select_related("solicitacao__avaliada_por", "aluno__usuario")
            .annotate(
                total_eventos=Subquery(totais, output_field=IntegerField()),
                total_registrados=Subquery(registrados, output_field=IntegerField()),
                total_expirados=Subquery(expirados, output_field=IntegerField()),
            )
        )

    def eventos_do_grupo(self, grupo_portaria_id, bloquear=False):
        from .models import EventoAcesso

        qs = EventoAcesso.objects.filter(grupo_portaria_id=grupo_portaria_id).select_related(
            "solicitacao__avaliada_por", "aluno__usuario", "registro__registrado_por", "registro__operado_por"
        )
        if bloquear:
            qs = qs.select_for_update(of=('self',))
        return qs.order_by("aluno_nome", "id")

    def instante_inicio(self, data_acesso, hora_prevista):
        return timezone.make_aware(datetime.combine(data_acesso, hora_prevista))

    def instante_expiracao(self, data_acesso, hora_prevista):
        return self.instante_inicio(data_acesso, hora_prevista)

    def horario_disponivel(self, data_acesso, hora_prevista, agora=None):
        agora = agora or timezone.localtime()
        return agora <= self.instante_expiracao(data_acesso, hora_prevista)

    def horario_expirado(self, data_acesso, hora_prevista, agora=None):
        agora = agora or timezone.localtime()
        return agora > self.instante_expiracao(data_acesso, hora_prevista)
