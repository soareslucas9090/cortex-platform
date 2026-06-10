from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.serializers import Serializer

from AppCore.basics.mixins.mixins import IsAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
    BasicPatchAPIView,
)

from .models import Terceirizado
from .serializers import (
    TerceirizadoSerializer,
    CriarTerceirizadoSerializer,
    AtualizarTerceirizadoSerializer,
)


# Classe vazia para endpoints que não recebem body
class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Terceirizados'],
    summary='Listar terceirizados',
    description='''
    Lista todos os terceirizados cadastrados.

    **Permissões:** Apenas administradores.

    Query params apenas reduzem o conjunto, nunca expandem o acesso.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por status: true = Ativo, false = Inativo.',
        ),
        OpenApiParameter(
            'empresa', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por ID da empresa/instituição.',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome do terceirizado (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'cpf', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do CPF do terceirizado.',
        ),
        OpenApiParameter(
            'cargo', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por ID do cargo.',
        ),
        OpenApiParameter(
            'nome_cargo', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome do cargo (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'nome_empresa', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome da empresa/instituição (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: TerceirizadoSerializer(many=True),
    },
)
class ListarTerceirizadosView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = TerceirizadoSerializer
    mensagem_sucesso = 'Terceirizados listados com sucesso.'

    def get_queryset(self):
        qs = Terceirizado.objects.select_related('usuario', 'empresa_instituicao', 'cargo').all()

        if not self.request.user.is_staff:
            return qs.filter(usuario__id=self.request.user.id)

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')

        empresa = self.request.query_params.get('empresa')
        if empresa is not None:
            try:
                empresa_int = int(empresa)
                qs = qs.filter(empresa_instituicao_id=empresa_int)
            except (ValueError, TypeError):
                pass

        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(usuario__nome__unaccent__icontains=nome)

        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(usuario__cpf__unaccent__icontains=cpf)

        cargo = self.request.query_params.get('cargo')
        if cargo is not None:
            try:
                cargo_int = int(cargo)
                qs = qs.filter(cargo_id=cargo_int)
            except (ValueError, TypeError):
                pass

        nome_cargo = self.request.query_params.get('nome_cargo')
        if nome_cargo:
            qs = qs.filter(cargo__nome__unaccent__icontains=nome_cargo)

        nome_empresa = self.request.query_params.get('nome_empresa')
        if nome_empresa:
            qs = qs.filter(empresa_instituicao__nome__unaccent__icontains=nome_empresa)

        return qs


@extend_schema(
    tags=['Terceirizados'],
    summary='Criar terceirizado',
    description='''
    Cria um novo perfil de terceirizado para um usuário existente.

    **Permissões:** Apenas administradores.

    **Regras:**
    - O usuário informado deve existir e não possuir perfil de terceirizado.
    - A empresa/instituição informada deve existir e estar ativa.
    ''',
    request=CriarTerceirizadoSerializer,
    responses={
        status.HTTP_201_CREATED: TerceirizadoSerializer,
    },
)
class CriarTerceirizadoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarTerceirizadoSerializer
    mensagem_sucesso = 'Terceirizado criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        terceirizado = Terceirizado().business.criar_terceirizado(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': TerceirizadoSerializer(terceirizado).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Terceirizados'],
    summary='Detalhar terceirizado',
    description='''
    Exibe os detalhes de um terceirizado específico.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: TerceirizadoSerializer,
    },
)
class DetalharTerceirizadoView(IsAdminMixin, BasicRetrieveAPIView):
    queryset = Terceirizado.objects.select_related('usuario', 'empresa_instituicao').all()
    serializer_class = TerceirizadoSerializer
    mensagem_sucesso = 'Terceirizado detalhado com sucesso.'


@extend_schema(
    tags=['Terceirizados'],
    summary='Atualizar terceirizado',
    description='''
    Atualiza os dados de um terceirizado existente.

    **Permissões:** Apenas administradores.
    ''',
    request=AtualizarTerceirizadoSerializer,
    responses={
        status.HTTP_200_OK: TerceirizadoSerializer,
    },
)
class AtualizarTerceirizadoView(IsAdminMixin, BasicPatchAPIView):
    queryset = Terceirizado.objects.select_related('usuario', 'empresa_instituicao').all()
    serializer_class = AtualizarTerceirizadoSerializer
    mensagem_sucesso = 'Terceirizado atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        terceirizado = self.get_object()
        terceirizado.business.atualizar_dados(serializer_data)
        terceirizado.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': TerceirizadoSerializer(terceirizado).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Terceirizados'],
    summary='Desativar terceirizado',
    description='''
    Desativa o perfil de um terceirizado.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: TerceirizadoSerializer,
    },
)
class DesativarTerceirizadoView(IsAdminMixin, BasicPostAPIView):
    queryset = Terceirizado.objects.select_related('usuario', 'empresa_instituicao').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Terceirizado desativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        terceirizado = self.get_object()
        terceirizado.business.desativar()
        terceirizado.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': TerceirizadoSerializer(terceirizado).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Terceirizados'],
    summary='Reativar terceirizado',
    description='''
    Reativa o perfil de um terceirizado inativo.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: TerceirizadoSerializer,
    },
)
class ReativarTerceirizadoView(IsAdminMixin, BasicPostAPIView):
    queryset = Terceirizado.objects.select_related('usuario', 'empresa_instituicao').all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Terceirizado reativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        terceirizado = self.get_object()
        terceirizado.business.reativar()
        terceirizado.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': TerceirizadoSerializer(terceirizado).data,
            'status_code': status.HTTP_200_OK,
        }
