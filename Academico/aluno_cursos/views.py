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

from .models import AlunoCurso
from .serializers import (
    AlunoCursoSerializer,
    CriarAlunoCursoSerializer,
    AtualizarAlunoCursoSerializer,
    EncerrarAlunoCursoSerializer,
)


@extend_schema(
    tags=['Aluno-Cursos'],
    summary='Listar vínculos aluno-curso',
    description='''
    Lista os vínculos acadêmicos entre alunos e cursos.

    **Permissões:** Apenas administradores.

    **Paginação:** Suportada via query param `paginacao` (padrão 10, máximo 100).

    **Filtros:** Os query params apenas reduzem o conjunto de resultados — nunca expandem o acesso além do que a permissão do usuário já permite.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por status: true = Ativo, false = Encerrado.',
        ),
        OpenApiParameter(
            'aluno', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Filtra pelo ID do aluno.',
        ),
        OpenApiParameter(
            'curso', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Filtra pelo ID do curso.',
        ),
        OpenApiParameter(
            'nome_aluno', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do aluno (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'nome_curso', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do curso (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: AlunoCursoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    }
)
class ListarAlunoCursosView(IsAdminMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = AlunoCursoSerializer
    mensagem_sucesso = 'Vínculos listados com sucesso.'

    def get_queryset(self):
        qs = AlunoCurso.objects.all().select_related('aluno__usuario', 'curso')

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')

        aluno = self.request.query_params.get('aluno')
        if aluno is not None:
            try:
                qs = qs.filter(aluno_id=int(aluno))
            except (ValueError, TypeError):
                pass

        curso = self.request.query_params.get('curso')
        if curso is not None:
            try:
                qs = qs.filter(curso_id=int(curso))
            except (ValueError, TypeError):
                pass

        nome_aluno = self.request.query_params.get('nome_aluno')
        if nome_aluno:
            qs = qs.filter(aluno__usuario__nome__unaccent__icontains=nome_aluno)

        nome_curso = self.request.query_params.get('nome_curso')
        if nome_curso:
            qs = qs.filter(curso__nome__unaccent__icontains=nome_curso)

        return qs


@extend_schema(
    tags=['Aluno-Cursos'],
    summary='Criar vínculo aluno-curso',
    description='''
    Cria um novo vínculo acadêmico entre um aluno e um curso.

    **Permissões:** Apenas administradores.

    Não é possível criar um segundo vínculo ativo do mesmo aluno no mesmo curso.
    ''',
    request=CriarAlunoCursoSerializer,
    responses={
        status.HTTP_201_CREATED: AlunoCursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou vínculo já existente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    }
)
class CriarAlunoCursoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarAlunoCursoSerializer
    mensagem_sucesso = 'Vínculo acadêmico criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        vinculo = AlunoCurso().business.criar_vinculo(
            aluno_id=serializer_data['aluno'],
            curso_id=serializer_data['curso'],
            ano_conclusao=serializer_data.get('ano_conclusao'),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoCursoSerializer(vinculo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Aluno-Cursos'],
    summary='Detalhar vínculo aluno-curso',
    description='''
    Exibe os detalhes de um vínculo acadêmico específico.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: AlunoCursoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    }
)
class DetalharAlunoCursoView(IsAdminMixin, BasicRetrieveAPIView):
    queryset = AlunoCurso.objects.all().select_related('aluno__usuario', 'curso')
    serializer_class = AlunoCursoSerializer
    mensagem_sucesso = 'Vínculo detalhado com sucesso.'


@extend_schema(
    tags=['Aluno-Cursos'],
    summary='Atualizar vínculo aluno-curso',
    description='''
    Atualiza parcialmente os dados de um vínculo acadêmico (ex: ano_conclusao, ativo).

    **Permissões:** Apenas administradores.
    ''',
    request=AtualizarAlunoCursoSerializer,
    responses={
        status.HTTP_200_OK: AlunoCursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    }
)
class AtualizarAlunoCursoView(IsAdminMixin, BasicPatchAPIView):
    queryset = AlunoCurso.objects.all()
    serializer_class = AtualizarAlunoCursoSerializer
    mensagem_sucesso = 'Vínculo atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        vinculo = self.get_object()
        vinculo.business.atualizar_dados(serializer_data)
        vinculo.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoCursoSerializer(vinculo).data,
            'status_code': status.HTTP_200_OK,
        }


class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Aluno-Cursos'],
    summary='Encerrar vínculo aluno-curso',
    description='''
    Encerra um vínculo acadêmico ativo, registrando o ano de conclusão.

    **Permissões:** Apenas administradores.
    ''',
    request=EncerrarAlunoCursoSerializer,
    responses={
        status.HTTP_200_OK: AlunoCursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Vínculo já encerrado ou dados inválidos.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
    }
)
class EncerrarAlunoCursoView(IsAdminMixin, BasicPostAPIView):
    queryset = AlunoCurso.objects.all()
    serializer_class = EncerrarAlunoCursoSerializer
    mensagem_sucesso = 'Vínculo acadêmico encerrado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        vinculo = self.get_object()
        vinculo.business.encerrar(ano_conclusao=serializer_data['ano_conclusao'])
        vinculo.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': AlunoCursoSerializer(vinculo).data,
            'status_code': status.HTTP_200_OK,
        }
