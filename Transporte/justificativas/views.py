from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .models import Justificativa
from .serializers import (
    AnalisarJustificativaSerializer,
    JustificativaDetalheSerializer,
    JustificativaSerializer,
)


@extend_schema(
    tags=['Transporte · Justificativas'],
    summary='Listar justificativas',
    description=(
        'Lista justificativas do aluno autenticado.\n\n'
        '**Permissões:** Autenticado. L1 vê somente as próprias justificativas; L3 vê todas.'
    ),
    responses={
        status.HTTP_200_OK: JustificativaSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarJustificativasView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = JustificativaSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Justificativas listadas com sucesso.'

    def get_queryset(self):
        return Justificativa().business.listar_para_usuario(self.request.user)


@extend_schema(
    tags=['Transporte · Justificativas'],
    summary='Detalhar justificativa',
    description=(
        'Retorna os dados de uma justificativa específica.\n\n'
        '**Permissões:** Autenticado. L1 vê somente justificativa própria; L3 vê qualquer uma.'
    ),
    responses={
        status.HTTP_200_OK: JustificativaDetalheSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Justificativa não encontrada no escopo.'},
    },
)
class DetalharJustificativaView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    serializer_class = JustificativaDetalheSerializer
    mensagem_sucesso = 'Justificativa obtida com sucesso.'

    def get_queryset(self):
        return Justificativa().business.listar_para_usuario(self.request.user)


class AnalisarJustificativaView(IsAdminMixin, BasicPostAPIView):
    serializer_class = AnalisarJustificativaSerializer
    aprovar = None

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        justificativa = Justificativa().business.obter_por_id(kwargs['pk'])
        justificativa = justificativa.business.analisar(
            aprovar=self.aprovar,
            usuario=request.user,
            observacao_analise=serializer_data.get('observacao_analise', ''),
        )
        return {'dados': JustificativaSerializer(justificativa).data}


@extend_schema(
    tags=['Transporte · Justificativas'],
    summary='Aprovar justificativa',
    description=(
        'Aprova a justificativa e faz o strike deixar de contar.\n\n'
        '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
    ),
    request=AnalisarJustificativaSerializer,
    responses={
        status.HTTP_200_OK: JustificativaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Justificativa não está pendente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Justificativa não encontrada.'},
    },
)
class AprovarJustificativaView(AnalisarJustificativaView):
    aprovar = True
    mensagem_sucesso = 'Justificativa aprovada com sucesso.'


@extend_schema(
    tags=['Transporte · Justificativas'],
    summary='Rejeitar justificativa',
    description=(
        'Rejeita a justificativa e mantém o strike ativo.\n\n'
        '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
    ),
    request=AnalisarJustificativaSerializer,
    responses={
        status.HTTP_200_OK: JustificativaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Justificativa não está pendente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Justificativa não encontrada.'},
    },
)
class RejeitarJustificativaView(AnalisarJustificativaView):
    aprovar = False
    mensagem_sucesso = 'Justificativa rejeitada com sucesso.'
