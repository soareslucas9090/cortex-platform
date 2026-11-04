from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicPostAPIView, BasicRetrieveAPIView
from AcessoCampus.permissoes.access import PodeOperarPortariaMixin

from .models import EventoAcesso
from .serializers import (
    AlunoEventoAcessoSerializer,
    EventoAcessoDetalheSerializer,
    EventoAcessoSerializer,
    RegistrarEventoAcessoSerializer,
    RegistrarEventoAcessoResponseSerializer,
    ResponsavelElegivelSerializer,
)

PERMISSAO_PORTARIA = '''
    **Permissões:** `operar_portaria` ou L3 (EDITAR_TUDO).

    Os query params apenas reduzem o conjunto e nunca expandem o acesso concedido.
    '''

PARAMETRO_PAGINACAO = OpenApiParameter(
    'paginacao',
    OpenApiTypes.INT,
    OpenApiParameter.QUERY,
    required=False,
    description='Quantidade por página, entre 1 e 100.',
)


@extend_schema(
    tags=['AcessoCampus - Portaria'],
    summary='Listar autorizações da portaria',
    description=f'''
    Lista autorizações individuais ou de turma disponíveis para operação da portaria.

    {PERMISSAO_PORTARIA}
    ''',
    parameters=[
        OpenApiParameter(
            'status', OpenApiTypes.STR, OpenApiParameter.QUERY, many=True,
            enum=['PENDENTE', 'CONCLUIDA', 'EXPIRADA'],
            description='Filtra por um ou mais status operacionais.',
        ),
        OpenApiParameter(
            'busca', OpenApiTypes.STR, OpenApiParameter.QUERY,
            description='Busca por aluno, turma ou responsável pela autorização.',
        ),
        OpenApiParameter(
            'tipo_movimento', OpenApiTypes.STR, OpenApiParameter.QUERY,
            enum=['ENTRADA', 'SAIDA'], description='Filtra pelos dois tipos-base de movimento.',
        ),
        OpenApiParameter(
            'tipo_beneficiario', OpenApiTypes.STR, OpenApiParameter.QUERY,
            enum=['INDIVIDUAL', 'TURMA'], description='Filtra o tipo de beneficiário.',
        ),
        OpenApiParameter(
            'data_autorizada', OpenApiTypes.DATE, OpenApiParameter.QUERY,
            description='Data autorizada no formato YYYY-MM-DD.',
        ),
        OpenApiParameter('hora_inicio', OpenApiTypes.TIME, OpenApiParameter.QUERY),
        OpenApiParameter('hora_fim', OpenApiTypes.TIME, OpenApiParameter.QUERY),
        OpenApiParameter(
            'ordenacao', OpenApiTypes.STR, OpenApiParameter.QUERY,
            enum=[
                'nome', '-nome', 'tipo_movimento', '-tipo_movimento', 'autorizado_por',
                '-autorizado_por', 'data_autorizada', '-data_autorizada', 'hora_autorizada',
                '-hora_autorizada',
            ],
        ),
        PARAMETRO_PAGINACAO,
    ],
    responses={
        status.HTTP_200_OK: EventoAcessoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem operar_portaria.'},
    },
)
class ListarEventosAcessoView(PodeOperarPortariaMixin, BasicGetAPIView):
    serializer_class = EventoAcessoSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Autorizações de acesso listadas com sucesso.'

    def get_queryset(self):
        return EventoAcesso().business.listar_grupos(self.request.query_params)


@extend_schema(
    tags=['AcessoCampus - Portaria'],
    summary='Detalhar autorização da portaria',
    description=f'''
    Detalha uma autorização agrupada da portaria.

    {PERMISSAO_PORTARIA}
    ''',
    responses={
        status.HTTP_200_OK: EventoAcessoDetalheSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem operar_portaria.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Autorização não encontrada.'},
    },
)
class DetalharEventoAcessoView(PodeOperarPortariaMixin, BasicRetrieveAPIView):
    serializer_class = EventoAcessoDetalheSerializer
    lookup_field = 'grupo_portaria_id'
    lookup_url_kwarg = 'grupo_portaria_id'
    mensagem_sucesso = 'Autorização de acesso detalhada com sucesso.'

    def get_queryset(self):
        return EventoAcesso().business.listar_grupos()


@extend_schema(
    tags=['AcessoCampus - Portaria'],
    summary='Listar alunos para conferência',
    description=f'''
    Lista os alunos congelados na autorização de turma para conferência parcial.

    {PERMISSAO_PORTARIA}
    ''',
    parameters=[
        OpenApiParameter('busca', OpenApiTypes.STR, OpenApiParameter.QUERY),
        PARAMETRO_PAGINACAO,
    ],
    responses={
        status.HTTP_200_OK: AlunoEventoAcessoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem operar_portaria.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Autorização não encontrada.'},
    },
)
class ListarAlunosEventoAcessoView(PodeOperarPortariaMixin, BasicGetAPIView):
    serializer_class = AlunoEventoAcessoSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Alunos da autorização listados com sucesso.'

    def get_queryset(self):
        return EventoAcesso().business.listar_alunos_grupo(
            self.kwargs['grupo_portaria_id'],
            self.request.query_params,
        )


@extend_schema(
    tags=['AcessoCampus - Portaria'],
    summary='Registrar entrada ou saída',
    description=f'''
    Registra a movimentação individual ou a seleção parcial de alunos de uma turma.

    {PERMISSAO_PORTARIA}
    ''',
    request=RegistrarEventoAcessoSerializer,
    responses={
        status.HTTP_200_OK: RegistrarEventoAcessoResponseSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Autorização expirada ou dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem operar_portaria.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Autorização não encontrada.'},
    },
)
class RegistrarEventoAcessoView(PodeOperarPortariaMixin, BasicPostAPIView):
    serializer_class = RegistrarEventoAcessoSerializer
    mensagem_sucesso = 'Acesso registrado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        eventos, resumo = EventoAcesso().business.registrar(
            grupo_portaria_id=kwargs['grupo_portaria_id'],
            operador=request.user,
            responsavel_id=serializer_data.get('responsavel_liberacao_id'),
            aluno_ids=serializer_data.get('aluno_ids'),
            observacao=serializer_data.get('observacao', ''),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': {
                'autorizacao': EventoAcessoDetalheSerializer(eventos[0]).data,
                'registro': resumo,
            },
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['AcessoCampus - Portaria'],
    summary='Listar responsáveis elegíveis',
    description=f'''
    Lista os vigilantes físicos que podem ser informados por uma conta guarita.

    {PERMISSAO_PORTARIA}
    ''',
    parameters=[
        OpenApiParameter('busca', OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter('cpf', OpenApiTypes.STR, OpenApiParameter.QUERY),
        PARAMETRO_PAGINACAO,
    ],
    responses={
        status.HTTP_200_OK: ResponsavelElegivelSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem operar_portaria.'},
    },
)
class ListarResponsaveisElegiveisView(PodeOperarPortariaMixin, BasicGetAPIView):
    serializer_class = ResponsavelElegivelSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Responsáveis elegíveis listados com sucesso.'

    def get_queryset(self):
        return EventoAcesso().business.listar_responsaveis(
            self.request.user,
            self.request.query_params,
        )
