from drf_spectacular.utils import extend_schema
from rest_framework import status

from Academico.alunos.models import Aluno
from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from Transporte.justificativas.models import Justificativa
from Transporte.justificativas.serializers import (
    CriarJustificativaSerializer,
    JustificativaSerializer,
)

from .business import BloqueioBusiness
from .serializers import BloqueioDetalheSerializer, BloqueioSerializer


@extend_schema(
    tags=['Transporte · Bloqueios'],
    summary='Listar alunos bloqueados',
    description=(
        'Lista alunos bloqueados no transporte universitário.\n\n'
        '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
    ),
    responses={
        status.HTTP_200_OK: BloqueioSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
    },
)
class ListarBloqueiosView(IsAdminMixin, BasicGetAPIView):
    serializer_class = BloqueioSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Bloqueios listados com sucesso.'

    def get_queryset(self):
        return BloqueioBusiness(Aluno()).listar_bloqueados(self.request.user)


@extend_schema(
    tags=['Transporte · Bloqueios'],
    summary='Detalhar bloqueio',
    description=(
        'Retorna os dados de um aluno bloqueado, incluindo strikes e justificativa pendente.\n\n'
        '**Permissões:** L3 (EDITAR_TUDO) — perfil TI / administradores.'
    ),
    responses={
        status.HTTP_200_OK: BloqueioDetalheSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Acesso administrativo obrigatório.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Bloqueio não encontrado.'},
    },
)
class DetalharBloqueioView(IsAdminMixin, BasicRetrieveAPIView):
    serializer_class = BloqueioDetalheSerializer
    mensagem_sucesso = 'Bloqueio obtido com sucesso.'

    def get_object(self):
        return BloqueioBusiness(Aluno()).obter_detalhe(
            self.kwargs['aluno_pk'],
            self.request.user,
        )


@extend_schema(
    tags=['Transporte · Bloqueios'],
    summary='Enviar justificativa de bloqueio',
    description=(
        'Envia uma justificativa cobrindo todos os strikes ativos do aluno bloqueado.\n\n'
        '**Permissões:** L1 (EDITAR_EU) — somente o próprio aluno bloqueado.'
    ),
    request=CriarJustificativaSerializer,
    responses={
        status.HTTP_201_CREATED: JustificativaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Aluno não bloqueado ou texto inválido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class CriarJustificativaBloqueioView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = CriarJustificativaSerializer
    mensagem_sucesso = 'Justificativa enviada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        justificativa = Justificativa().business.criar_justificativa(
            usuario=request.user,
            texto=serializer_data['texto'],
        )
        return {
            'dados': JustificativaSerializer(justificativa).data,
            'status_code': status.HTTP_201_CREATED,
        }
