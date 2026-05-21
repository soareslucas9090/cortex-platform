import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin
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
    tags=['VÃ­nculos de Setor'],
    summary='Listar vÃ­nculos do setor',
    description='''
    Retorna a lista paginada de vÃ­nculos de um setor especÃ­fico.

    **PermissÃµes:** Apenas administradores.

    **Query params apenas reduzem o conjunto â€” nunca expandem o acesso.**
    ''',
    parameters=[
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da pÃ¡gina (1â€“100, padrÃ£o 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: SetorVinculoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor nÃ£o encontrado.'},
    },
)
class ListarVinculosView(IsAdminMixin, BasicGetAPIView):
    """GET /organizacional/setores/<setor_pk>/vinculos/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SetorVinculoSerializer
    mensagem_sucesso = 'VÃ­nculos listados com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])


@extend_schema(
    tags=['VÃ­nculos de Setor'],
    summary='Criar vÃ­nculo no setor',
    description='''
    Vincula um usuÃ¡rio ao setor com uma funÃ§Ã£o obrigatÃ³ria.

    **Regras:**
    - Setor e funÃ§Ã£o devem estar ativos.
    - A combinaÃ§Ã£o (usuÃ¡rio, setor, funÃ§Ã£o) deve ser Ãºnica.
    - Um usuÃ¡rio pode ter mÃºltiplos vÃ­nculos com setores ou funÃ§Ãµes diferentes.

    **PermissÃµes:** Apenas administradores.
    ''',
    request=CriarVinculoSerializer,
    responses={
        status.HTTP_201_CREATED: SetorVinculoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados invÃ¡lidos, setor/funÃ§Ã£o inativo ou vÃ­nculo duplicado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Setor nÃ£o encontrado.'},
    },
)
class CriarVinculoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/"""
    serializer_class = CriarVinculoSerializer
    mensagem_sucesso = 'VÃ­nculo criado com sucesso.'

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
    tags=['VÃ­nculos de Setor'],
    summary='Encerrar vÃ­nculo',
    description='Remove o vÃ­nculo do usuÃ¡rio com o setor. Bloqueado se for o Ãºnico responsÃ¡vel.\n\n**PermissÃµes:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'VÃ­nculo encerrado com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'OperaÃ§Ã£o bloqueada: setor perderia seu Ãºnico responsÃ¡vel.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'VÃ­nculo nÃ£o encontrado.'},
    },
)
class EncerrarVinculoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/encerrar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'VÃ­nculo encerrado com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.encerrar_vinculo()


@extend_schema(
    tags=['VÃ­nculos de Setor'],
    summary='Definir vÃ­nculo como responsÃ¡vel',
    description='''
    Marca o vÃ­nculo como responsÃ¡vel pelo setor.

    **Nota:** a validaÃ§Ã£o de elegibilidade (responsÃ¡vel deve ser Servidor) serÃ¡
    implementada em etapa futura junto ao domÃ­nio PessoasInstitucionais.

    **PermissÃµes:** Apenas administradores.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'ResponsÃ¡vel definido com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Setor inativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'VÃ­nculo nÃ£o encontrado.'},
    },
)
class DefinirResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/definir-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'ResponsÃ¡vel definido com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.definir_como_responsavel()


@extend_schema(
    tags=['VÃ­nculos de Setor'],
    summary='Remover responsabilidade do vÃ­nculo',
    description='Remove a marcaÃ§Ã£o de responsÃ¡vel do vÃ­nculo. Bloqueado se for o Ãºnico responsÃ¡vel do setor.\n\n**PermissÃµes:** Apenas administradores.',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Responsabilidade removida com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'OperaÃ§Ã£o bloqueada: setor perderia seu Ãºnico responsÃ¡vel.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'VÃ­nculo nÃ£o encontrado.'},
    },
)
class RemoverResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/remover-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Responsabilidade removida com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        self.get_object().business.remover_responsabilidade()


@extend_schema(
    tags=['VÃ­nculos de Setor'],
    summary='Atualizar funÃ§Ã£o do vÃ­nculo',
    description='Substitui a funÃ§Ã£o exercida no vÃ­nculo. A nova funÃ§Ã£o deve estar ativa e a combinaÃ§Ã£o nÃ£o deve ser duplicada.\n\n**PermissÃµes:** Apenas administradores.',
    request=AtualizarVinculoFuncaoSerializer,
    responses={
        status.HTTP_200_OK: {'description': 'FunÃ§Ã£o do vÃ­nculo atualizada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'FunÃ§Ã£o inativa ou vÃ­nculo duplicado resultante.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'NÃ£o autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissÃ£o de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'VÃ­nculo nÃ£o encontrado.'},
    },
)
class AtualizarVinculoFuncaoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /organizacional/setores/<setor_pk>/vinculos/<pk>/funcao/"""
    serializer_class = AtualizarVinculoFuncaoSerializer
    mensagem_sucesso = 'FunÃ§Ã£o do vÃ­nculo atualizada com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        self.object.business.atualizar_funcao(serializer_data['funcao'])

logger = logging.getLogger(__name__)
