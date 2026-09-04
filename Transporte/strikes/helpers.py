from django.db.models import Count, Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import StatusStrike


def sincronizar_faltas_transporte(aluno):
    from .models import Strike

    estava_bloqueado = aluno.is_bloqueado
    faltas = Strike.objects.filter(
        ticket__aluno=aluno,
        status=StatusStrike.ATIVO,
    ).count()
    aluno.faltas = faltas
    aluno.is_bloqueado = faltas >= 3
    if not estava_bloqueado and aluno.is_bloqueado:
        aluno.quantidade_bloqueios += 1
    aluno.save(update_fields=[
        'faltas',
        'is_bloqueado',
        'quantidade_bloqueios',
        'updated_at',
    ])
    return aluno


class StrikeHelpers(ModelInstanceHelpers):

    def _listar_com_relacionamentos(self):
        from .models import Strike

        return Strike.objects.select_related(
            'ticket',
            'ticket__execucao_rota',
            'ticket__execucao_rota__rota',
            'ticket__execucao_rota__rota__percurso',
            'ticket__aluno',
            'ticket__aluno__usuario',
        )

    def listar_para_usuario(self, usuario):
        queryset = self._listar_com_relacionamentos()
        if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            return queryset
        aluno = getattr(usuario, 'aluno', None)
        return queryset.filter(ticket__aluno=aluno) if aluno is not None else queryset.none()

    def aluno_esta_bloqueado(self):
        return self.object_instance.ticket.aluno.is_bloqueado
