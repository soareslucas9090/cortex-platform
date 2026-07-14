from datetime import date

from django.db.models import Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class AutorizacaoHelpers(ModelInstanceHelpers):

    def esta_vigente(self, data_referencia: date | None = None) -> bool:
        """Autorização não revogada e dentro do período configurado."""
        autorizacao = self.object_instance
        if autorizacao.revogado_em is not None:
            return False
        referencia = data_referencia or date.today()
        if autorizacao.data_inicio > referencia:
            return False
        if autorizacao.data_fim is not None and autorizacao.data_fim < referencia:
            return False
        return True

    def usuario_tem_autorizacao_vigente_para_recurso(
        self,
        usuario,
        recurso,
        data_referencia: date | None = None,
    ) -> bool:
        """
        Verifica autorização direta no recurso ou por sala.
        Autorização por sala cobre recursos futuros da mesma sala (avaliação em runtime).
        """
        from .models import Autorizacao

        referencia = data_referencia or date.today()
        filtro_vigencia = Q(revogado_em__isnull=True, data_inicio__lte=referencia) & (
            Q(data_fim__isnull=True) | Q(data_fim__gte=referencia)
        )
        filtro_alvo = Q(recurso=recurso)
        if recurso.sala_id:
            filtro_alvo |= Q(sala_id=recurso.sala_id)

        return Autorizacao.objects.filter(
            filtro_vigencia,
            beneficiario=usuario,
        ).filter(filtro_alvo).exists()

    def listar_para_filtros(
        self,
        beneficiario_id=None,
        sala_id=None,
        recurso_id=None,
        vigente=None,
        data_referencia: date | None = None,
    ):
        """Lista autorizações com filtros opcionais de beneficiário, alvo e vigência."""
        from .models import Autorizacao

        qs = Autorizacao.objects.select_related(
            'beneficiario',
            'concedente',
            'sala',
            'recurso',
            'revogador',
        ).all()

        if beneficiario_id is not None:
            qs = qs.filter(beneficiario_id=beneficiario_id)
        if sala_id is not None:
            qs = qs.filter(sala_id=sala_id)
        if recurso_id is not None:
            qs = qs.filter(recurso_id=recurso_id)
        if vigente is not None:
            referencia = data_referencia or date.today()
            filtro_vigencia = Q(revogado_em__isnull=True, data_inicio__lte=referencia) & (
                Q(data_fim__isnull=True) | Q(data_fim__gte=referencia)
            )
            qs = qs.filter(filtro_vigencia) if vigente else qs.exclude(filtro_vigencia)
        return qs
