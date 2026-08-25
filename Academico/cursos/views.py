from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.serializers import Serializer

from AppCore.basics.mixins.mixins import IsAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
    BasicPatchAPIView,
)

from .models import Curso
from .serializers import CursoSerializer, CriarCursoSerializer, AtualizarCursoSerializer


@extend_schema(
    tags=['Cursos'],
    summary='Listar cursos',
    description='''
    Lista todos os cursos cadastrados.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).

    **Paginação:** Suportada via query param `paginacao` (padrão 10, máximo 100).

    **Filtros:** Os query params apenas reduzem o conjunto de resultados — nunca expandem o acesso além do que a permissão do usuário já permite.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
            required=False, description='Filtra por status: true = Ativo, false = Inativo.',
        ),
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do curso (ignora acentos e maiúsculas).',
        ),
        OpenApiParameter(
            'codigo_curso', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do código do curso.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: CursoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    }
)
class ListarCursosView(IsAuthenticatedMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = CursoSerializer
    mensagem_sucesso = 'Cursos listados com sucesso.'

    def get_queryset(self):
        qs = Curso.objects.all()

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')

        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)

        codigo_curso = self.request.query_params.get('codigo_curso')
        if codigo_curso:
            qs = qs.filter(codigo_curso__unaccent__icontains=codigo_curso)

        return qs


@extend_schema(
    tags=['Cursos'],
    summary='Criar curso',
    description='''
    Cria um novo curso.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).
    ''',
    request=CriarCursoSerializer,
    responses={
        status.HTTP_201_CREATED: CursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou código de curso já em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    }
)
class CriarCursoView(IsAdminMixin, BasicPostAPIView):
    serializer_class = CriarCursoSerializer
    mensagem_sucesso = 'Curso criado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        curso = Curso().business.criar_curso(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CursoSerializer(curso).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Cursos'],
    summary='Detalhar curso',
    description='''
    Exibe os detalhes de um curso específico.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).
    ''',
    responses={
        status.HTTP_200_OK: CursoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Curso não encontrado.'},
    }
)
class DetalharCursoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    mensagem_sucesso = 'Curso detalhado com sucesso.'


@extend_schema(
    tags=['Cursos'],
    summary='Atualizar curso',
    description='''
    Atualiza parcialmente os dados de um curso existente.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).
    ''',
    request=AtualizarCursoSerializer,
    responses={
        status.HTTP_200_OK: CursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou código já em uso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Curso não encontrado.'},
    }
)
class AtualizarCursoView(IsAdminMixin, BasicPatchAPIView):
    queryset = Curso.objects.all()
    serializer_class = AtualizarCursoSerializer
    mensagem_sucesso = 'Curso atualizado com sucesso.'

    def do_action_patch(self, serializer_data, request, *args, **kwargs):
        curso = self.get_object()
        curso.business.atualizar_dados(serializer_data)
        curso.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CursoSerializer(curso).data,
            'status_code': status.HTTP_200_OK,
        }


class SerializerVazio(Serializer):
    pass


@extend_schema(
    tags=['Cursos'],
    summary='Desativar curso',
    description='''
    Desativa um curso ativo.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: CursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Curso já está inativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Curso não encontrado.'},
    }
)
class DesativarCursoView(IsAdminMixin, BasicPostAPIView):
    queryset = Curso.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Curso desativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        curso = self.get_object()
        curso.business.desativar()
        curso.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CursoSerializer(curso).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Cursos'],
    summary='Reativar curso',
    description='''
    Reativa um curso inativo.

    **Permissões:** Qualquer usuário autenticado (catálogo de referência). Escrita apenas L3 (EDITAR_TUDO).
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: CursoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Curso já está ativo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Curso não encontrado.'},
    }
)
class ReativarCursoView(IsAdminMixin, BasicPostAPIView):
    queryset = Curso.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Curso reativado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        curso = self.get_object()
        curso.business.reativar()
        curso.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': CursoSerializer(curso).data,
            'status_code': status.HTTP_200_OK,
        }
