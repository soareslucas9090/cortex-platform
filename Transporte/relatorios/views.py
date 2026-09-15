from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.views.basic_views import BasicGetAPIView
from Transporte.permissoes.access import PodeVisualizarRelatorioAlunosMixin

from .choices import CategoriaRelatorioAluno
from .models import RelatorioAlunos
from .serializers import (
    RelatorioAlunosDashboardSerializer,
    RelatorioAlunosDetalhesSerializer,
)

PERMISSAO_RELATORIO_ALUNOS = (
    '**Permissões:** capacidade `transporte.visualizar_relatorio_alunos`. '
    'Disponível para L3, diretores, coordenadores e chefes com vínculo ativo, '
    'além de colaboradores autorizados diretamente.'
)


@extend_schema(
    tags=['Transporte · Relatórios'],
    summary='Dashboard do relatório de alunos',
    description=(
        'Retorna o resumo agregado e a distribuição por horário no período informado.\n\n'
        '`sem_ticket` conta registros de `EntradaSemTicket` no período: walk-in '
        'nas vagas restantes após a chamada, inclusive quem estava `EM_ESPERA` e '
        'entrou por CPF (`CONTEMPLADO`). Não conta quem apenas deixou de reservar '
        'ticket.\n\n'
        f'{PERMISSAO_RELATORIO_ALUNOS}'
    ),
    parameters=[
        OpenApiParameter(
            'data_inicio',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=True,
            description='Data inicial do período (AAAA-MM-DD).',
        ),
        OpenApiParameter(
            'data_fim',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=True,
            description='Data final do período (AAAA-MM-DD).',
        ),
    ],
    responses={
        status.HTTP_200_OK: RelatorioAlunosDashboardSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Parâmetros inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class RelatorioAlunosDashboardView(PodeVisualizarRelatorioAlunosMixin, BasicGetAPIView):
    serializer_class = RelatorioAlunosDashboardSerializer
    mensagem_sucesso = 'Dashboard do relatório de alunos gerado com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        dados = RelatorioAlunos().business.obter_dashboard(request.query_params)
        serializer = self.get_serializer(dados)
        return Response(
            {
                'status': 'success',
                'mensagem': self.mensagem_sucesso,
                'dados': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['Transporte · Relatórios'],
    summary='Detalhes do relatório de alunos por categoria',
    description=(
        'Lista paginada de alunos enriquecidos para a aba Detalhes, filtrada por '
        'categoria. Query params apenas reduzem o conjunto dentro do escopo já '
        'autorizado e nunca expandem o acesso.\n\n'
        f'{PERMISSAO_RELATORIO_ALUNOS}'
    ),
    parameters=[
        OpenApiParameter(
            'data_inicio',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=True,
        ),
        OpenApiParameter(
            'data_fim',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=True,
        ),
        OpenApiParameter(
            'categoria',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            enum=[item.value for item in CategoriaRelatorioAluno],
        ),
        OpenApiParameter(
            'busca',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome do aluno.',
        ),
        OpenApiParameter(
            'page',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Página solicitada (mínimo 1, padrão 1).',
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Itens por página (mínimo 1, máximo 100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: RelatorioAlunosDetalhesSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Parâmetros inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class RelatorioAlunosDetalhesView(PodeVisualizarRelatorioAlunosMixin, BasicGetAPIView):
    serializer_class = RelatorioAlunosDetalhesSerializer
    mensagem_sucesso = 'Detalhes do relatório de alunos listados com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        dados = RelatorioAlunos().business.obter_detalhes(request.query_params)
        serializer = self.get_serializer(dados)
        dados_validados = serializer.data
        return Response(
            {
                'status': 'success',
                'mensagem': self.mensagem_sucesso,
                'count': dados_validados['count'],
                'next': dados_validados['next'],
                'previous': dados_validados['previous'],
                'categoria': dados_validados['categoria'],
                'dados': dados_validados['results'],
            },
            status=status.HTTP_200_OK,
        )
