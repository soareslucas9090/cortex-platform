import logging

from django.db import transaction

from rest_framework import status
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import IsAdminMixin, RespostasMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicPostAPIView, BasicPatchAPIView

from .business import SetorBusiness, FuncaoBusiness, SetorVinculoBusiness
from .models import Setor, Funcao, SetorVinculo
from .serializers import (
    AtualizarFuncaoSerializer,
    AtualizarSetorSerializer,
    AtualizarVinculoFuncaoSerializer,
    CriarFuncaoSerializer,
    CriarSetorSerializer,
    CriarVinculoSerializer,
    FuncaoSerializer,
    SerializerVazio,
    SetorSerializer,
    SetorVinculoSerializer,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Setores
# ===========================================================================

class SetoresView(IsAdminMixin, RespostasMixin, GenericAPIView):
    """GET /organizacional/setores/ | POST /organizacional/setores/"""
    pagination_class = PaginacaoCustomizada

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CriarSetorSerializer
        return SetorSerializer

    def get_queryset(self):
        qs = Setor.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs

    @extend_schema(
        tags=['Setores'],
        summary='Listar setores',
        description='''
        Retorna a lista paginada de setores da instituição.

        **Permissões:** Apenas administradores.

        **Query params apenas reduzem o conjunto — nunca expandem o acesso.**
        ''',
        parameters=[
            OpenApiParameter(
                'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                required=False, description='Filtra por ativo (true) ou inativo (false).',
            ),
            OpenApiParameter(
                'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Tamanho da página (1–100, padrão 10).',
            ),
        ],
        responses={
            status.HTTP_200_OK: SetorSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.resposta_lista_paginada(queryset, 'Setores listados com sucesso.')

    @extend_schema(
        tags=['Setores'],
        summary='Criar setor',
        description='Cria um novo setor. A sigla deve ser única.\n\n**Permissões:** Apenas administradores.',
        request=CriarSetorSerializer,
        responses={
            status.HTTP_201_CREATED: SetorSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                setor = SetorBusiness().criar_setor(**serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        return self.resposta_sucesso(
            'Setor criado com sucesso.',
            SetorSerializer(setor).data,
            status.HTTP_201_CREATED,
        )


class SetorView(IsAdminMixin, RespostasMixin, GenericAPIView):
    """GET /organizacional/setores/<pk>/ | PATCH /organizacional/setores/<pk>/"""
    queryset = Setor.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return AtualizarSetorSerializer
        return SetorSerializer

    @extend_schema(
        tags=['Setores'],
        summary='Detalhe do setor',
        description='Retorna os dados de um setor específico.\n\n**Permissões:** Apenas administradores.',
        responses={
            status.HTTP_200_OK: SetorSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        setor = self.get_object()
        return self.resposta_sucesso('Setor obtido com sucesso.', SetorSerializer(setor).data)

    @extend_schema(
        tags=['Setores'],
        summary='Atualizar setor',
        description='Atualiza parcialmente os dados do setor (nome e/ou sigla).\n\n**Permissões:** Apenas administradores.',
        request=AtualizarSetorSerializer,
        responses={
            status.HTTP_200_OK: SetorSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
        },
    )
    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        setor = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                setor.business.atualizar_dados(serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        setor.refresh_from_db()
        return self.resposta_sucesso('Setor atualizado com sucesso.', SetorSerializer(setor).data)


class DesativarSetorView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Setor desativado com sucesso.'
    queryset = Setor.objects.all()

    @extend_schema(
        tags=['Setores'],
        summary='Desativar setor',
        description='Desativa um setor. Bloqueado se houver vínculos ativos.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Setor desativado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Setor já inativo ou com vínculos ativos.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.desativar()


class ReativarSetorView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Setor reativado com sucesso.'
    queryset = Setor.objects.all()

    @extend_schema(
        tags=['Setores'],
        summary='Reativar setor',
        description='Reativa um setor previamente desativado.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Setor reativado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Setor já está ativo.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.reativar()


# ===========================================================================
# Funções
# ===========================================================================

class FuncoesView(IsAdminMixin, RespostasMixin, GenericAPIView):
    """GET /organizacional/funcoes/ | POST /organizacional/funcoes/"""
    pagination_class = PaginacaoCustomizada

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CriarFuncaoSerializer
        return FuncaoSerializer

    def get_queryset(self):
        qs = Funcao.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs

    @extend_schema(
        tags=['Funções'],
        summary='Listar funções',
        description='''
        Retorna a lista paginada de funções organizacionais.

        **Permissões:** Apenas administradores.

        **Query params apenas reduzem o conjunto — nunca expandem o acesso.**
        ''',
        parameters=[
            OpenApiParameter(
                'ativo', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                required=False, description='Filtra por ativa (true) ou inativa (false).',
            ),
            OpenApiParameter(
                'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Tamanho da página (1–100, padrão 10).',
            ),
        ],
        responses={
            status.HTTP_200_OK: FuncaoSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.resposta_lista_paginada(queryset, 'Funções listadas com sucesso.')

    @extend_schema(
        tags=['Funções'],
        summary='Criar função',
        description='Cria uma nova função organizacional. A sigla deve ser única.\n\n**Permissões:** Apenas administradores.',
        request=CriarFuncaoSerializer,
        responses={
            status.HTTP_201_CREATED: FuncaoSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        },
    )
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                funcao = FuncaoBusiness().criar_funcao(**serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        return self.resposta_sucesso(
            'Função criada com sucesso.',
            FuncaoSerializer(funcao).data,
            status.HTTP_201_CREATED,
        )


class FuncaoView(IsAdminMixin, RespostasMixin, GenericAPIView):
    """GET /organizacional/funcoes/<pk>/ | PATCH /organizacional/funcoes/<pk>/"""
    queryset = Funcao.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return AtualizarFuncaoSerializer
        return FuncaoSerializer

    @extend_schema(
        tags=['Funções'],
        summary='Detalhe da função',
        description='Retorna os dados de uma função específica.\n\n**Permissões:** Apenas administradores.',
        responses={
            status.HTTP_200_OK: FuncaoSerializer,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        funcao = self.get_object()
        return self.resposta_sucesso('Função obtida com sucesso.', FuncaoSerializer(funcao).data)

    @extend_schema(
        tags=['Funções'],
        summary='Atualizar função',
        description='Atualiza parcialmente os dados da função.\n\n**Permissões:** Apenas administradores.',
        request=AtualizarFuncaoSerializer,
        responses={
            status.HTTP_200_OK: FuncaoSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou sigla já cadastrada.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
        },
    )
    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        funcao = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                funcao.business.atualizar_dados(serializer.validated_data)
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        funcao.refresh_from_db()
        return self.resposta_sucesso('Função atualizada com sucesso.', FuncaoSerializer(funcao).data)


class DesativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/funcoes/<pk>/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Função desativada com sucesso.'
    queryset = Funcao.objects.all()

    @extend_schema(
        tags=['Funções'],
        summary='Desativar função',
        description='Desativa uma função. Bloqueado se estiver em uso em vínculos.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Função desativada com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Função já inativa ou em uso.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.desativar()


class ReativarFuncaoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/funcoes/<pk>/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Função reativada com sucesso.'
    queryset = Funcao.objects.all()

    @extend_schema(
        tags=['Funções'],
        summary='Reativar função',
        description='Reativa uma função previamente desativada.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Função reativada com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Função já está ativa.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Função não encontrada.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.reativar()


# ===========================================================================
# Vínculos de Setor
# ===========================================================================

class VinculosView(IsAdminMixin, RespostasMixin, GenericAPIView):
    """GET /organizacional/setores/<setor_pk>/vinculos/ | POST ..."""
    pagination_class = PaginacaoCustomizada

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CriarVinculoSerializer
        return SetorVinculoSerializer

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Listar vínculos do setor',
        description='''
        Retorna a lista paginada de vínculos de um setor específico.

        **Permissões:** Apenas administradores.

        **Query params apenas reduzem o conjunto — nunca expandem o acesso.**
        ''',
        parameters=[
            OpenApiParameter(
                'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Tamanho da página (1–100, padrão 10).',
            ),
        ],
        responses={
            status.HTTP_200_OK: SetorVinculoSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.resposta_lista_paginada(queryset, 'Vínculos listados com sucesso.')

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Criar vínculo no setor',
        description='''
        Vincula um usuário ao setor com uma função obrigatória.

        **Regras:**
        - Setor e função devem estar ativos.
        - A combinação (usuário, setor, função) deve ser única.
        - Um usuário pode ter múltiplos vínculos com setores ou funções diferentes.

        **Permissões:** Apenas administradores.
        ''',
        request=CriarVinculoSerializer,
        responses={
            status.HTTP_201_CREATED: SetorVinculoSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos, setor/função inativo ou vínculo duplicado.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Setor não encontrado.'},
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
                vinculo = SetorVinculoBusiness().criar_vinculo_no_setor(
                    usuario=dados['usuario'],
                    setor_pk=self.kwargs['setor_pk'],
                    funcao=dados['funcao'],
                    responsavel=dados.get('responsavel', False),
                )
            except Exception:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)
        return self.resposta_sucesso(
            'Vínculo criado com sucesso.',
            SetorVinculoSerializer(vinculo).data,
            status.HTTP_201_CREATED,
        )


class EncerrarVinculoView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/encerrar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Vínculo encerrado com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Encerrar vínculo',
        description='Remove o vínculo do usuário com o setor. Bloqueado se for o único responsável.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Vínculo encerrado com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Operação bloqueada: setor perderia seu único responsável.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.encerrar_vinculo()


class DefinirResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/definir-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Responsável definido com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Definir vínculo como responsável',
        description='''
        Marca o vínculo como responsável pelo setor.

        **Nota:** a validação de elegibilidade (responsável deve ser Servidor) será
        implementada em etapa futura junto ao domínio PessoasInstitucionais.

        **Permissões:** Apenas administradores.
        ''',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Responsável definido com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Setor inativo.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.definir_como_responsavel()


class RemoverResponsavelView(IsAdminMixin, BasicPostAPIView):
    """POST /organizacional/setores/<setor_pk>/vinculos/<pk>/remover-responsavel/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Responsabilidade removida com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Remover responsabilidade do vínculo',
        description='Remove a marcação de responsável do vínculo. Bloqueado se for o único responsável do setor.\n\n**Permissões:** Apenas administradores.',
        request=None,
        responses={
            status.HTTP_200_OK: {'description': 'Responsabilidade removida com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Operação bloqueada: setor perderia seu único responsável.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer_data, request):
        self.get_object().business.remover_responsabilidade()


class AtualizarVinculoFuncaoView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /organizacional/setores/<setor_pk>/vinculos/<pk>/funcao/"""
    serializer_class = AtualizarVinculoFuncaoSerializer
    mensagem_sucesso = 'Função do vínculo atualizada com sucesso.'

    def get_queryset(self):
        return SetorVinculo.objects.filter(setor_id=self.kwargs['setor_pk'])

    @extend_schema(
        tags=['Vínculos de Setor'],
        summary='Atualizar função do vínculo',
        description='Substitui a função exercida no vínculo. A nova função deve estar ativa e a combinação não deve ser duplicada.\n\n**Permissões:** Apenas administradores.',
        request=AtualizarVinculoFuncaoSerializer,
        responses={
            status.HTTP_200_OK: {'description': 'Função do vínculo atualizada com sucesso.'},
            status.HTTP_400_BAD_REQUEST: {'description': 'Função inativa ou vínculo duplicado resultante.'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Vínculo não encontrado.'},
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer_data, request):
        self.object.business.atualizar_funcao(serializer_data['funcao'])
