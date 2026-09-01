from drf_spectacular.utils import extend_schema
from rest_framework import status

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView

from .models import Strike
from .serializers import StrikeSerializer


@extend_schema(
    tags=['Transporte · Strikes'],
    summary='Listar strikes',
    description=(
        'Lista os strikes do aluno autenticado.\n\n'
        '**Permissões:** Autenticado. L1 vê somente os próprios strikes; L3 vê todos.'
    ),
    responses={
        status.HTTP_200_OK: StrikeSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarStrikesView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = StrikeSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Strikes listados com sucesso.'

    def get_queryset(self):
        return Strike().business.listar_para_usuario(self.request.user)
