from django.http import HttpResponse

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView
from Infraestrutura.permissoes.access import PodeOperarInfraestruturaMixin
from Infraestrutura.recursos.choices import TipoRecurso

from .models import RelatorioEmprestimos
from .serializers import (
    ListarPessoasRelatorioQuerySerializer,
    PessoaRelatorioSerializer,
    RelatorioEmprestimosQuerySerializer,
)

PERMISSAO_OPERAR = (
    '**Permissões:** capacidade `operar` em Infraestrutura (administradores e superusuários '
    'incluídos pelo bypass de acesso total).'
)

DESCRICAO_PDF = f'''
Gera o relatório de empréstimos em PDF sob demanda, sem persistir o arquivo.

O período filtra `retirada_em` no fuso America/Sao_Paulo (inclusive 00:00 do dia inicial
até antes de 00:00 do dia seguinte ao final). A diferença máxima entre as datas é de 30 dias.
Inclui empréstimos com itens devolvidos e em aberto. Filtros de tipo de recurso, sala e bloco
restringem os **itens** impressos (histórico, inclusive devolvidos). Quando sala e bloco são
informados juntos, a sala deve pertencer ao bloco. O limite é de 3000 empréstimos por geração;
acima disso refine os filtros. O escopo de origem coletiva segue a mesma regra da listagem.

Diferente da listagem de empréstimos, parâmetros de query inválidos retornam 400 (não são
ignorados), pois um filtro ignorado alteraria o conteúdo do PDF.

{PERMISSAO_OPERAR}
'''


class BaixarRelatorioEmprestimosPdfView(PodeOperarInfraestruturaMixin, BasicGetAPIView):
    serializer_class = RelatorioEmprestimosQuerySerializer
    mensagem_sucesso = 'Relatório de empréstimos gerado com sucesso.'

    @extend_schema(
        tags=['Infraestrutura · Empréstimos'],
        summary='Baixar relatório de empréstimos em PDF',
        description=DESCRICAO_PDF,
        parameters=[
            OpenApiParameter(
                'data_inicio',
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=True,
                description='Data inicial do período (AAAA-MM-DD), inclusiva em America/Sao_Paulo.',
            ),
            OpenApiParameter(
                'data_fim',
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=True,
                description='Data final do período (AAAA-MM-DD), inclusiva em America/Sao_Paulo.',
            ),
            OpenApiParameter(
                'solicitante_id',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description='Filtra por solicitante.',
            ),
            OpenApiParameter(
                'responsavel_id',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description='Filtra por responsável que registrou a entrega.',
            ),
            OpenApiParameter(
                'tipo_recurso',
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                enum=[item.value for item in TipoRecurso],
                description='Filtra itens pelo tipo de recurso.',
            ),
            OpenApiParameter(
                'bloco_id',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description='Filtra itens pelo bloco da sala do recurso.',
            ),
            OpenApiParameter(
                'sala_id',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
                description='Filtra itens pela sala do recurso.',
            ),
        ],
        responses={
            status.HTTP_200_OK: {'description': 'Arquivo PDF do relatório de empréstimos.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Parâmetros inválidos ou limite excedido.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade operar.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        serializer = RelatorioEmprestimosQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        conteudo, nome_arquivo = RelatorioEmprestimos().business.gerar_pdf(
            request.user,
            serializer.validated_data,
        )
        resposta = HttpResponse(conteudo, content_type='application/pdf')
        resposta['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        resposta['Cache-Control'] = 'no-store'
        return resposta


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar pessoas do relatório de empréstimos',
    description=f'''
    Lista solicitantes ou responsáveis que já aparecem em empréstimos no escopo do operador
    (origem coletiva, quando aplicável), inclusive usuários inativos. Os parâmetros apenas
    reduzem o conjunto.

    {PERMISSAO_OPERAR}
    ''',
    parameters=[
        OpenApiParameter(
            'papel',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            enum=['solicitante', 'responsavel'],
            description='Papel da pessoa no empréstimo.',
        ),
        OpenApiParameter(
            'nome',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome (icontains).',
        ),
        OpenApiParameter(
            'page',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Página solicitada.',
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Itens por página.',
        ),
    ],
    responses={
        status.HTTP_200_OK: PessoaRelatorioSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: {'description': 'Parâmetros inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade operar.'},
    },
)
class ListarPessoasRelatorioView(PodeOperarInfraestruturaMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = PessoaRelatorioSerializer
    mensagem_sucesso = 'Pessoas do relatório listadas com sucesso.'

    def validate_get(self, request, *args, **kwargs):
        serializer = ListarPessoasRelatorioQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self._filtros = serializer.validated_data

    def get_queryset(self):
        return RelatorioEmprestimos().business.listar_pessoas(self.request.user, self._filtros)