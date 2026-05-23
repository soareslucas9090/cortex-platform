from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status

from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
    BasicPatchAPIView,
)
from AppCore.basics.mixins.mixins import IsAdminMixin
from .models import Aluno
from .serializers import AlunoSerializer, CriarAlunoSerializer, AtualizarAlunoSerializer


@extend_schema(
    tags=['Alunos'],
    summary='Listar alunos',
    description='Retorna a lista de alunos cadastrados. Apenas administradores.',
    responses={200: AlunoSerializer(many=True)},
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra alunos ativos/inativos.'
        ),
        OpenApiParameter(
            'situacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Filtra pela situação do aluno.'
        ),
    ]
)
class ListarAlunosView(IsAdminMixin, BasicGetAPIView):
    serializer_class = AlunoSerializer
    
    def get_queryset(self):
        qs = Aluno.objects.all().select_related('usuario')
        
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
            
        situacao = self.request.query_params.get('situacao')
        if situacao is not None:
            try:
                situacao_int = int(situacao)
                qs = qs.filter(situacao=situacao_int)
            except (ValueError, TypeError):
                pass
                
        return qs


@extend_schema(
    tags=['Alunos'],
    summary='Criar aluno',
    description='Cria um novo perfil de aluno para um usuário existente. Apenas administradores.',
    request=CriarAlunoSerializer,
    responses={201: AlunoSerializer},
)
class CriarAlunoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarAlunoSerializer
    mensagem_sucesso = 'Aluno criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        # Create an instance to call business (since ModelInstanceBusiness needs an instance or class)
        # However, for creation we typically use an empty instance or call it on the class if possible.
        # But according to standard usage, we just use a temporary instance or get_business on the model.
        # Actually ModelBusinessMixin provides a class method `get_business_class` or we can just instantiate it.
        # Let's instantiate a temporary empty model to access business, or just instantiate Business directly.
        aluno = Aluno().business.criar_aluno(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoSerializer(aluno).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Alunos'],
    summary='Detalhar aluno',
    description='Retorna os detalhes de um aluno. Apenas administradores.',
    responses={200: AlunoSerializer},
)
class DetalharAlunoView(IsAdminMixin, BasicRetrieveAPIView):
    serializer_class = AlunoSerializer
    queryset = Aluno.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'usuario_id'


@extend_schema(
    tags=['Alunos'],
    summary='Atualizar aluno',
    description='Atualiza os dados de um aluno existente. Apenas administradores.',
    request=AtualizarAlunoSerializer,
    responses={200: AlunoSerializer},
)
class AtualizarAlunoView(IsAdminMixin, BasicPatchAPIView):
    serializer_class = AtualizarAlunoSerializer
    queryset = Aluno.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'usuario_id'
    mensagem_sucesso = 'Aluno atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        aluno = self.get_object().business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoSerializer(aluno).data,
            'status_code': status.HTTP_200_OK,
        }
