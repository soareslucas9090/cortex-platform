from datetime import date, timedelta

from django.apps import apps
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.utils import timezone

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from Infraestrutura.permissoes.access import usuario_pode_operar_infraestrutura, usuario_tem_acesso_total_infraestrutura
from Infraestrutura.recursos.choices import TipoRecurso

from .choices import HORAS_ALERTA_ATRASO, OrigemContaColetiva


class EmprestimoHelpers(ModelInstanceHelpers):

    def extrair_ids_recursos(self, *grupos_valores) -> list[int]:
        ids: list[int] = []
        for valores in grupos_valores:
            for valor in valores:
                for parte in str(valor).split(','):
                    parte = parte.strip()
                    if parte.isdigit():
                        ids.append(int(parte))
        return list(dict.fromkeys(ids))

    def recursos_pertencem_a_emprestimo_aberto_do_usuario(self, usuario, recurso_ids: list[int]) -> bool:
        from .models import ItemEmprestimo

        if not recurso_ids:
            return False
        quantidade_recursos = len(set(recurso_ids))
        return (
            ItemEmprestimo.objects.filter(
                emprestimo__solicitante=usuario, devolvido_em__isnull=True, recurso_id__in=recurso_ids
            )
            .values('emprestimo_id')
            .annotate(quantidade=Count('recurso_id', distinct=True))
            .filter(quantidade=quantidade_recursos)
            .exists()
        )

    def listar_detalhados(self, usuario=None):
        from .models import Emprestimo, ItemEmprestimo

        itens_abertos = ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('pk'), devolvido_em__isnull=True)
        qs = (
            Emprestimo.objects.select_related('solicitante', 'responsavel')
            .prefetch_related('itens__recurso__sala__bloco')
            .annotate(_aberto=Exists(itens_abertos))
        )
        if usuario is not None:
            qs = qs.prefetch_related(
                Prefetch(
                    'solicitacoes_troca_titular',
                    queryset=self._listar_solicitacoes_pendentes_relacionadas(usuario),
                    to_attr='_solicitacoes_troca_usuario',
                )
            )
        return qs

    def obter_detalhado(self, emprestimo_id: int):
        return self.listar_detalhados().get(pk=emprestimo_id)

    def esta_ativo(self) -> bool:
        """Verifica se o empréstimo possui itens em aberto."""
        emprestimo = self.object_instance
        if emprestimo.pk is None:
            return False
        if hasattr(emprestimo, '_aberto'):
            return emprestimo._aberto
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
        retirada_irrestrita → servidor (qualquer) → terceirizado/SalaSetor (chave) → autorização.
        """
        if self._solicitante_tem_retirada_irrestrita(solicitante):
            return True
        if self._usuario_e_servidor_ativo(solicitante):
            return True
        if recurso.tipo == TipoRecurso.CHAVE:
            if self._usuario_e_terceirizado_ativo(solicitante):
                return True
            if self._usuario_tem_vinculo_setor_na_sala(solicitante, recurso.sala_id):
                return True
        return self._usuario_tem_autorizacao_vigente(solicitante, recurso)

    def recurso_esta_emprestado(self, recurso) -> bool:
        from .models import ItemEmprestimo

        return ItemEmprestimo.objects.filter(recurso=recurso, devolvido_em__isnull=True).exists()

    def listar_solicitantes_elegiveis_para_recurso(self, recurso, *, nome=None, ativo=True):
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
        elegiveis |= Q(permissao_infraestrutura__retirada_irrestrita=True)
        elegiveis |= Q(servidor__ativo=True)

        if recurso.tipo == TipoRecurso.CHAVE:
            elegiveis |= Q(terceirizado__ativo=True)
            if recurso.sala_id:
                elegiveis |= Q(
                    setor_vinculos__setor__ativo=True, setor_vinculos__setor__salas_vinculadas__sala_id=recurso.sala_id
                )

        filtro_vigencia = Q(
            autorizacoes_infraestrutura__revogado_em__isnull=True,
            autorizacoes_infraestrutura__data_inicio__lte=referencia,
        ) & (
            Q(autorizacoes_infraestrutura__data_fim__isnull=True)
            | Q(autorizacoes_infraestrutura__data_fim__gte=referencia)
        )
        elegiveis |= Q(autorizacoes_infraestrutura__recurso_id=recurso.pk) & filtro_vigencia
        if recurso.sala_id:
            elegiveis |= Q(autorizacoes_infraestrutura__sala_id=recurso.sala_id) & filtro_vigencia

        qs = Usuario.objects.filter(elegiveis, usuario_coletivo=False)
        if ativo is not None:
            qs = qs.filter(ativo=ativo)
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        return qs.distinct().order_by('nome')

    def listar_solicitantes_elegiveis_para_recursos(self, recursos, *, nome=None, ativo=True):
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
        atrasado=None,
    ):
        """L2 (`operar`): consulta ampla. L1: próprios e pendências recebidas."""
        from .choices import StatusSolicitacaoTrocaTitular
        from .models import Emprestimo, ItemEmprestimo, SolicitacaoTrocaTitular

        solicitacoes_usuario = self._listar_solicitacoes_pendentes_relacionadas(usuario)
        solicitacoes_pendentes = SolicitacaoTrocaTitular.objects.filter(
            emprestimo_id=OuterRef('pk'), status=StatusSolicitacaoTrocaTitular.PENDENTE
        )
        solicitacoes_pendentes_relacionadas = solicitacoes_pendentes.filter(
            Q(solicitante=usuario) | Q(destinatario=usuario)
        )
        solicitacoes_pendentes_recebidas = solicitacoes_pendentes.filter(destinatario=usuario)

        qs = (
            Emprestimo.objects.select_related('solicitante', 'responsavel')
            .prefetch_related(
                'itens__recurso__sala__bloco',
                Prefetch(
                    'solicitacoes_troca_titular', queryset=solicitacoes_usuario, to_attr='_solicitacoes_troca_usuario'
                ),
            )
            .annotate(
                _solicitacao_pendente_relacionada=Exists(solicitacoes_pendentes_relacionadas),
                _solicitacao_pendente_recebida=Exists(solicitacoes_pendentes_recebidas),
            )
        )

        if usuario_pode_operar_infraestrutura(usuario):
            qs = self.restringir_por_origem_conta_coletiva(qs, usuario)
            if solicitante_id is not None:
                qs = qs.filter(solicitante_id=solicitante_id)
            if responsavel_id is not None:
                qs = qs.filter(responsavel_id=responsavel_id)
            if ativo is not None:
                qs = self._filtrar_por_ativo(qs, ativo)
        else:
            qs = qs.filter(Q(solicitante=usuario) | Q(_solicitacao_pendente_recebida=True))
            if ativo is not None:
                qs = self._filtrar_por_ativo(qs, ativo)

        if recurso_id is not None:
            qs = qs.filter(itens__recurso_id=recurso_id).distinct()
        if tipo_recurso is not None:
            qs = qs.filter(itens__recurso__tipo=tipo_recurso).distinct()
        if atrasado is not None:
            qs = self._filtrar_por_atrasado(qs, atrasado)

        # Pendências relacionadas primeiro; depois abertos e mais recentes.
        itens_abertos = ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('pk'), devolvido_em__isnull=True)
        return qs.annotate(_aberto=Exists(itens_abertos)).order_by(
            '-_solicitacao_pendente_relacionada', '-_aberto', '-retirada_em', 'pk'
        )

    def usuario_pode_consultar_emprestimo(self, usuario, emprestimo) -> bool:
        """Operador consulta conforme seu escopo; L1 consulta próprios e pendências recebidas."""
        from .choices import StatusSolicitacaoTrocaTitular
        from .models import SolicitacaoTrocaTitular

        if usuario_tem_acesso_total_infraestrutura(usuario):
            return True
        if usuario_pode_operar_infraestrutura(usuario):
            if usuario.usuario_coletivo:
                tipo = usuario.tipo_conta_coletiva
                return tipo in OrigemContaColetiva.values and emprestimo.origem_conta_coletiva == tipo
            return True
        if emprestimo.solicitante_id == usuario.pk:
            return True
        return SolicitacaoTrocaTitular.objects.filter(
            emprestimo=emprestimo, destinatario=usuario, status=StatusSolicitacaoTrocaTitular.PENDENTE
        ).exists()

    def _listar_solicitacoes_pendentes_relacionadas(self, usuario):
        from .choices import StatusSolicitacaoTrocaTitular
        from .models import ItemEmprestimo, SolicitacaoTrocaTitular

        return (
            SolicitacaoTrocaTitular.objects.filter(status=StatusSolicitacaoTrocaTitular.PENDENTE)
            .filter(Q(solicitante=usuario) | Q(destinatario=usuario))
            .select_related('solicitante', 'destinatario')
            .annotate(
                _emprestimo_aberto=Exists(
                    ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('emprestimo_id'), devolvido_em__isnull=True)
                )
            )
        )

    def restringir_por_origem_conta_coletiva(self, qs, usuario):
        """Restringe contas coletivas sem afetar administradores ou contas comuns."""
        if usuario_tem_acesso_total_infraestrutura(usuario):
            return qs
        if not usuario.usuario_coletivo:
            return qs
        tipo = usuario.tipo_conta_coletiva
        if tipo not in OrigemContaColetiva.values:
            return qs.none()
        return qs.filter(origem_conta_coletiva=tipo)

    def _filtrar_por_ativo(self, qs, ativo: bool):
        from .models import ItemEmprestimo

        itens_abertos = ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('pk'), devolvido_em__isnull=True)
        if ativo:
            return qs.filter(Exists(itens_abertos))
        return qs.exclude(Exists(itens_abertos))

    def _filtrar_por_atrasado(self, qs, atrasado: bool):
        """Filtra pela mesma condição usada na propriedade calculada ``atrasado``."""
        from .models import ItemEmprestimo

        limite = timezone.now() - timedelta(hours=HORAS_ALERTA_ATRASO)
        itens_abertos = ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('pk'), devolvido_em__isnull=True)
        if atrasado:
            return qs.filter(Exists(itens_abertos), retirada_em__lt=limite)
        return qs.exclude(Exists(itens_abertos), retirada_em__lt=limite)

    def _esta_ativo_por_pk(self, emprestimo_id: int) -> bool:
        from .models import ItemEmprestimo

        return ItemEmprestimo.objects.filter(emprestimo_id=emprestimo_id, devolvido_em__isnull=True).exists()

    def _solicitante_tem_retirada_irrestrita(self, solicitante) -> bool:
        infraestrutura = getattr(solicitante, 'permissoes', {}).get('infraestrutura', {})
        return bool(infraestrutura.get('retirada_irrestrita'))

    def _usuario_e_servidor_ativo(self, usuario) -> bool:
        try:
            Servidor = apps.get_model('servidores', 'Servidor')
        except LookupError:
            return False
        return Servidor.objects.filter(usuario=usuario, ativo=True).exists()

    def _usuario_e_terceirizado_ativo(self, usuario) -> bool:
        try:
            Terceirizado = apps.get_model('terceirizados', 'Terceirizado')
        except LookupError:
            return False
        return Terceirizado.objects.filter(usuario=usuario, ativo=True).exists()

    def _usuario_tem_vinculo_setor_na_sala(self, usuario, sala_id) -> bool:
        if not sala_id:
            return False
        try:
            SalaSetor = apps.get_model('salas', 'SalaSetor')
            SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
        except LookupError:
            return False
        setor_ids = SalaSetor.objects.filter(sala_id=sala_id).values_list('setor_id', flat=True)
        return SetorVinculo.objects.filter(usuario=usuario, setor_id__in=setor_ids, setor__ativo=True).exists()

    def _usuario_tem_autorizacao_vigente(self, solicitante, recurso) -> bool:
        try:
            Autorizacao = apps.get_model('autorizacoes', 'Autorizacao')
        except LookupError:
            return False
        return Autorizacao().helper.usuario_tem_autorizacao_vigente_para_recurso(solicitante, recurso)


class SolicitacaoTrocaTitularHelpers(ModelInstanceHelpers):

    def listar_para_usuario(self, usuario, *, status=None, direcao=None, emprestimo_id=None):
        from .choices import StatusSolicitacaoTrocaTitular
        from .models import ItemEmprestimo, SolicitacaoTrocaTitular

        if not getattr(usuario, 'is_authenticated', False):
            return SolicitacaoTrocaTitular.objects.none()

        qs = (
            SolicitacaoTrocaTitular.objects.filter(Q(solicitante=usuario) | Q(destinatario=usuario))
            .select_related(
                'solicitante', 'destinatario', 'novo_emprestimo', 'emprestimo__solicitante', 'emprestimo__responsavel'
            )
            .prefetch_related('emprestimo__itens__recurso__sala__bloco')
            .annotate(
                _emprestimo_aberto=Exists(
                    ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('emprestimo_id'), devolvido_em__isnull=True)
                )
            )
        )

        if isinstance(status, str):
            status_normalizado = status.strip().upper()
            status_por_nome = {escolha.name: escolha.value for escolha in StatusSolicitacaoTrocaTitular}
            if status_normalizado.isdigit():
                status = int(status_normalizado)
            else:
                status = status_por_nome.get(status_normalizado)
        if status in StatusSolicitacaoTrocaTitular.values:
            qs = qs.filter(status=status)
        if direcao == 'recebidas':
            qs = qs.filter(destinatario=usuario)
        elif direcao == 'enviadas':
            qs = qs.filter(solicitante=usuario)
        if emprestimo_id is not None:
            qs = qs.filter(emprestimo_id=emprestimo_id)
        return qs.order_by('-created_at', '-pk')

    def obter_detalhada(self, solicitacao_id: int):
        return self.listar_detalhadas().get(pk=solicitacao_id)

    def listar_detalhadas(self):
        from .models import Emprestimo, ItemEmprestimo, SolicitacaoTrocaTitular

        itens_abertos = ItemEmprestimo.objects.filter(emprestimo_id=OuterRef('pk'), devolvido_em__isnull=True)
        emprestimos = (
            Emprestimo.objects.select_related('solicitante', 'responsavel')
            .prefetch_related('itens__recurso__sala__bloco')
            .annotate(_aberto=Exists(itens_abertos))
        )

        return SolicitacaoTrocaTitular.objects.select_related(
            'solicitante', 'destinatario', 'novo_emprestimo'
        ).prefetch_related(Prefetch('emprestimo', queryset=emprestimos))
