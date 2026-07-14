from rest_framework import status

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from Infraestrutura.permissoes.access import PodeAutorizarInfraestruturaMixin

from .models import Autorizacao
from .serializers import (
    AutorizacaoSerializer,
    ConcederAutorizacaoSerializer,
    SerializerVazio,
)


def queryset_autorizacao_detalhado():
    return Autorizacao.objects.select_related(
        'beneficiario',
        'concedente',
        'sala',
        'recurso',
        'revogador',
    ).all()


@extend_schema(
    tags=['Infraestrutura · Autorizações'],
    summary='Listar autorizações',
    description='''
    Retorna autorizações de retirada por sala ou recurso.

    **Permissões:** Capacidade `autorizar` em Infraestrutura.
    ''',
    parameters=[
        OpenApiParameter('beneficiario_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('sala_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('recurso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('vigente', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: AutorizacaoSerializer(many=True)},
)
class ListarAutorizacoesView(PodeAutorizarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/autorizacoes/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = AutorizacaoSerializer
    mensagem_sucesso = 'Autorizações listadas com sucesso.'

    def get_queryset(self):
        beneficiario_id = self.request.query_params.get('beneficiario_id')
        sala_id = self.request.query_params.get('sala_id')
        recurso_id = self.request.query_params.get('recurso_id')
        vigente = self.request.query_params.get('vigente')

        kwargs = {}
        if beneficiario_id and beneficiario_id.isdigit():
            kwargs['beneficiario_id'] = int(beneficiario_id)
        if sala_id and sala_id.isdigit():
            kwargs['sala_id'] = int(sala_id)
        if recurso_id and recurso_id.isdigit():
            kwargs['recurso_id'] = int(recurso_id)
        if vigente is not None and vigente.lower() in ('true', 'false'):
            kwargs['vigente'] = vigente.lower() == 'true'

        return Autorizacao().helper.listar_para_filtros(**kwargs)


@extend_schema(
    tags=['Infraestrutura · Autorizações'],
    summary='Conceder autorização',
    description='''
    Concede autorização temporária ou permanente para sala ou recurso (XOR).

    **Permissões:** Capacidade `autorizar` em Infraestrutura.
    ''',
    request=ConcederAutorizacaoSerializer,
    responses={status.HTTP_201_CREATED: AutorizacaoSerializer},
)
class ConcederAutorizacaoView(PodeAutorizarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/autorizacoes/"""
    serializer_class = ConcederAutorizacaoSerializer
    mensagem_sucesso = 'Autorização concedida com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        autorizacao = Autorizacao().business.conceder_autorizacao(
            concedente=request.user,
            **serializer_data,
        )
        autorizacao = queryset_autorizacao_detalhado().get(pk=autorizacao.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AutorizacaoSerializer(autorizacao).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Autorizações'],
    summary='Detalhe da autorização',
    description='Retorna os dados de uma autorização.\n\n**Permissões:** Capacidade `autorizar` em Infraestrutura.',
    responses={status.HTTP_200_OK: AutorizacaoSerializer},
)
class DetalheAutorizacaoView(PodeAutorizarInfraestruturaMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/autorizacoes/<pk>/"""
    queryset = queryset_autorizacao_detalhado()
    serializer_class = AutorizacaoSerializer
    mensagem_sucesso = 'Autorização obtida com sucesso.'


@extend_schema(
    tags=['Infraestrutura · Autorizações'],
    summary='Revogar autorização',
    description='Revoga uma autorização vigente.\n\n**Permissões:** Capacidade `autorizar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: AutorizacaoSerializer},
)
class RevogarAutorizacaoView(PodeAutorizarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/autorizacoes/<pk>/revogar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Autorização revogada com sucesso.'
    queryset = Autorizacao.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        autorizacao = self.get_object()
        autorizacao.business.revogar(request.user)
        autorizacao = queryset_autorizacao_detalhado().get(pk=autorizacao.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AutorizacaoSerializer(autorizacao).data,
        }
