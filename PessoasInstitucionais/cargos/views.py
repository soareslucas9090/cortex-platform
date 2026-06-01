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

from .models import Cargo
from .serializers import CargoSerializer, CriarCargoSerializer, AtualizarCargoSerializer


@extend_schema(
    tags=['Cargos'],
    summary='Listar cargos',
    description='''
    Lista todos os cargos cadastrados.
    
    **Permissões:** Apenas administradores.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por status: true = Ativo, false = Inativo.',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: CargoSerializer(many=True),
    }
)
class ListarCargosView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = CargoSerializer
    mensagem_sucesso = 'Cargos listados com sucesso.'

    def get_queryset(self):
        qs = Cargo.objects.all()
        
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
            
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
            
        return qs


@extend_schema(
    tags=['Cargos'],
    summary='Criar cargo',
    description='''
    Cria um novo cargo.
    
    **Permissões:** Apenas administradores.
    ''',
    request=CriarCargoSerializer,
    responses={
        status.HTTP_201_CREATED: CargoSerializer,
    }
)
class CriarCargoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarCargoSerializer
    mensagem_sucesso = 'Cargo criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        cargo = Cargo().business.criar_cargo(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CargoSerializer(cargo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Cargos'],
    summary='Detalhar cargo',
    description='''
    Exibe os detalhes de um cargo específico.
    
    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: CargoSerializer,
    }
)
class DetalharCargoView(IsAdminMixin, BasicRetrieveAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    mensagem_sucesso = 'Cargo detalhado com sucesso.'


@extend_schema(
    tags=['Cargos'],
    summary='Atualizar cargo',
    description='''
    Atualiza os dados de um cargo existente.
    
    **Permissões:** Apenas administradores.
    ''',
    request=AtualizarCargoSerializer,
    responses={
        status.HTTP_200_OK: CargoSerializer,
    }
)
class AtualizarCargoView(IsAdminMixin, BasicPatchAPIView):
    queryset = Cargo.objects.all()
    serializer_class = AtualizarCargoSerializer
    mensagem_sucesso = 'Cargo atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        cargo = self.get_object()
        cargo.business.atualizar_dados(serializer_data)
        cargo.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CargoSerializer(cargo).data,
            'status_code': status.HTTP_200_OK,
        }


# Classe vazia temporária para usar no schema do DRF Spectacular
class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Cargos'],
    summary='Desativar cargo',
    description='''
    Desativa um cargo.
    
    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: CargoSerializer,
    }
)
class DesativarCargoView(IsAdminMixin, BasicPostAPIView):
    queryset = Cargo.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Cargo desativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        cargo = self.get_object()
        cargo.business.desativar()
        cargo.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CargoSerializer(cargo).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Cargos'],
    summary='Reativar cargo',
    description='''
    Reativa um cargo inativo.
    
    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: CargoSerializer,
    }
)
class ReativarCargoView(IsAdminMixin, BasicPostAPIView):
    queryset = Cargo.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Cargo reativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        cargo = self.get_object()
        cargo.business.reativar()
        cargo.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CargoSerializer(cargo).data,
            'status_code': status.HTTP_200_OK,
        }
