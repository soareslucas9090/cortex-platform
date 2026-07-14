from django.http import Http404
from rest_framework import status

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from Infraestrutura.permissoes.access import PodeOperarInfraestruturaMixin
from Infraestrutura.recursos.models import Recurso

from .models import Emprestimo
from .serializers import (
    DevolverItensSerializer,
    EmprestimoSerializer,
    RealizarEmprestimoSerializer,
    SerializerVazio,
    TrocarTitularSerializer,
    UsuarioResumoSerializer,
)


def queryset_emprestimo_detalhado():
    return Emprestimo.objects.select_related(
        'solicitante',
        'responsavel',
    ).prefetch_related(
        'itens__recurso__sala',
    ).all()


def _extrair_ids_recursos_da_query(query_params) -> list[int]:
    """Aceita `recurso_id`, `recurso_ids` repetidos ou separados por vírgula."""
    ids: list[int] = []
    for chave in ('recurso_ids', 'recurso_id'):
        for valor in query_params.getlist(chave):
            for parte in str(valor).split(','):
                parte = parte.strip()
                if parte.isdigit():
                    ids.append(int(parte))
    return list(dict.fromkeys(ids))


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar solicitantes elegíveis para recurso(s)',
    description='''
    Retorna usuários que podem ser solicitantes de empréstimo para **todos** os recursos
    informados, conforme as regras de elegibilidade (retirada irrestrita, autorização,
    SalaSetor, servente de limpeza).

    Informe um ou mais IDs em `recurso_id` e/ou `recurso_ids` (repetidos ou separados
    por vírgula). A resposta contém apenas usuários elegíveis a cada recurso enviado.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    parameters=[
        OpenApiParameter(
            'recurso_id',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='ID de um recurso (pode repetir o parâmetro para vários recursos).',
        ),
        OpenApiParameter(
            'recurso_ids',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='IDs de recursos (repetir o parâmetro ou separar por vírgula).',
        ),
        OpenApiParameter(
            'nome',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome do solicitante.',
        ),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: UsuarioResumoSerializer(many=True)},
)
class ListarSolicitantesElegiveisView(PodeOperarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/emprestimos/solicitantes-elegiveis/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioResumoSerializer
    mensagem_sucesso = 'Solicitantes elegíveis listados com sucesso.'

    def get_queryset(self):
        recurso_ids = _extrair_ids_recursos_da_query(self.request.query_params)
        if not recurso_ids:
            raise Http404('Informe ao menos um recurso.')

        recursos = list(
            Recurso.objects.select_related('sala').filter(pk__in=recurso_ids),
        )
        if len(recursos) != len(recurso_ids):
            raise Http404('Um ou mais recursos não foram encontrados.')

        nome = self.request.query_params.get('nome')
        return Emprestimo().helper.listar_solicitantes_elegiveis_para_recursos(
            recursos,
            nome=nome or None,
        )


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar empréstimos',
    description='''
    Com `operar`: consulta ampla com filtros.
    Sem `operar` (L1): apenas empréstimos ativos do próprio solicitante.

    **Permissões:** Usuário autenticado (escopo conforme capacidade `operar`).
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('solicitante_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('responsavel_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('recurso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('tipo_recurso', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: EmprestimoSerializer(many=True)},
)
class ListarEmprestimosView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/emprestimos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = EmprestimoSerializer
    mensagem_sucesso = 'Empréstimos listados com sucesso.'

    def get_queryset(self):
        params = self.request.query_params
        kwargs = {}

        ativo = params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            kwargs['ativo'] = ativo.lower() == 'true'

        solicitante_id = params.get('solicitante_id')
        if solicitante_id and solicitante_id.isdigit():
            kwargs['solicitante_id'] = int(solicitante_id)

        responsavel_id = params.get('responsavel_id')
        if responsavel_id and responsavel_id.isdigit():
            kwargs['responsavel_id'] = int(responsavel_id)

        recurso_id = params.get('recurso_id')
        if recurso_id and recurso_id.isdigit():
            kwargs['recurso_id'] = int(recurso_id)

        tipo_recurso = params.get('tipo_recurso')
        if tipo_recurso:
            kwargs['tipo_recurso'] = tipo_recurso

        return Emprestimo().helper.listar_para_usuario(self.request.user, **kwargs)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Realizar empréstimo',
    description='''
    Registra retirada multi-item para um solicitante.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=RealizarEmprestimoSerializer,
    responses={status.HTTP_201_CREATED: EmprestimoSerializer},
)
class RealizarEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/"""
    serializer_class = RealizarEmprestimoSerializer
    mensagem_sucesso = 'Empréstimo realizado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo = Emprestimo().business.realizar_emprestimo(
            responsavel=request.user,
            **serializer_data,
        )
        emprestimo = queryset_emprestimo_detalhado().get(pk=emprestimo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmprestimoSerializer(emprestimo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Detalhe do empréstimo',
    description='''
    Com `operar`: qualquer empréstimo.
    Sem `operar`: apenas empréstimos ativos do próprio solicitante.

    **Permissões:** Usuário autenticado (escopo conforme capacidade `operar`).
    ''',
    responses={status.HTTP_200_OK: EmprestimoSerializer},
)
class DetalheEmprestimoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/emprestimos/<pk>/"""
    queryset = queryset_emprestimo_detalhado()
    serializer_class = EmprestimoSerializer
    mensagem_sucesso = 'Empréstimo obtido com sucesso.'

    def validate_retrieve(self, request, *args, **kwargs):
        self.object.rules.pode_consultar(request.user)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Devolver itens',
    description='''
    Devolução parcial de itens. O empréstimo encerra quando todos forem devolvidos.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=DevolverItensSerializer,
    responses={status.HTTP_200_OK: EmprestimoSerializer},
)
class DevolverItensEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/<pk>/devolver/"""
    serializer_class = DevolverItensSerializer
    mensagem_sucesso = 'Itens devolvidos com sucesso.'
    queryset = Emprestimo.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo = self.get_object()
        emprestimo.business.devolver_itens(request.user, serializer_data['item_ids'])
        emprestimo = queryset_emprestimo_detalhado().get(pk=emprestimo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmprestimoSerializer(emprestimo).data,
        }


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Trocar titular',
    description='''
    Devolve itens em aberto e registra novo empréstimo para outro solicitante.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=TrocarTitularSerializer,
    responses={status.HTTP_201_CREATED: EmprestimoSerializer},
)
class TrocarTitularEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/<pk>/trocar-titular/"""
    serializer_class = TrocarTitularSerializer
    mensagem_sucesso = 'Titular trocado com sucesso.'
    queryset = Emprestimo.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo_anterior = self.get_object()
        novo_emprestimo = emprestimo_anterior.business.trocar_titular(
            request.user,
            **serializer_data,
        )
        novo_emprestimo = queryset_emprestimo_detalhado().get(pk=novo_emprestimo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmprestimoSerializer(novo_emprestimo).data,
            'status_code': status.HTTP_201_CREATED,
        }
