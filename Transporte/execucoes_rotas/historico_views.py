from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicRetrieveAPIView
from Transporte.permissoes.access import PodeOperarRotaMixin

from .historico_serializers import (
    DetalheHistoricoRotaSerializer,
    HistoricoRotaSerializer,
    PercursoHistoricoSerializer,
)
from .models import ExecucaoRota

PERMISSAO_HISTORICO = (
    '**Permissões:** Motorista ativo ou L3 (administrador). '
    'Todos consultam as viagens concluídas de todos os motoristas. '
    'Alunos, conferentes sem perfil motorista e L2 não têm acesso.'
)


@extend_schema(
    tags=['Transporte · Motorista'],
    summary='Listar histórico de rotas executadas',
    description=(
        'Inclui somente viagens finalizadas pelo motorista. Preserva rotas e percursos '
        'desativados. Presentes conta tickets embarcados, ausentes conta tickets ausentes '
        'e sem_ticket conta entradas registradas sem ticket. '
        'Filtros inválidos são ignorados.\n\n' + PERMISSAO_HISTORICO
    ),
    parameters=[
        OpenApiParameter(
            'busca', OpenApiTypes.STR,
            description='Apelido, descrição do percurso ou data (DD/MM/AAAA ou AAAA-MM-DD).',
        ),
        OpenApiParameter('percurso_id', OpenApiTypes.INT),
        OpenApiParameter('data', OpenApiTypes.DATE),
        OpenApiParameter(
            'ordenacao', OpenApiTypes.STR,
            enum=['data', '-data', 'horario', '-horario', 'percurso', '-percurso'],
        ),
        OpenApiParameter('paginacao', OpenApiTypes.INT, description='Itens por página, entre 1 e 100.'),
    ],
    responses={
        200: HistoricoRotaSerializer(many=True),
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem acesso ao histórico.'},
    },
)
class ListarHistoricoRotasView(PodeOperarRotaMixin, BasicGetAPIView):
    serializer_class = HistoricoRotaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Histórico de rotas listado com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_historico(self.request.user, self.request.query_params)


@extend_schema(
    tags=['Transporte · Motorista'],
    summary='Listar percursos com viagens concluídas',
    description='Opções do filtro, incluindo percursos desativados com histórico.\n\n' + PERMISSAO_HISTORICO,
    responses={
        200: PercursoHistoricoSerializer(many=True),
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem acesso ao histórico.'},
    },
)
class ListarPercursosHistoricoView(PodeOperarRotaMixin, BasicGetAPIView):
    serializer_class = PercursoHistoricoSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Percursos do histórico listados com sucesso.'

    def get_queryset(self):
        return ExecucaoRota().business.listar_percursos_historico(self.request.user)


@extend_schema(
    tags=['Transporte · Motorista'],
    summary='Detalhar rota executada',
    description=(
        'Horários, duração, responsável e nomes dos passageiros por categoria. '
        'Não expõe CPF, contatos nem informações clínicas.\n\n' + PERMISSAO_HISTORICO
    ),
    responses={
        200: DetalheHistoricoRotaSerializer,
        401: {'description': 'Não autenticado.'},
        403: {'description': 'Perfil sem acesso ao histórico.'},
        404: {'description': 'Viagem inexistente ou ainda não concluída.'},
    },
)
class DetalharHistoricoRotaView(PodeOperarRotaMixin, BasicRetrieveAPIView):
    serializer_class = DetalheHistoricoRotaSerializer
    mensagem_sucesso = 'Detalhes da rota executada obtidos com sucesso.'

    def get_object(self):
        return ExecucaoRota().business.detalhar_historico(self.request.user, self.kwargs['pk'])
