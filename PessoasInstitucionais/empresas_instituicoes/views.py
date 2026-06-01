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

from .models import EmpresaInstituicao
from .serializers import (
    EmpresaInstituicaoSerializer,
    CriarEmpresaInstituicaoSerializer,
    AtualizarEmpresaInstituicaoSerializer,
)


# Classe vazia para endpoints que não recebem body
class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Listar empresas/instituições',
    description='''
    Lista todas as empresas/instituições cadastradas.

    **Permissões:** Apenas administradores.

    Query params apenas reduzem o conjunto, nunca expandem o acesso.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por status: true = Ativa, false = Inativa.',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'cnpj', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do CNPJ.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: EmpresaInstituicaoSerializer(many=True),
    },
)
class ListarEmpresasView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = EmpresaInstituicaoSerializer
    mensagem_sucesso = 'Empresas/instituições listadas com sucesso.'

    def get_queryset(self):
        qs = EmpresaInstituicao.objects.all()
        
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
            
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
            
        cnpj = self.request.query_params.get('cnpj')
        if cnpj:
            qs = qs.filter(cnpj__unaccent__icontains=cnpj)
            
        return qs


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Criar empresa/instituição',
    description='''
    Cria uma nova empresa/instituição.

    **Permissões:** Apenas administradores.
    ''',
    request=CriarEmpresaInstituicaoSerializer,
    responses={
        status.HTTP_201_CREATED: EmpresaInstituicaoSerializer,
    },
)
class CriarEmpresaView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarEmpresaInstituicaoSerializer
    mensagem_sucesso = 'Empresa/instituição criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        empresa = EmpresaInstituicao().business.criar_empresa(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmpresaInstituicaoSerializer(empresa).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Detalhar empresa/instituição',
    description='''
    Exibe os detalhes de uma empresa/instituição específica.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: EmpresaInstituicaoSerializer,
    },
)
class DetalharEmpresaView(IsAdminMixin, BasicRetrieveAPIView):
    queryset = EmpresaInstituicao.objects.all()
    serializer_class = EmpresaInstituicaoSerializer
    mensagem_sucesso = 'Empresa/instituição detalhada com sucesso.'


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Atualizar empresa/instituição',
    description='''
    Atualiza os dados de uma empresa/instituição existente.

    **Permissões:** Apenas administradores.
    ''',
    request=AtualizarEmpresaInstituicaoSerializer,
    responses={
        status.HTTP_200_OK: EmpresaInstituicaoSerializer,
    },
)
class AtualizarEmpresaView(IsAdminMixin, BasicPatchAPIView):
    queryset = EmpresaInstituicao.objects.all()
    serializer_class = AtualizarEmpresaInstituicaoSerializer
    mensagem_sucesso = 'Empresa/instituição atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        empresa = self.get_object()
        empresa.business.atualizar_dados(serializer_data)
        empresa.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmpresaInstituicaoSerializer(empresa).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Desativar empresa/instituição',
    description='''
    Desativa uma empresa/instituição.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: EmpresaInstituicaoSerializer,
    },
)
class DesativarEmpresaView(IsAdminMixin, BasicPostAPIView):
    queryset = EmpresaInstituicao.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Empresa/instituição desativada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        empresa = self.get_object()
        empresa.business.desativar()
        empresa.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmpresaInstituicaoSerializer(empresa).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Empresas/Instituições'],
    summary='Reativar empresa/instituição',
    description='''
    Reativa uma empresa/instituição inativa.

    **Permissões:** Apenas administradores.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: EmpresaInstituicaoSerializer,
    },
)
class ReativarEmpresaView(IsAdminMixin, BasicPostAPIView):
    queryset = EmpresaInstituicao.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Empresa/instituição reativada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        empresa = self.get_object()
        empresa.business.reativar()
        empresa.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmpresaInstituicaoSerializer(empresa).data,
            'status_code': status.HTTP_200_OK,
        }
