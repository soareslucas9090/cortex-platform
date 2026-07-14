from datetime import date, timedelta

from django.apps import apps
from django.conf import settings
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from Infraestrutura.permissoes.access import usuario_pode_operar_infraestrutura
from Infraestrutura.recursos.choices import TipoRecurso

from .choices import CARGO_SERVENTE_LIMPEZA, HORAS_ALERTA_ATRASO


class EmprestimoHelpers(ModelInstanceHelpers):

    def esta_ativo(self) -> bool:
        """Verifica se o empréstimo possui itens em aberto."""
        emprestimo = self.object_instance
        if emprestimo.pk is None:
            return False
        return emprestimo.itens.filter(devolvido_em__isnull=True).exists()

    def esta_atrasado(self) -> bool:
        """Empréstimo ativo retirado há mais de 24 horas."""
        emprestimo = self.object_instance
        if not self.esta_ativo():
            return False
        limite = timezone.now() - timedelta(hours=HORAS_ALERTA_ATRASO)
        return emprestimo.retirada_em < limite

    def solicitante_pode_retirar_recurso(self, solicitante, recurso) -> bool:
        """
        Elegibilidade do solicitante:
        retirada_irrestrita → servente limpeza (chave) → SalaSetor (chave) → autorização.
        """
        if self._solicitante_tem_retirada_irrestrita(solicitante):
            return True
        if recurso.tipo == TipoRecurso.CHAVE and self._usuario_e_servente_limpeza(solicitante):
            return True
        if recurso.tipo == TipoRecurso.CHAVE and self._usuario_tem_vinculo_setor_na_sala(
            solicitante,
            recurso.sala_id,
        ):
            return True
        return self._usuario_tem_autorizacao_vigente(solicitante, recurso)

    def recurso_esta_emprestado(self, recurso) -> bool:
        from .models import ItemEmprestimo

        return ItemEmprestimo.objects.filter(
            recurso=recurso,
            devolvido_em__isnull=True,
        ).exists()

    def listar_solicitantes_elegiveis_para_recurso(
        self,
        recurso,
        *,
        nome=None,
        ativo=True,
    ):
        """
        Retorna usuários ativos elegíveis a retirar o recurso informado.
        Espelha as regras de solicitante_pode_retirar_recurso em nível de queryset.
        """
        from Identidade.usuarios.models import Usuario

        referencia = date.today()
        elegiveis = Q(is_superuser=True) | Q(is_admin=True)
        elegiveis |= Q(
            setor_vinculos__setor__ativo=True,
            setor_vinculos__funcao__isnull=False,
            setor_vinculos__funcao__ativo=True,
            setor_vinculos__funcao__permissao_infraestrutura__retirada_irrestrita=True,
        )

        if recurso.tipo == TipoRecurso.CHAVE:
            elegiveis |= Q(
                terceirizado__ativo=True,
                terceirizado__cargo__ativo=True,
                terceirizado__cargo__nome__iexact=CARGO_SERVENTE_LIMPEZA,
            )
            if recurso.sala_id:
                elegiveis |= Q(
                    setor_vinculos__setor__ativo=True,
                    setor_vinculos__setor__salas_vinculadas__sala_id=recurso.sala_id,
                )

        filtro_vigencia = Q(
            autorizacoes_infraestrutura__revogado_em__isnull=True,
            autorizacoes_infraestrutura__data_inicio__lte=referencia,
        ) & (
            Q(autorizacoes_infraestrutura__data_fim__isnull=True)
            | Q(autorizacoes_infraestrutura__data_fim__gte=referencia)
        )
        elegiveis |= Q(
            autorizacoes_infraestrutura__recurso_id=recurso.pk,
        ) & filtro_vigencia
        if recurso.sala_id:
            elegiveis |= Q(
                autorizacoes_infraestrutura__sala_id=recurso.sala_id,
            ) & filtro_vigencia

        qs = Usuario.objects.filter(elegiveis)
        if ativo is not None:
            qs = qs.filter(ativo=ativo)
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        return qs.distinct().order_by('nome')

    def listar_solicitantes_elegiveis_para_recursos(
        self,
        recursos,
        *,
        nome=None,
        ativo=True,
    ):
        """
        Retorna usuários elegíveis a retirar todos os recursos informados (interseção).
        """
        from Identidade.usuarios.models import Usuario

        if not recursos:
            return Usuario.objects.none()

        qs = None
        for recurso in recursos:
            qs_recurso = self.listar_solicitantes_elegiveis_para_recurso(recurso, ativo=ativo)
            qs = qs_recurso if qs is None else qs.filter(pk__in=qs_recurso.values('pk'))

        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        return qs.distinct().order_by('nome')

    def listar_para_usuario(
        self,
        usuario,
        *,
        ativo=None,
        solicitante_id=None,
        responsavel_id=None,
        recurso_id=None,
        tipo_recurso=None,
    ):
        """L2 (`operar`): consulta ampla. L1: apenas empréstimos ativos próprios."""
        from .models import Emprestimo, ItemEmprestimo

        qs = Emprestimo.objects.select_related(
            'solicitante',
            'responsavel',
        ).prefetch_related(
            'itens__recurso__sala',
        )

        if usuario_pode_operar_infraestrutura(usuario):
            if solicitante_id is not None:
                qs = qs.filter(solicitante_id=solicitante_id)
            if responsavel_id is not None:
                qs = qs.filter(responsavel_id=responsavel_id)
            if ativo is not None:
                qs = self._filtrar_por_ativo(qs, ativo)
        else:
            qs = qs.filter(solicitante=usuario)
            qs = self._filtrar_por_ativo(qs, True)

        if recurso_id is not None:
            qs = qs.filter(itens__recurso_id=recurso_id).distinct()
        if tipo_recurso is not None:
            qs = qs.filter(itens__recurso__tipo=tipo_recurso).distinct()

        return qs

    def usuario_pode_consultar_emprestimo(self, usuario, emprestimo) -> bool:
        """Operador consulta qualquer; L1 apenas empréstimos ativos próprios."""
        if usuario_pode_operar_infraestrutura(usuario):
            return True
        if emprestimo.solicitante_id != usuario.pk:
            return False
        return self._esta_ativo_por_pk(emprestimo.pk)

    def _filtrar_por_ativo(self, qs, ativo: bool):
        from .models import ItemEmprestimo

        itens_abertos = ItemEmprestimo.objects.filter(
            emprestimo_id=OuterRef('pk'),
            devolvido_em__isnull=True,
        )
        if ativo:
            return qs.filter(Exists(itens_abertos))
        return qs.exclude(Exists(itens_abertos))

    def _esta_ativo_por_pk(self, emprestimo_id: int) -> bool:
        from .models import ItemEmprestimo

        return ItemEmprestimo.objects.filter(
            emprestimo_id=emprestimo_id,
            devolvido_em__isnull=True,
        ).exists()

    def _solicitante_tem_retirada_irrestrita(self, solicitante) -> bool:
        infraestrutura = getattr(solicitante, 'permissoes', {}).get('infraestrutura', {})
        return bool(infraestrutura.get('retirada_irrestrita'))

    def _usuario_e_servente_limpeza(self, usuario) -> bool:
        try:
            Terceirizado = apps.get_model('terceirizados', 'Terceirizado')
        except LookupError:
            return False
        return Terceirizado.objects.filter(
            usuario=usuario,
            ativo=True,
            cargo__ativo=True,
            cargo__nome__iexact=CARGO_SERVENTE_LIMPEZA,
        ).exists()

    def _usuario_tem_vinculo_setor_na_sala(self, usuario, sala_id) -> bool:
        if not sala_id:
            return False
        try:
            SalaSetor = apps.get_model('salas', 'SalaSetor')
            SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
        except LookupError:
            return False
        setor_ids = SalaSetor.objects.filter(sala_id=sala_id).values_list('setor_id', flat=True)
        return SetorVinculo.objects.filter(
            usuario=usuario,
            setor_id__in=setor_ids,
            setor__ativo=True,
        ).exists()

    def _usuario_tem_autorizacao_vigente(self, solicitante, recurso) -> bool:
        try:
            Autorizacao = apps.get_model('autorizacoes', 'Autorizacao')
        except LookupError:
            return False
        return Autorizacao().helper.usuario_tem_autorizacao_vigente_para_recurso(solicitante, recurso)
