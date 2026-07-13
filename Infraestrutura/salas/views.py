from rest_framework import status

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicDeleteAPIView,
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from Infraestrutura.permissoes.access import PodeCadastrarInfraestruturaMixin

from .business import SalaBusiness, SalaSetorBusiness
from .models import Sala, SalaSetor
from .serializers import (
    AtualizarSalaSerializer,
    CriarSalaSerializer,
    CriarSalaSetorSerializer,
    SalaSerializer,
    SalaSetorSerializer,
    SerializerVazio,
)


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Listar salas',
    description='''
    Retorna a lista paginada de salas.

    **Permissões:** Qualquer usuário autenticado. Escrita exige capacidade `cadastrar`.
    ''',
    parameters=[
        OpenApiParameter('ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('nome', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('bloco_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: SalaSerializer(many=True)},
)
class ListarSalasView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/salas/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SalaSerializer
    mensagem_sucesso = 'Salas listadas com sucesso.'

    def get_queryset(self):
        qs = Sala.objects.select_related('bloco').all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        bloco_id = self.request.query_params.get('bloco_id')
        if bloco_id and bloco_id.isdigit():
            qs = qs.filter(bloco_id=bloco_id)
        return qs


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Criar sala',
    description='Cria uma nova sala vinculada a um bloco.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=CriarSalaSerializer,
    responses={status.HTTP_201_CREATED: SalaSerializer},
)
class CriarSalaView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/salas/"""
    serializer_class = CriarSalaSerializer
    mensagem_sucesso = 'Sala criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        sala = SalaBusiness().criar_sala(**serializer_data)
        sala = Sala.objects.select_related('bloco').get(pk=sala.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SalaSerializer(sala).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Detalhe da sala',
    description='Retorna os dados de uma sala.\n\n**Permissões:** Qualquer usuário autenticado.',
    responses={status.HTTP_200_OK: SalaSerializer},
)
class DetalheSalaView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/salas/<pk>/"""
    queryset = Sala.objects.select_related('bloco').all()
    serializer_class = SalaSerializer
    mensagem_sucesso = 'Sala obtida com sucesso.'


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Atualizar sala',
    description='Atualiza parcialmente uma sala.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=AtualizarSalaSerializer,
    responses={status.HTTP_200_OK: SalaSerializer},
)
class AtualizarSalaView(PodeCadastrarInfraestruturaMixin, BasicPatchAPIView):
    """PATCH /cortex/infraestrutura/salas/<pk>/"""
    queryset = Sala.objects.select_related('bloco').all()
    serializer_class = AtualizarSalaSerializer
    mensagem_sucesso = 'Sala atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        self.object.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SalaSerializer(self.object).data,
        }


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Desativar sala',
    description='Desativa uma sala.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Sala desativada com sucesso.'}},
)
class DesativarSalaView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/salas/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Sala desativada com sucesso.'
    queryset = Sala.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.desativar()


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Reativar sala',
    description='Reativa uma sala.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=None,
    responses={status.HTTP_200_OK: {'description': 'Sala reativada com sucesso.'}},
)
class ReativarSalaView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/salas/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Sala reativada com sucesso.'
    queryset = Sala.objects.all()

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.reativar()


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Listar vínculos sala–setor',
    description='''
    Retorna vínculos entre salas e setores.

    **Permissões:** Qualquer usuário autenticado. Escrita exige capacidade `cadastrar`.
    ''',
    parameters=[
        OpenApiParameter('sala_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('setor_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={status.HTTP_200_OK: SalaSetorSerializer(many=True)},
)
class ListarSalaSetorView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/salas-setores/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SalaSetorSerializer
    mensagem_sucesso = 'Vínculos sala–setor listados com sucesso.'

    def get_queryset(self):
        qs = SalaSetor.objects.select_related('sala__bloco', 'setor').all()
        sala_id = self.request.query_params.get('sala_id')
        if sala_id and sala_id.isdigit():
            qs = qs.filter(sala_id=sala_id)
        setor_id = self.request.query_params.get('setor_id')
        if setor_id and setor_id.isdigit():
            qs = qs.filter(setor_id=setor_id)
        return qs


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Criar vínculo sala–setor',
    description='Vincula uma sala a um setor.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    request=CriarSalaSetorSerializer,
    responses={status.HTTP_201_CREATED: SalaSetorSerializer},
)
class CriarSalaSetorView(PodeCadastrarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/salas-setores/"""
    serializer_class = CriarSalaSetorSerializer
    mensagem_sucesso = 'Vínculo sala–setor criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        vinculo = SalaSetorBusiness().criar_vinculo(**serializer_data)
        vinculo = SalaSetor.objects.select_related('sala__bloco', 'setor').get(pk=vinculo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SalaSetorSerializer(vinculo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Salas'],
    summary='Remover vínculo sala–setor',
    description='Remove um vínculo sala–setor.\n\n**Permissões:** Capacidade `cadastrar` em Infraestrutura.',
    responses={status.HTTP_204_NO_CONTENT: {'description': 'Vínculo removido com sucesso.'}},
)
class RemoverSalaSetorView(PodeCadastrarInfraestruturaMixin, BasicDeleteAPIView):
    """DELETE /cortex/infraestrutura/salas-setores/<pk>/"""
    queryset = SalaSetor.objects.all()

    def do_action_delete(self, request, *args, **kwargs):
        self.object.business.remover_vinculo()
