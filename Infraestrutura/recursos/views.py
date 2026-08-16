from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AllowAnyMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicDeleteAPIView,
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from Infraestrutura.permissoes.access import PodeCadastrarInfraestruturaMixin

from .choices import TipoRecurso
from .models import Recurso
from .serializers import (
    AtualizarRecursoSerializer,
    CriarRecursoSerializer,
    EnviarFotoRecursoSerializer,
    RecursoSerializer,
    SerializerVazio,
)


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Listar recursos',
    description='''
    Retorna a lista paginada de recursos físicos.

    **Permissões:** Qualquer usuário autenticado. Escrita exige capacidade `cadastrar`.
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('codigo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('tipo', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('sala_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: RecursoSerializer(many=True)},
)
class ListarRecursosView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/recursos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = RecursoSerializer
    mensagem_sucesso = 'Recursos listados com sucesso.'

    def get_queryset(self):
        qs = Recurso.objects.select_related('sala').all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        codigo = self.request.query_params.get('codigo')
        if codigo:
            qs = qs.filter(codigo__unaccent__icontains=codigo)
        tipo = self.request.query_params.get('tipo')
        if tipo and tipo in TipoRecurso.values:
            qs = qs.filter(tipo=tipo)
        sala_id = self.request.query_params.get('sala_id')
        if sala_id and sala_id.isdigit():
            qs = qs.filter(sala_id=sala_id)
        return qs


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Criar recurso',
    description='''
    Cria um novo recurso. Tipo chave exige sala vinculada.

    A foto é opcional. Envie `multipart/form-data` para incluir o arquivo
    (JPEG, PNG ou WebP, até 3 MB, orientação retrato, recorte 3:4, mínimo 480×640).
    Cadastro em JSON sem foto continua válido.

    **Permissões:** Capacidade `cadastrar` em Infraestrutura.
    ''',
    request=CriarRecursoSerializer,
    responses={status.HTTP_201_CREATED: RecursoSerializer},
)
class CriarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/"""
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    serializer_class = CriarRecursoSerializer
    mensagem_sucesso = 'Recurso criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        recurso = Recurso().business.criar_recurso(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RecursoSerializer(recurso, context={'request': request}).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Detalhe do recurso',
    description='Retorna os dados de um recurso.\n\n**Permissões:** Qualquer usuário autenticado.',
    responses={status.HTTP_200_OK: RecursoSerializer},
)
class DetalheRecursoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/recursos/<pk>/"""
    queryset = Recurso.objects.select_related('sala').all()
    serializer_class = RecursoSerializer
    mensagem_sucesso = 'Recurso obtido com sucesso.'


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Atualizar recurso',
    description='Atualiza parcialmente um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=AtualizarRecursoSerializer,
    responses={status.HTTP_200_OK: RecursoSerializer},
)
class AtualizarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPatchAPIView):
    """PATCH /cortex/infraestrutura/recursos/<pk>/"""
    queryset = Recurso.objects.select_related('sala').all()
    serializer_class = AtualizarRecursoSerializer
    mensagem_sucesso = 'Recurso atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        self.object.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RecursoSerializer(self.object, context={'request': request}).data,
        }


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Desativar recurso',
    description='Desativa um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Recurso desativado com sucesso.'}},
)
class DesativarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Recurso desativado com sucesso.'
    queryset = Recurso.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Reativar recurso',
    description='Reativa um recurso.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Recurso reativado com sucesso.'}},
)
class ReativarRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Recurso reativado com sucesso.'
    queryset = Recurso.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()


class ObterFotoRecursoView(AllowAnyMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/recursos/{pk}/foto/"""
    queryset = Recurso.objects.all()
    serializer_class = SerializerVazio

    @extend_schema(
        tags=['Infraestrutura · Recursos'],
        summary='Obter foto do recurso',
        description='''
        Retorna o arquivo de imagem da foto do recurso via proxy da API.

        **Permissões:** Público (AllowAny — não requer autenticação).

        O bucket S3 permanece privado; este endpoint faz o stream da imagem para o navegador.
        ''',
        responses={
            status.HTTP_200_OK: {
                'description': 'Imagem retornada com sucesso.',
                'content': {
                    'image/jpeg': {},
                    'image/png': {},
                    'image/webp': {},
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Recurso ou foto não encontrados.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        stream, content_type = self.get_object().business.obter_stream_foto()
        response = StreamingHttpResponse(stream, content_type=content_type)
        response['Cache-Control'] = 'public, max-age=86400'
        return response


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Enviar foto do recurso',
    description='''
    Faz upload da foto do recurso para o S3 e persiste a referência.

    A imagem deve estar na orientação retrato. O backend recorta o centro
    para 3:4 (largura:altura) sem deformar. Após o recorte, o mínimo é 480×640.

    **Limites do arquivo:** JPEG, PNG ou WebP, com tamanho máximo de 3 MB.

    **Permissões:** Capacidade `cadastrar` em Infraestrutura.
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'foto': {
                    'type': 'string',
                    'format': 'binary',
                    'description': (
                        'Arquivo de imagem (JPEG, PNG ou WebP, até 3 MB). '
                        'Retrato 3:4, mínimo 480×640 após recorte.'
                    ),
                }
            },
            'required': ['foto'],
        }
    },
    responses={
        status.HTTP_200_OK: RecursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Arquivo inválido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Recurso não encontrado.'},
    },
)
class EnviarFotoRecursoView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/recursos/{pk}/foto/"""
    queryset = Recurso.objects.select_related('sala').all()
    parser_classes = (MultiPartParser,)
    serializer_class = EnviarFotoRecursoSerializer
    mensagem_sucesso = 'Foto do recurso atualizada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        recurso = self.get_object()
        recurso.business.atualizar_foto(serializer_data['foto'])
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': RecursoSerializer(recurso, context={'request': request}).data,
        }


@extend_schema(
    tags=['Infraestrutura · Recursos'],
    summary='Remover foto do recurso',
    description='''
    Remove a foto do recurso e tenta apagar o arquivo correspondente no S3.

    **Permissões:** Capacidade `cadastrar` em Infraestrutura.
    ''',
    request=None,
    responses={
        status.HTTP_204_NO_CONTENT: {'description': 'Foto do recurso removida com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Recurso não encontrado.'},
    },
)
class RemoverFotoRecursoView(PodeCadastrarInfraestruturaMixin, BasicDeleteAPIView):
    """DELETE /cortex/infraestrutura/recursos/{pk}/foto/"""
    queryset = Recurso.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Foto do recurso removida com sucesso.'

    def do_action_delete(self, request, *args, **kwargs):
        self.object.business.remover_foto()
