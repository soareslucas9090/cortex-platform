import logging

from django.db import transaction

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import IsAdminMixin, IsOwnerOrAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicPostAPIView, BasicPatchAPIView
from AppCore.core.exceptions.exceptions import AuthorizationException, NotFoundException
from AppCore.core.permissions.permissions import IsAdminPermission, IsOwnerOrAdminPermission

from .business import UsuarioBusiness
from .choices import SituacaoMatricula
from .models import Usuario, Contato, Endereco, Matricula
from .serializers import (
    AdicionarMatriculaSerializer,
    AtualizarUsuarioSerializer,
    ContatoInputSerializer,
    ContatoSerializer,
    CriarUsuarioSerializer,
    EnderecoInputSerializer,
    EnderecoSerializer,
    MatriculaSerializer,
    SerializerVazio,
    UsuarioSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _verificar_acesso_usuario(request, usuario_pk):
    """
    Verifica se o usuário autenticado tem acesso aos dados do usuario_pk.

    Utilizada em endpoints de listagem de sub-recursos (contatos, matrículas),
    onde has_object_permission não é acionado automaticamente pelo DRF.
    Os query params de filtragem são aplicados APÓS esta verificação —
    eles nunca expandem o acesso, apenas reduzem o conjunto de resultados.
    """
    if not (
        request.user.pk == int(usuario_pk)
        or getattr(request.user, 'is_admin', False)
        or request.user.is_superuser
    ):
        raise AuthorizationException('Você não tem permissão para acessar esses dados.')


def _resposta_sucesso(mensagem, dados=None, status_code=status.HTTP_200_OK):
    data = {'status': 'success', 'mensagem': mensagem}
    if dados is not None:
        data['dados'] = dados
    return Response(data, status=status_code)


def _resposta_lista_paginada(view, queryset, mensagem):
    page = view.paginate_queryset(queryset)
    if page is not None:
        serializer = view.get_serializer(page, many=True)
        paginada = view.get_paginated_response(serializer.data)
        return Response({
            'status': 'success',
            'mensagem': mensagem,
            'count': paginada.data.get('count'),
            'next': paginada.data.get('next'),
            'previous': paginada.data.get('previous'),
            'dados': paginada.data.get('results'),
        }, status=status.HTTP_200_OK)
    serializer = view.get_serializer(queryset, many=True)
    return Response({'status': 'success', 'mensagem': mensagem, 'dados': serializer.data})


# ===========================================================================
# Usuários
# ===========================================================================

class UsuariosView(IsAdminMixin, GenericAPIView):
    """
    GET  /identidade/usuarios/  — lista paginada de usuários
    POST /identidade/usuarios/  — criar novo usuário
    """
    pagination_class = PaginacaoCustomizada

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CriarUsuarioSerializer
        return UsuarioSerializer

    def get_queryset(self):
        qs = Usuario.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs

    @extend_schema(
        tags=['Identidade'],
        summary='Listar usuários',
        description='''
        Retorna a lista paginada de usuários do sistema.

        **Permissões:** Apenas administradores.

        **Query params:**
        - `ativo` (bool, opcional): filtra por status — `true` (ativos) ou `false` (inativos).
          Omitindo o parâmetro, retorna todos.
        - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.

        **Segurança:** os query params apenas restringem o conjunto de resultados dentro do
        escopo já autorizado — nunca expandem o acesso além do permitido pela permissão.
        ''',
        parameters=[
            OpenApiParameter(
                'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                required=False, description='Filtra por status ativo (true) ou inativo (false).',
            ),
            OpenApiParameter(
                'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Tamanho da página (1–100, padrão 10).',
            ),
        ],
        responses={
            status.HTTP_200_OK: UsuarioSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return _resposta_lista_paginada(self, queryset, 'Usuários listados com sucesso.')

    @extend_schema(
        tags=['Identidade'],
        summary='Criar usuário',
        description='''
        Cria um novo usuário no sistema.

        **Permissões:** Apenas administradores.

        Não há auto-cadastro — usuários são sempre criados por administradores,
        individualmente ou em lote via JSON.
        ''',
        request=CriarUsuarioSerializer,
        responses={
            status.HTTP_201_CREATED: UsuarioSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou CPF já cadastrado.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                usuario = UsuarioBusiness().criar_usuario(
                    cpf=dados['cpf'],
                    nome=dados['nome'],
                    password=dados['password'],
                    email=dados.get('email'),
                    deficiencia=dados.get('deficiencia', ''),
                )
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return _resposta_sucesso(
            'Usuário criado com sucesso.',
            UsuarioSerializer(usuario).data,
            status.HTTP_201_CREATED,
        )


class UsuarioView(IsOwnerOrAdminMixin, GenericAPIView):
    """
    GET   /identidade/usuarios/{pk}/  — detalhe do usuário
    PATCH /identidade/usuarios/{pk}/  — atualizar dados básicos
    """
    queryset = Usuario.objects.all()

    def obter_usuario_dono(self, obj):
        return obj  # O usuário é dono de si mesmo

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return AtualizarUsuarioSerializer
        return UsuarioSerializer

    @extend_schema(
        tags=['Identidade'],
        summary='Detalhe do usuário',
        description='''
        Retorna os dados de um usuário específico.

        **Permissões:** O próprio usuário ou administradores.
        ''',
        responses={
            status.HTTP_200_OK: UsuarioSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        usuario = self.get_object()
        return _resposta_sucesso('Usuário obtido com sucesso.', UsuarioSerializer(usuario).data)

    @extend_schema(
        tags=['Identidade'],
        summary='Atualizar dados do usuário',
        description='''
        Atualiza parcialmente os dados básicos do usuário (nome, e-mail, foto, deficiência).

        **Permissões:** O próprio usuário ou administradores.

        CPF não é alterável neste endpoint.
        ''',
        request=AtualizarUsuarioSerializer,
        responses={
            status.HTTP_200_OK: UsuarioSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        usuario = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                usuario.business.atualizar_dados(serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        usuario.refresh_from_db()
        return _resposta_sucesso('Usuário atualizado com sucesso.', UsuarioSerializer(usuario).data)


class DesativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário desativado com sucesso.'

    @extend_schema(
        tags=['Identidade'],
        summary='Desativar usuário',
        description='''
        Desativa um usuário do sistema (não remove o registro).

        **Permissões:** Apenas administradores.
        ''',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Usuário desativado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Usuário já está inativo.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        usuario = Usuario.objects.get(pk=self.kwargs['pk'])
        usuario.business.desativar()


class ReativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário reativado com sucesso.'

    @extend_schema(
        tags=['Identidade'],
        summary='Reativar usuário',
        description='''
        Reativa um usuário previamente desativado.

        **Permissões:** Apenas administradores.
        ''',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Usuário reativado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Usuário já está ativo.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        usuario = Usuario.objects.get(pk=self.kwargs['pk'])
        usuario.business.reativar()


# ===========================================================================
# Contatos
# ===========================================================================

class ContatosView(IsOwnerOrAdminMixin, GenericAPIView):
    """
    GET  /identidade/usuarios/{usuario_pk}/contatos/  — listar contatos
    POST /identidade/usuarios/{usuario_pk}/contatos/  — adicionar contato
    """
    pagination_class = PaginacaoCustomizada

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContatoInputSerializer
        return ContatoSerializer

    def get_queryset(self):
        return Contato.objects.filter(usuario_id=self.kwargs['usuario_pk'])

    @extend_schema(
        tags=['Identidade'],
        summary='Listar contatos do usuário',
        description='''
        Retorna a lista de contatos de um usuário específico.

        **Permissões:** O próprio usuário ou administradores.

        **Query params:**
        - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.

        **Segurança:** os resultados já estão restritos ao usuário da URL — query params
        apenas reduzem o conjunto, nunca expandem o acesso.
        ''',
        parameters=[
            OpenApiParameter(
                'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Tamanho da página (1–100, padrão 10).',
            ),
        ],
        responses={
            status.HTTP_200_OK: ContatoSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        _verificar_acesso_usuario(request, self.kwargs['usuario_pk'])
        queryset = self.filter_queryset(self.get_queryset())
        return _resposta_lista_paginada(self, queryset, 'Contatos listados com sucesso.')

    @extend_schema(
        tags=['Identidade'],
        summary='Adicionar contato ao usuário',
        description='''
        Adiciona um novo contato (e-mail acadêmico, e-mail pessoal ou telefone) ao usuário.

        **Permissões:** O próprio usuário ou administradores.

        Informe ao menos um dos campos de contato.
        ''',
        request=ContatoInputSerializer,
        responses={
            status.HTTP_201_CREATED: ContatoSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        _verificar_acesso_usuario(request, self.kwargs['usuario_pk'])
        usuario = Usuario.objects.get(pk=self.kwargs['usuario_pk'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                contato = usuario.business.adicionar_contato(**serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return _resposta_sucesso(
            'Contato adicionado com sucesso.',
            ContatoSerializer(contato).data,
            status.HTTP_201_CREATED,
        )


class ContatoView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    """PATCH /identidade/usuarios/{usuario_pk}/contatos/{pk}/"""
    serializer_class = ContatoInputSerializer

    def obter_usuario_dono(self, obj):
        return obj.usuario

    def get_queryset(self):
        return Contato.objects.filter(usuario_id=self.kwargs['usuario_pk'])

    @extend_schema(
        tags=['Identidade'],
        summary='Atualizar contato',
        description='''
        Atualiza parcialmente os dados de um contato do usuário.

        **Permissões:** O próprio usuário ou administradores.
        ''',
        request=ContatoInputSerializer,
        responses={
            status.HTTP_200_OK: {'description': 'Contato atualizado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Contato não encontrado.'},
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer_data, request):
        self.object.usuario.business.atualizar_contato(self.object, serializer_data)


# ===========================================================================
# Endereço
# ===========================================================================

class EnderecoView(IsOwnerOrAdminMixin, GenericAPIView):
    """
    GET /identidade/usuarios/{usuario_pk}/endereco/  — obter endereço
    PUT /identidade/usuarios/{usuario_pk}/endereco/  — salvar (cria ou atualiza)
    """

    def obter_usuario_dono(self, obj):
        return obj  # obj é sempre o Usuario nesta view

    def _obter_usuario_com_acesso(self, usuario_pk):
        _verificar_acesso_usuario(self.request, usuario_pk)
        return Usuario.objects.get(pk=usuario_pk)

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return EnderecoInputSerializer
        return EnderecoSerializer

    @extend_schema(
        tags=['Identidade'],
        summary='Obter endereço do usuário',
        description='''
        Retorna o endereço cadastrado do usuário.

        **Permissões:** O próprio usuário ou administradores.

        Retorna 404 se o endereço ainda não foi cadastrado.
        ''',
        responses={
            status.HTTP_200_OK: EnderecoSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Endereço não cadastrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        usuario = self._obter_usuario_com_acesso(self.kwargs['usuario_pk'])
        if not hasattr(usuario, 'endereco'):
            raise NotFoundException('Endereço não cadastrado.')
        return _resposta_sucesso('Endereço obtido com sucesso.', EnderecoSerializer(usuario.endereco).data)

    @extend_schema(
        tags=['Identidade'],
        summary='Salvar endereço do usuário',
        description='''
        Cria ou atualiza o endereço do usuário (operação idempotente).

        **Permissões:** O próprio usuário ou administradores.
        ''',
        request=EnderecoInputSerializer,
        responses={
            status.HTTP_200_OK: EnderecoSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
        },
    )
    @handle_exceptions
    def put(self, request, *args, **kwargs):
        usuario = self._obter_usuario_com_acesso(self.kwargs['usuario_pk'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                endereco = usuario.business.salvar_endereco(serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return _resposta_sucesso('Endereço salvo com sucesso.', EnderecoSerializer(endereco).data)


# ===========================================================================
# Matrículas
# ===========================================================================

class MatriculasView(GenericAPIView):
    """
    GET  /identidade/usuarios/{usuario_pk}/matriculas/  — listar matrículas
    POST /identidade/usuarios/{usuario_pk}/matriculas/  — adicionar matrícula (admin)
    """
    serializer_class = MatriculaSerializer
    pagination_class = PaginacaoCustomizada

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminPermission()]
        return [IsOwnerOrAdminPermission()]

    def obter_usuario_dono(self, obj):
        return obj.usuario

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
        return qs

    @extend_schema(
        tags=['Identidade'],
        summary='Listar matrículas do usuário',
        description='''
        Retorna a lista de matrículas de um usuário específico.

        **Permissões:** O próprio usuário ou administradores.

        **Query params:**
        - `situacao` (int, opcional): filtra por situação — `1` (Ativa) ou `2` (Inativa).
          Omitindo, retorna todas.
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
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        _verificar_acesso_usuario(request, self.kwargs['usuario_pk'])
        queryset = self.filter_queryset(self.get_queryset())
        return _resposta_lista_paginada(self, queryset, 'Matrículas listadas com sucesso.')

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
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        usuario = Usuario.objects.get(pk=self.kwargs['usuario_pk'])
        serializer = AdicionarMatriculaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                matricula = usuario.business.adicionar_matricula(serializer.validated_data['matricula'])
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return _resposta_sucesso(
            'Matrícula adicionada com sucesso.',
            MatriculaSerializer(matricula).data,
            status.HTTP_201_CREATED,
        )


class DesativarMatriculaView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{usuario_pk}/matriculas/{pk}/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Matrícula desativada com sucesso.'

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
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        usuario = Usuario.objects.get(pk=self.kwargs['usuario_pk'])
        matricula = Matricula.objects.get(pk=self.kwargs['pk'], usuario=usuario)
        usuario.business.desativar_matricula(matricula)
