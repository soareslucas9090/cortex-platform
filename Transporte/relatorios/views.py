from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.views.basic_views import BasicGetAPIView
from AppCore.core.exceptions.exceptions import ValidationException

from .business import RelatorioAlunosBusiness
from .choices import CategoriaRelatorioAluno
from .serializers import (
    RelatorioAlunosDashboardSerializer,
    RelatorioAlunosDetalhesSerializer,
)

PERMISSAO_ADMIN = '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'


def _parse_date_param(valor: str | None, nome: str):
    if not valor:
        raise ValidationException(f'O parâmetro {nome} é obrigatório.')
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationException(f'{nome} deve estar no formato AAAA-MM-DD.')


@extend_schema(
    tags=['Transporte · Relatórios'],
    summary='Dashboard do relatório de alunos',
    description=(
        'Retorna o resumo agregado e a distribuição por horário de rota no período informado.\n\n'
        f'{PERMISSAO_ADMIN}'
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
class RelatorioAlunosDashboardView(IsAdminMixin, BasicGetAPIView):
    serializer_class = RelatorioAlunosDashboardSerializer
    mensagem_sucesso = 'Dashboard do relatório de alunos gerado com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        data_inicio = _parse_date_param(request.query_params.get('data_inicio'), 'data_inicio')
        data_fim = _parse_date_param(request.query_params.get('data_fim'), 'data_fim')

        dados = RelatorioAlunosBusiness().obter_dashboard(data_inicio, data_fim)
        serializer = self.get_serializer(dados)

        return Response({
            'status': 'success',
            'mensagem': self.mensagem_sucesso,
            'dados': serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Transporte · Relatórios'],
    summary='Detalhes do relatório de alunos por categoria',
    description=(
        'Lista paginada de alunos enriquecidos para a aba Detalhes, filtrada por categoria.\n\n'
        f'{PERMISSAO_ADMIN}'
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
        OpenApiParameter('page', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: RelatorioAlunosDetalhesSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Parâmetros inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class RelatorioAlunosDetalhesView(IsAdminMixin, BasicGetAPIView):
    serializer_class = RelatorioAlunosDetalhesSerializer
    mensagem_sucesso = 'Detalhes do relatório de alunos listados com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        data_inicio = _parse_date_param(request.query_params.get('data_inicio'), 'data_inicio')
        data_fim = _parse_date_param(request.query_params.get('data_fim'), 'data_fim')
        categoria = request.query_params.get('categoria')
        if not categoria:
            raise ValidationException('O parâmetro categoria é obrigatório.')

        page = int(request.query_params.get('page', 1))
        paginacao = int(request.query_params.get('paginacao', 10))
        busca = request.query_params.get('busca', '')

        dados = RelatorioAlunosBusiness().obter_detalhes(
            data_inicio,
            data_fim,
            categoria,
            busca=busca,
            page=page,
            paginacao=paginacao,
        )
        serializer = self.get_serializer(dados)

        return Response({
            'status': 'success',
            'mensagem': self.mensagem_sucesso,
            'count': dados['count'],
            'next': dados['next'],
            'previous': dados['previous'],
            'categoria': dados['categoria'],
            'dados': dados['results'],
        }, status=status.HTTP_200_OK)
