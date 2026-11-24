from datetime import datetime, time, timedelta

from django.db.models import Exists, OuterRef, Prefetch, Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class RelatorioEmprestimosHelpers(ModelInstanceHelpers):

    def sala_pertence_ao_bloco(self, sala_id: int, bloco_id: int) -> bool:
        from Infraestrutura.salas.models import Sala

        return Sala.objects.filter(pk=sala_id, bloco_id=bloco_id).exists()

    def _criterio_filtro_itens(self, filtros: dict) -> tuple[Q, bool]:
        criterio = Q()
        tem_filtro = False
        tipo_recurso = filtros.get('tipo_recurso')
        if tipo_recurso:
            criterio &= Q(recurso__tipo=tipo_recurso)
            tem_filtro = True
        sala_id = filtros.get('sala_id')
        if sala_id:
            criterio &= Q(recurso__sala_id=sala_id)
            tem_filtro = True
        bloco_id = filtros.get('bloco_id')
        if bloco_id:
            criterio &= Q(recurso__sala__bloco_id=bloco_id)
            tem_filtro = True
        return criterio, tem_filtro

    def listar_emprestimos(self, usuario, filtros: dict):
        from Infraestrutura.emprestimos.helpers import FUSO_HORARIO_EMPRESTIMOS
        from Infraestrutura.emprestimos.models import Emprestimo, ItemEmprestimo

        data_inicio = filtros['data_inicio']
        data_fim = filtros['data_fim']
        inicio_local = datetime.combine(data_inicio, time.min, tzinfo=FUSO_HORARIO_EMPRESTIMOS)
        fim_exclusivo = datetime.combine(
            data_fim + timedelta(days=1),
            time.min,
            tzinfo=FUSO_HORARIO_EMPRESTIMOS,
        )

        qs = Emprestimo.objects.filter(
            retirada_em__gte=inicio_local,
            retirada_em__lt=fim_exclusivo,
        )

        qs = Emprestimo().helper.restringir_por_origem_conta_coletiva(qs, usuario)

        solicitante_id = filtros.get('solicitante_id')
        if solicitante_id:
            qs = qs.filter(solicitante_id=solicitante_id)
        responsavel_id = filtros.get('responsavel_id')
        if responsavel_id:
            qs = qs.filter(responsavel_id=responsavel_id)

        criterio_itens, tem_filtro_item = self._criterio_filtro_itens(filtros)

        if tem_filtro_item:
            qs = qs.filter(
                Exists(
                    ItemEmprestimo.objects.filter(
                        emprestimo_id=OuterRef('pk'),
                    ).filter(criterio_itens),
                ),
            )
            itens_qs = (
                ItemEmprestimo.objects.filter(criterio_itens)
                .select_related('recurso', 'recurso__sala', 'recurso__sala__bloco')
                .order_by('recurso__codigo')
            )
        else:
            itens_qs = (
                ItemEmprestimo.objects.select_related(
                    'recurso',
                    'recurso__sala',
                    'recurso__sala__bloco',
                ).order_by('recurso__codigo')
            )

        return (
            qs.select_related('solicitante', 'responsavel')
            .prefetch_related(Prefetch('itens', queryset=itens_qs))
            .order_by('retirada_em', 'pk')
        )

    def listar_pessoas(self, usuario, filtros: dict):
        from Identidade.usuarios.models import Usuario
        from Infraestrutura.emprestimos.models import Emprestimo

        papel = filtros['papel']
        campo = 'solicitante_id' if papel == 'solicitante' else 'responsavel_id'

        emprestimos_escopo = Emprestimo().helper.restringir_por_origem_conta_coletiva(
            Emprestimo.objects.all(),
            usuario,
        )
        ids = emprestimos_escopo.order_by().values_list(campo, flat=True).distinct()

        qs = Usuario.objects.filter(id__in=ids).only('id', 'nome').order_by('nome')
        nome = (filtros.get('nome') or '').strip()
        if nome:
            qs = qs.filter(nome__icontains=nome)
        return qs

    def resolver_rotulo_pessoa(self, usuario_id: int | None) -> str | None:
        if not usuario_id:
            return None
        from Identidade.usuarios.models import Usuario

        return Usuario.objects.filter(pk=usuario_id).values_list('nome', flat=True).first()

    def resolver_rotulo_bloco(self, bloco_id: int | None) -> str | None:
        if not bloco_id:
            return None
        from Infraestrutura.blocos.models import Bloco

        return Bloco.objects.filter(pk=bloco_id).values_list('nome', flat=True).first()

    def resolver_rotulo_sala(self, sala_id: int | None) -> str | None:
        if not sala_id:
            return None
        from Infraestrutura.salas.models import Sala

        sala = Sala.objects.select_related('bloco').filter(pk=sala_id).first()
        if not sala:
            return None
        return f'{sala.bloco.nome} — {sala.nome}'