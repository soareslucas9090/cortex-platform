from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicPatchAPIView

from .models import Notificacao
from .serializers import (
    ContadorNaoLidasSerializer,
    NotificacaoSerializer,
    SerializerVazio,
)

PERMISSAO_INBOX = (
    '**Permissões:** Usuário autenticado; somente a própria inbox '
    '(L2/L3 não leem caixa alheia).'
)


@extend_schema(
    tags=['Notificações'],
    summary='Listar notificações da inbox',
    description=f'''
    Lista paginada das notificações do usuário autenticado, ordenadas da mais recente.

    Filtros opcionais: `lida` (`true`/`false`) e `tipo` (código estável).

    {PERMISSAO_INBOX}
    ''',
    parameters=[
        OpenApiParameter(
            'lida',
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por lidas (`true`) ou não lidas (`false`).',
        ),
        OpenApiParameter(
            'tipo',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra pelo código de tipo da notificação.',
        ),
        OpenApiParameter(
            'paginacao',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='Itens por página (1–100).',
        ),
    ],
    responses={
        status.HTTP_200_OK: NotificacaoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarNotificacoesView(IsAuthenticatedMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = NotificacaoSerializer
    mensagem_sucesso = 'Notificações listadas com sucesso.'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notificacao.objects.none()

        params = self.request.query_params
        lida = None
        lida_param = params.get('lida')
        if lida_param is not None and lida_param.lower() in ('true', 'false'):
            lida = lida_param.lower() == 'true'

        tipo = params.get('tipo') or None

        return Notificacao().business.listar_para_usuario(
            self.request.user,
            lida=lida,
            tipo=tipo,
        )


@extend_schema(
    tags=['Notificações'],
    summary='Contador de notificações não lidas',
    description=f'''
    Retorna a quantidade de notificações com `lida_em` nulo do usuário autenticado.

    {PERMISSAO_INBOX}
    ''',
    responses={
        status.HTTP_200_OK: ContadorNaoLidasSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ContadorNaoLidasView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = SerializerVazio
    pagination_class = None
    mensagem_sucesso = 'Contador de não lidas obtido com sucesso.'

    def get(self, request, *args, **kwargs):
        quantidade = Notificacao().business.contar_nao_lidas(request.user.pk)
        return Response({
            'status': 'success',
            'mensagem': self.mensagem_sucesso,
            'dados': {'quantidade': quantidade},
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Notificações'],
    summary='Marcar notificação como lida',
    description=f'''
    Define `lida_em` para o instante atual se ainda não estiver lida. Idempotente.

    {PERMISSAO_INBOX}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: {'description': 'Notificação marcada como lida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Notificação inexistente ou de outro usuário.'},
    },
)
class MarcarNotificacaoLidaView(IsAuthenticatedMixin, BasicPatchAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Notificação marcada como lida com sucesso.'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notificacao.objects.none()
        return Notificacao().business.listar_para_usuario(self.request.user)

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.marcar_lida()


@extend_schema(
    tags=['Notificações'],
    summary='Marcar todas as notificações como lidas',
    description=f'''
    Marca como lidas todas as notificações não lidas do usuário autenticado.

    {PERMISSAO_INBOX}
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: {'description': 'Notificações atualizadas.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class MarcarTodasLidasView(IsAuthenticatedMixin, BasicPatchAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Notificações marcadas como lidas com sucesso.'

    def get_object(self):
        return Notificacao()

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        atualizadas = Notificacao().business.marcar_todas_lidas(request.user.pk)
        return {'dados': {'atualizadas': atualizadas}}
