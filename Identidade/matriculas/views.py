import logging

from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin, IsOwnerOrAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicPostAPIView

from .choices import SituacaoMatricula
from .models import Matricula
from .serializers import AdicionarMatriculaSerializer, MatriculaSerializer, SerializerVazio

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Identidade'],
    summary='Listar matrículas do usuário',
    description='''
    Retorna a lista de matrículas de um usuário específico.

    **Permissões:** O próprio usuário ou administradores.

    **Query params:**
    - `situacao` (int, opcional): filtra por situação — `1` (Ativa) ou `2` (Inativa).
      Omitindo, retorna todas.
    - `matricula` (str, opcional): filtra pela string da matrícula.
    - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.

    **Segurança:** os resultados já estão restritos ao usuário da URL — query params
    apenas reduzem o conjunto, nunca expandem o acesso.
    ''',
    parameters=[
        OpenApiParameter(
            'situacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False,
            description='Filtra por situação: 1 = Ativa, 2 = Inativa.',
            enum=[1, 2],
        ),
        OpenApiParameter(
            'matricula', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra pela string da matrícula.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: MatriculaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ListarMatriculasView(IsOwnerOrAdminMixin, BasicGetAPIView):
    """GET /cortex/identidade/usuarios/{usuario_pk}/matriculas/"""
    serializer_class = MatriculaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Matrículas listadas com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def validate_get(self, request, *args, **kwargs):
        from Identidade.usuarios.models import Usuario
        Usuario.objects.get(pk=self.kwargs['usuario_pk'])
        self.verificar_acesso_usuario(request, self.kwargs['usuario_pk'])

    def get_queryset(self):
        qs = Matricula.objects.filter(usuario_id=self.kwargs['usuario_pk'])
        situacao = self.request.query_params.get('situacao')
        if situacao is not None:
            try:
                situacao_int = int(situacao)
                if situacao_int in SituacaoMatricula.values:
                    qs = qs.filter(situacao=situacao_int)
            except (ValueError, TypeError):
                pass
                
        matricula = self.request.query_params.get('matricula')
        if matricula:
            qs = qs.filter(matricula__unaccent__icontains=matricula)
            
        return qs


@extend_schema(
    tags=['Identidade'],
    summary='Adicionar matrícula ao usuário',
    description='''
    Adiciona uma nova matrícula (número) ao usuário.

    **Permissões:** Apenas administradores.
    ''',
    request=AdicionarMatriculaSerializer,
    responses={
        status.HTTP_201_CREATED: MatriculaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Matrícula duplicada ou dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AdicionarMatriculaView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{usuario_pk}/matriculas/"""
    serializer_class = AdicionarMatriculaSerializer
    mensagem_sucesso = 'Matrícula adicionada com sucesso.'

    def do_action_post(self, serializer_data, request, **kwargs):
        from django.shortcuts import get_object_or_404
        from Identidade.usuarios.models import Usuario
        usuario = get_object_or_404(Usuario, pk=self.kwargs['usuario_pk'])
        matricula = usuario.business.adicionar_matricula(serializer_data['matricula'])
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': MatriculaSerializer(matricula).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Desativar matrícula',
    description='''
    Marca uma matrícula do usuário como inativa.

    **Permissões:** Apenas administradores.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Matrícula desativada com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário ou matrícula não encontrados.'},
    },
)
class DesativarMatriculaView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{usuario_pk}/matriculas/{pk}/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Matrícula desativada com sucesso.'

    def get_queryset(self):
        return Matricula.objects.filter(usuario_id=self.kwargs['usuario_pk'])

    def do_action_post(self, serializer_data, request, **kwargs):
        self.get_object().business.desativar()
