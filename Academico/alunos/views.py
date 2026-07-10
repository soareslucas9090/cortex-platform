from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status

from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
    BasicPatchAPIView,
)
from AppCore.basics.mixins.mixins import IsOwnerOrAdminMixin, IsAdminMixin
from Identidade.usuarios.access import escopar_queryset_cortex
from .models import Aluno
from .serializers import AlunoSerializer, CriarAlunoSerializer, AtualizarAlunoSerializer


@extend_schema(
    tags=['Alunos'],
    summary='Listar alunos',
    description='''
    Retorna a lista de alunos cadastrados.

    **Permissões:** Autenticado. L2+ (LER_TUDO) lista todos; L1 (EDITAR_EU) vê apenas o próprio.

    **Filtros:** Os query params apenas reduzem o conjunto de resultados — nunca expandem o acesso.
    ''',
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
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do aluno (ignora acentos e maiúsculas).'
        ),
        OpenApiParameter(
            'cpf', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do CPF do aluno.'
        ),
    ]
)
class ListarAlunosView(IsOwnerOrAdminMixin, BasicGetAPIView):
    serializer_class = AlunoSerializer
    
    def get_queryset(self):
        qs = Aluno.objects.all().select_related('usuario')
        qs = escopar_queryset_cortex(self.request.user, qs, campo_dono='usuario')
        
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
                
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(usuario__nome__unaccent__icontains=nome)
            
        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(usuario__cpf__unaccent__icontains=cpf)
                
        return qs


@extend_schema(
    tags=['Alunos'],
    summary='Criar aluno',
    description='''
    Cria um novo perfil de aluno para um usuário existente.

    **Permissões:** L3 (EDITAR_TUDO) — administradores.
    ''',
    request=CriarAlunoSerializer,
    responses={201: AlunoSerializer},
)
class CriarAlunoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarAlunoSerializer
    mensagem_sucesso = 'Aluno criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        aluno = Aluno().business.criar_aluno(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoSerializer(aluno).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Alunos'],
    summary='Detalhar aluno',
    description='''
    Retorna os detalhes de um aluno.

    **Permissões:** L2+ (LER_TUDO) ou dono do registro (L1).
    ''',
    responses={200: AlunoSerializer},
)
class DetalharAlunoView(IsOwnerOrAdminMixin, BasicRetrieveAPIView):
    serializer_class = AlunoSerializer
    queryset = Aluno.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'usuario_id'

    def obter_usuario_dono(self, obj):
        return obj.usuario


@extend_schema(
    tags=['Alunos'],
    summary='Atualizar aluno',
    description='''
    Atualiza os dados de um aluno existente.

    **Permissões:** L3 (EDITAR_TUDO) — administradores.
    ''',
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
