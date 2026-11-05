from datetime import datetime

from django.db.models import CharField, Count, DateTimeField, IntegerField, OuterRef, Q, Subquery
from django.utils import timezone

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class EventoAcessoHelpers(ModelInstanceHelpers):

    def listar_representantes(self):
        from .models import EventoAcesso

        eventos_grupo = EventoAcesso.objects.filter(grupo_portaria_id=OuterRef('grupo_portaria_id'))
        agora = timezone.localtime()
        data_atual = agora.date()
        hora_atual = agora.time().replace(tzinfo=None)
        primeiro_id = eventos_grupo.order_by('id').values('id')[:1]
        totais = eventos_grupo.values('grupo_portaria_id').annotate(total=Count('id')).values('total')[:1]
        registrados = (
            eventos_grupo.filter(registro__isnull=False)
            .values('grupo_portaria_id')
            .annotate(total=Count('id'))
            .values('total')[:1]
        )
        expirados = (
            eventos_grupo.filter(registro__isnull=True)
            .filter(
                Q(expirado_em__isnull=False)
                | Q(data_acesso__lt=data_atual)
                | Q(data_acesso=data_atual, hora_prevista__lt=hora_atual)
            )
            .values('grupo_portaria_id')
            .annotate(total=Count('id'))
            .values('total')[:1]
        )
        ultimo_registro = eventos_grupo.filter(registro__isnull=False).order_by('-registro__registrado_em')
        ultima_expiracao = eventos_grupo.filter(expirado_em__isnull=False).order_by('-expirado_em')
        return (
            EventoAcesso.objects.filter(id=Subquery(primeiro_id))
            .select_related('solicitacao__avaliada_por', 'aluno__usuario', 'tipo')
            .annotate(
                total_eventos=Subquery(totais, output_field=IntegerField()),
                total_registrados=Subquery(registrados, output_field=IntegerField()),
                total_expirados=Subquery(expirados, output_field=IntegerField()),
                ultimo_registro_em=Subquery(
                    ultimo_registro.values('registro__registrado_em')[:1],
                    output_field=DateTimeField(),
                ),
                ultimo_registrado_por_id=Subquery(
                    ultimo_registro.values('registro__registrado_por_id')[:1],
                    output_field=IntegerField(),
                ),
                ultimo_registrado_por_nome=Subquery(
                    ultimo_registro.values('registro__registrado_por__nome')[:1],
                    output_field=CharField(),
                ),
                ultima_expiracao_em=Subquery(
                    ultima_expiracao.values('expirado_em')[:1],
                    output_field=DateTimeField(),
                ),
            )
        )

    def eventos_do_grupo(self, grupo_portaria_id, bloquear=False):
        from .models import EventoAcesso

        qs = EventoAcesso.objects.filter(grupo_portaria_id=grupo_portaria_id).select_related(
            'solicitacao__avaliada_por', 'aluno__usuario', 'tipo', 'registro__registrado_por', 'registro__operado_por'
        )
        if bloquear:
            qs = qs.select_for_update(of=('self',))
        return qs.order_by('aluno_nome', 'id')

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
