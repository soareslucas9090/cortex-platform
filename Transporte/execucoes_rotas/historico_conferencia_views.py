from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicRetrieveAPIView
from Transporte.permissoes.access import PodeConferirTransporteMixin

from .historico_conferencia_serializers import DetalheHistoricoConferenciaSerializer
from .historico_serializers import HistoricoRotaSerializer, PercursoHistoricoSerializer
from .models import ExecucaoRota

PERMISSAO_HISTORICO_CONFERENCIA = (
    '**Permissões:** capacidade `transporte.conferir` (conferente) ou L3 (administrador). '
    'Alunos, L2 sem conferir e motoristas sem conferir não têm acesso.'
)

REDUZ_CONJUNTO = (
    ' Apenas reduz o conjunto visível, nunca expande o acesso. Valor inválido é ignorado.'
)
PARAMETROS_FILTRO_HISTORICO = [
    OpenApiParameter(
        'busca', OpenApiTypes.STR,
        description=(
            'Apelido, descrição do percurso ou data (DD/MM/AAAA ou AAAA-MM-DD).'
            + REDUZ_CONJUNTO
        ),
    ),
    OpenApiParameter(
        'percurso_id', OpenApiTypes.INT,
        description='Filtra pelo percurso.' + REDUZ_CONJUNTO,
    ),
    OpenApiParameter(
        'data', OpenApiTypes.DATE,
        description='Filtra pela data da execução.' + REDUZ_CONJUNTO,
    ),
    OpenApiParameter(
        'ordenacao', OpenApiTypes.STR,
        enum=['data', '-data', 'horario', '-horario', 'percurso', '-percurso'],
        description='Ordenação da lista. Valor fora do enum usa o padrão (-data).' + REDUZ_CONJUNTO,
    ),
    OpenApiParameter('paginacao', OpenApiTypes.INT, description='Itens por página, entre 1 e 100.'),
]


@extend_schema(
    tags=['Transporte · Histórico de viagens'],
    summary='Listar histórico da conferência',
    description=(
        'Inclui somente viagens finalizadas pelo motorista. Mesmos filtros e contagens '
        'do histórico do motorista. O conferente autenticado no finalizar não aparece na lista. '
        'Filtros inválidos são ignorados e apenas reduzem o conjunto, nunca expandem o acesso.\n\n'
        + PERMISSAO_HISTORICO_CONFERENCIA
    ),
    parameters=PARAMETROS_FILTRO_HISTORICO,
    responses={
        200: HistoricoRotaSerializer(many=True),
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem capacidade conferir.'},
    },
)
class ListarHistoricoConferenciaView(PodeConferirTransporteMixin, BasicGetAPIView):
    serializer_class = HistoricoRotaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Histórico da conferência listado com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_historico_conferencia(
            self.request.user, self.request.query_params,
        )


@extend_schema(
    tags=['Transporte · Histórico de viagens'],
    summary='Listar percursos com viagens no histórico da conferência',
    description=(
        'Opções do filtro, incluindo percursos desativados com histórico.\n\n'
        + PERMISSAO_HISTORICO_CONFERENCIA
    ),
    parameters=[
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, description='Itens por página, entre 1 e 100.',
        ),
    ],
    responses={
        200: PercursoHistoricoSerializer(many=True),
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem capacidade conferir.'},
    },
)
class ListarPercursosHistoricoConferenciaView(PodeConferirTransporteMixin, BasicGetAPIView):
    serializer_class = PercursoHistoricoSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Percursos do histórico da conferência listados com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_percursos_historico_conferencia(self.request.user)


@extend_schema(
    tags=['Transporte · Histórico de viagens'],
    summary='Detalhar viagem no histórico da conferência',
    description=(
        'Horários, conferente que finalizou a conferência e alunos (id, nome, CPF, '
        'tem_deficiencia) por categoria. Sem foto nem tipo clínico.\n\n'
        + PERMISSAO_HISTORICO_CONFERENCIA
    ),
    responses={
        200: DetalheHistoricoConferenciaSerializer,
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem capacidade conferir.'},
        404: {'description': 'Viagem inexistente ou ainda não concluída.'},
    },
)
class DetalharHistoricoConferenciaView(PodeConferirTransporteMixin, BasicRetrieveAPIView):
    serializer_class = DetalheHistoricoConferenciaSerializer
    mensagem_sucesso = 'Detalhes da conferência no histórico obtidos com sucesso.'

    def get_object(self):
        return ExecucaoRota().business.detalhar_historico_conferencia(
            self.request.user, self.kwargs['pk'],
        )
