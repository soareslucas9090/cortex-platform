from django.http import StreamingHttpResponse
from rest_framework import parsers, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicPostAPIView
from Infraestrutura.permissoes.access import PodeCadastrarInfraestruturaMixin

from .models import ImportacaoLote
from .serializers import (
    ArquivoImportacaoInfraestruturaSerializer,
    ImportacaoInfraestruturaPreviewResponseSerializer,
    SerializerVazio,
    StatusImportacaoLoteSerializer,
)


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Baixar modelo de importação de infraestrutura',
    description='''
    Retorna o arquivo modelo `.ods` para importação em lote de blocos, salas e recursos.

    **Permissões:** cadastrar
    ''',
    responses={
        status.HTTP_200_OK: {'description': 'Arquivo retornado com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Arquivo modelo não encontrado.'},
    },
)
class BaixarModeloImportacaoInfraestruturaView(PodeCadastrarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/importacao/modelo/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Modelo de importação localizado com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        stream, content_type = ImportacaoLote().business.obter_arquivo_modelo_importacao()
        response = StreamingHttpResponse(stream, content_type=content_type)
        response['Content-Disposition'] = (
            'attachment; filename="modelo-importacao-infraestrutura.ods"'
        )
        return response


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Pré-visualizar importação em lote de infraestrutura',
    description='''
    Recebe um arquivo `.ods` e executa validação estrutural sem persistir dados.

    **Permissões:** cadastrar
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo para upload',
                }
            },
            'required': ['file'],
        }
    },
    responses={
        status.HTTP_200_OK: ImportacaoInfraestruturaPreviewResponseSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Arquivo inválido ou estrutura inconsistente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class PreVisualizarImportacaoInfraestruturaView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/importacao/pre-visualizar/"""
    parser_classes = (MultiPartParser,)
    serializer_class = ArquivoImportacaoInfraestruturaSerializer
    mensagem_sucesso = 'Pré-visualização concluída com sucesso.'

    def do_action_post(self, serializer_data, request):
        resultado = ImportacaoLote().business.pre_visualizar_importacao(
            arquivo=serializer_data['file']
        )
        return {
            'mensagem': resultado.mensagem,
            'dados': {
                'sucesso': resultado.sucesso,
                'mensagem': resultado.mensagem,
                'resumo': resultado.resumo.__dict__,
                'erros': [erro.__dict__ for erro in resultado.erros],
                'metadados': resultado.metadados,
            },
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Importar infraestrutura em lote (Assíncrono)',
    description='''
    Inicia o processo de importação em lote enviando o arquivo `.ods`.
    O processamento ocorre em background (Celery).

    **Permissões:** cadastrar
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo para upload',
                }
            },
            'required': ['file'],
        }
    },
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Importação enviada para fila de processamento.'},
        status.HTTP_400_BAD_REQUEST: {
            'description': 'Já existe uma importação em andamento ou arquivo inválido.'
        },
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ImportarInfraestruturaLoteView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/importacao/"""
    parser_classes = (MultiPartParser, parsers.FormParser)
    serializer_class = ArquivoImportacaoInfraestruturaSerializer
    mensagem_sucesso = 'Importação enviada para fila de processamento.'

    def do_action_post(self, serializer_data, request):
        importacao_id = ImportacaoLote().business.iniciar_importacao(
            arquivo=serializer_data['file']
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': {'importacao_id': importacao_id},
            'status_code': status.HTTP_202_ACCEPTED,
        }


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Consultar status da importação de infraestrutura',
    description='''
    Retorna o status da importação atual ou da última importação realizada.

    **Permissões:** cadastrar
    ''',
    responses={
        status.HTTP_200_OK: StatusImportacaoLoteSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Nenhuma importação encontrada.'},
    },
)
class StatusImportacaoLoteView(PodeCadastrarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/importacao/status/"""
    serializer_class = StatusImportacaoLoteSerializer
    mensagem_sucesso = 'Status retornado com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        importacao = ImportacaoLote().business.obter_status_recente()
        serializer = self.get_serializer(importacao)
        return Response({
            'status': 'success',
            'mensagem': self.mensagem_sucesso,
            'dados': serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Cancelar importação em lote de infraestrutura',
    description='''
    Cancela uma importação com status EM_ANDAMENTO.

    **Permissões:** cadastrar
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Importação cancelada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Não há importação em andamento.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class CancelarImportacaoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/importacao/cancelar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Importação cancelada com sucesso.'

    def do_action_post(self, serializer_data, request):
        ImportacaoLote().business.cancelar_importacoes_em_andamento()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': {},
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Infraestrutura · Importação'],
    summary='Histórico de importações de infraestrutura',
    description='''
    Retorna a lista paginada do histórico de importações.

    **Permissões:** cadastrar

    **Query params:**
    - `status` (str, opcional): EM_ANDAMENTO, CONCLUIDA, ERRO.
    - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.
    ''',
    parameters=[
        OpenApiParameter(
            'status',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra pelo status (EM_ANDAMENTO, CONCLUIDA, ERRO).',
            enum=['EM_ANDAMENTO', 'CONCLUIDA', 'ERRO'],
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: StatusImportacaoLoteSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class HistoricoImportacaoLoteView(PodeCadastrarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/importacao/historico/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = StatusImportacaoLoteSerializer
    mensagem_sucesso = 'Histórico de importações listado com sucesso.'

    def get_queryset(self):
        qs = ImportacaoLote.objects.all()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs
