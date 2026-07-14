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

from .models import Emprestimo
from .serializers import (
    DevolverItensSerializer,
    EmprestimoSerializer,
    RealizarEmprestimoSerializer,
    SerializerVazio,
    TrocarTitularSerializer,
)


def queryset_emprestimo_detalhado():
    return Emprestimo.objects.select_related(
        'solicitante',
        'responsavel',
    ).prefetch_related(
        'itens__recurso__sala',
    ).all()


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
