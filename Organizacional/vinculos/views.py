import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin, IsOwnerOrAdminMixin
from Identidade.usuarios.access import escopar_queryset_cortex
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
)

from .business import SetorVinculoBusiness
from .models import SetorVinculo
from .serializers import (
    AtualizarVinculoFuncaoSerializer,
    CriarVinculoSerializer,
    SerializerVazio,
    SetorVinculoSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Listar vínculos do setor',
    description='''
    Retorna a lista paginada de vínculos de um setor específico.

    **Permissões:** Autenticado. L2+ lista todos os vínculos do setor; L1 vê apenas os próprios.

    **Query params apenas reduzem o conjunto â€” nunca expandem o acesso.**
    ''',
    parameters=[
        OpenApiParameter(
            'nome_usuario', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do usuário (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'cpf_usuario', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do CPF do usuário.',
        ),
        OpenApiParameter(
            'papel_funcao', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do papel/função (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'responsavel', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por vínculos marcados como responsável (true) ou não (false).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1â€“100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: SetorVinculoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class ListarVinculosView(IsOwnerOrAdminMixin, BasicGetAPIView):
    """GET /cortex/organizacional/setores/<setor_pk>/vinculos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SetorVinculoSerializer
    mensagem_sucesso = 'Vínculos listados com sucesso.'

    def get_queryset(self):
        qs = SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])
        qs = escopar_queryset_cortex(self.request.user, qs, campo_dono='usuario')
        
        nome_usuario = self.request.query_params.get('nome_usuario')
        if nome_usuario:
            qs = qs.filter(usuario__nome__unaccent__icontains=nome_usuario)
            
        cpf_usuario = self.request.query_params.get('cpf_usuario')
        if cpf_usuario:
            qs = qs.filter(usuario__cpf__unaccent__icontains=cpf_usuario)
            
        papel_funcao = self.request.query_params.get('papel_funcao')
        if papel_funcao:
            qs = qs.filter(funcao__papel_funcao__unaccent__icontains=papel_funcao)
            
        responsavel = self.request.query_params.get('responsavel')
        if responsavel is not None and responsavel.lower() in ('true', 'false'):
            qs = qs.filter(responsavel=responsavel.lower() == 'true')
            
        return qs


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Criar vínculo no setor',
    description='''
    Vincula um usuário ao setor com uma função obrigatória.

    **Regras:**
    - Setor e função devem estar ativos.
    - A combinação (usuário, setor, função) deve ser única.
    - Um usuário pode ter múltiplos vínculos com setores ou funções diferentes.

    **Permissões:** Autenticado. L2+ lista todos os vínculos do setor; L1 vê apenas os próprios.
    ''',
    request=CriarVinculoSerializer,
    responses={
        status.HTTP_201_CREATED: SetorVinculoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos, setor/função inativo ou vínculo duplicado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
    },
)
class CriarVinculoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<setor_pk>/vinculos/"""
    serializer_class = CriarVinculoSerializer
    mensagem_sucesso = 'Vínculo criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        vinculo = SetorVinculoBusiness().criar_vinculo_no_setor(
            usuario=serializer_data['usuario'],
            setor_pk=self.kwargs['setor_pk'],
            funcao=serializer_data['funcao'],
            responsavel=serializer_data.get('responsavel', False),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SetorVinculoSerializer(vinculo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Encerrar vínculo',
    description='Remove o vínculo do usuário com o setor. Bloqueado se for o único responsável.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Vínculo encerrado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Operação bloqueada: setor perderia seu único responsável.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    },
)
class EncerrarVinculoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<setor_pk>/vinculos/<pk>/encerrar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Vínculo encerrado com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.encerrar_vinculo()


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Definir vínculo como responsável',
    description='''
    Marca o vínculo como responsável pelo setor.

    **Regras:**
    - O setor deve estar ativo.
    - O usuário do vínculo deve possuir perfil de servidor ativo.

    Apenas servidores ativos podem ocupar a responsabilidade principal de um setor.

    **Permissões:** Autenticado. L2+ lista todos os vínculos do setor; L1 vê apenas os próprios.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Responsável definido com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Setor inativo ou usuário não é servidor ativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    },
)
class DefinirResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<setor_pk>/vinculos/<pk>/definir-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Responsável definido com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.definir_como_responsavel()


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Remover responsabilidade do vínculo',
    description='Remove a marcação de responsável do vínculo. Bloqueado se for o único responsável do setor.\n\n**Permissões:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Responsabilidade removida com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Operação bloqueada: setor perderia seu único responsável.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    },
)
class RemoverResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/organizacional/setores/<setor_pk>/vinculos/<pk>/remover-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Responsabilidade removida com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.remover_responsabilidade()


@extend_schema(
    tags=['Vínculos de Setor'],
    summary='Atualizar função do vínculo',
    description='Substitui a função exercida no vínculo. A nova função deve estar ativa e a combinação não deve ser duplicada.\n\n**Permissões:** Apenas administradores.',
    request=AtualizarVinculoFuncaoSerializer,
    responses={
        status.HTTP_200_OK: {'description': 'Função do vínculo atualizada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Função inativa ou vínculo duplicado resultante.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    },
)
class AtualizarVinculoFuncaoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/organizacional/setores/<setor_pk>/vinculos/<pk>/funcao/"""
    serializer_class = AtualizarVinculoFuncaoSerializer
    mensagem_sucesso = 'Função do vínculo atualizada com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_funcao(serializer_data['funcao'])

logger = logging.getLogger(__name__)
