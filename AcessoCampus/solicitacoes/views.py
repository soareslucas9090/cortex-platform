from django.db.models import F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status

from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from AcessoCampus.permissoes.access import PodeAnalisarAcessoCampusMixin

from .escopo import vinculos_no_escopo
from .models import SolicitacaoAcesso
from .serializers import (
    AceitarSolicitacaoSerializer,
    AlunoElegivelSerializer,
    AutorizarAcessoSerializer,
    RecusarSolicitacaoSerializer,
    SolicitacaoAcessoDetalheSerializer,
    SolicitacaoAcessoSerializer,
    TurmaElegivelSerializer,
)

PERMISSOES = '''
    **Permissões:** `analisar_solicitacoes` ou L3 (EDITAR_TUDO).

    **Filtros:** os query params apenas reduzem o conjunto — nunca expandem o acesso além do escopo.
    '''


def _solicitacoes_no_escopo(usuario):
    return SolicitacaoAcesso.objects.filter(
        aluno_curso__in=vinculos_no_escopo(usuario),
    ).select_related('avaliada_por', 'liberado_por', 'aluno__usuario', 'aluno_curso')


@extend_schema(
    tags=['AcessoCampus'],
    summary='Listar alunos elegíveis',
    description=f'''
    Lista vínculos de Ensino Médio que a gestão pode autorizar.

    {PERMISSOES}
    ''',
    parameters=[
        OpenApiParameter(
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description='Parte do nome, sem diferenciar acento.',
        ),
        OpenApiParameter(
            'cpf', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description='Parte do CPF.',
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: AlunoElegivelSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
    },
)
class ListarAlunosElegiveisView(PodeAnalisarAcessoCampusMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = AlunoElegivelSerializer
    mensagem_sucesso = 'Alunos listados com sucesso.'

    def get_queryset(self):
        qs = vinculos_no_escopo(self.request.user).select_related('aluno__usuario', 'curso')
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(aluno__usuario__nome__unaccent__icontains=nome)
        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(aluno__usuario__cpf__icontains=cpf)
        return qs.order_by('aluno__usuario__nome', 'curso__nome')


@extend_schema(
    tags=['AcessoCampus'],
    summary='Listar turmas elegíveis',
    description=f'''
    Lista pares de curso e turma com aluno elegível de Ensino Médio no escopo.

    {PERMISSOES}
    ''',
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: TurmaElegivelSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
    },
)
class ListarTurmasView(PodeAnalisarAcessoCampusMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = TurmaElegivelSerializer
    mensagem_sucesso = 'Turmas listadas com sucesso.'

    def get_queryset(self):
        qs = (
            vinculos_no_escopo(self.request.user)
            .exclude(turma__isnull=True)
            .exclude(turma='')
        )
        curso_id = self.request.query_params.get('curso_id')
        if curso_id is not None and str(curso_id).isdigit():
            qs = qs.filter(curso_id=int(curso_id))
        return (
            qs.values('curso_id', 'turma', curso_nome=F('curso__nome'))
            .distinct()
            .order_by('curso_nome', 'turma')
        )


@extend_schema(
    tags=['AcessoCampus'],
    summary='Autorizar acesso',
    description=f'''
    Cria uma autorização já aceita para os alunos informados ou para a turma do curso.

    {PERMISSOES}
    ''',
    request=AutorizarAcessoSerializer,
    responses={
        status.HTTP_201_CREATED: SolicitacaoAcessoSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: {
            'description': (
                'Alvo inválido, turma sem aluno, aluno fora do escopo, '
                'data anterior a hoje ou autorização aceita já existente.'
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes ou sem curso sob coordenação.'},
    },
)
class AutorizarAcessoView(PodeAnalisarAcessoCampusMixin, BasicPostAPIView):
    serializer_class = AutorizarAcessoSerializer
    mensagem_sucesso = 'Acesso autorizado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        criadas = SolicitacaoAcesso().business.autorizar(
            usuario=request.user,
            tipo=serializer_data['tipo'],
            data_acesso=serializer_data['data_acesso'],
            hora_autorizada=serializer_data['hora_autorizada'],
            motivo=serializer_data['motivo'],
            observacao=serializer_data.get('observacao', ''),
            aluno_curso_ids=serializer_data.get('aluno_curso_ids'),
            curso_id=serializer_data.get('curso_id'),
            turma=serializer_data.get('turma'),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SolicitacaoAcessoSerializer(criadas, many=True).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['AcessoCampus'],
    summary='Listar solicitações de acesso',
    description=f'''
    Lista pedidos do aluno e autorizações da gestão no escopo.

    {PERMISSOES}
    ''',
    parameters=[
        OpenApiParameter('status', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('cpf', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
    },
)
class ListarSolicitacoesView(PodeAnalisarAcessoCampusMixin, BasicGetAPIView):
    pagination_class = PaginacaoCustomizada
    serializer_class = SolicitacaoAcessoSerializer
    mensagem_sucesso = 'Solicitações listadas com sucesso.'

    def get_queryset(self):
        qs = _solicitacoes_no_escopo(self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param is not None and str(status_param).isdigit():
            qs = qs.filter(status=int(status_param))
        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(aluno__usuario__cpf__icontains=cpf)
        return qs


@extend_schema(
    tags=['AcessoCampus'],
    summary='Detalhar solicitação de acesso',
    description=f'''
    Detalhe para avaliação, com histórico da própria solicitação.

    {PERMISSOES}
    ''',
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoDetalheSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação inexistente ou fora do escopo.'},
    },
)
class DetalharSolicitacaoView(PodeAnalisarAcessoCampusMixin, BasicRetrieveAPIView):
    serializer_class = SolicitacaoAcessoDetalheSerializer
    mensagem_sucesso = 'Solicitação detalhada com sucesso.'

    def get_queryset(self):
        return _solicitacoes_no_escopo(self.request.user)


@extend_schema(
    tags=['AcessoCampus'],
    summary='Aceitar solicitação de acesso',
    description=f'''
    Aceita uma solicitação pendente. Sem horário no corpo, grava 08:00.

    {PERMISSOES}
    ''',
    request=AceitarSolicitacaoSerializer,
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoDetalheSerializer,
        status.HTTP_400_BAD_REQUEST: {
            'description': 'Solicitação não está pendente, a data já passou ou já existe autorização aceita.',
        },
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação inexistente ou fora do escopo.'},
    },
)
class AceitarSolicitacaoView(PodeAnalisarAcessoCampusMixin, BasicPostAPIView):
    serializer_class = AceitarSolicitacaoSerializer
    mensagem_sucesso = 'Solicitação aceita com sucesso.'

    def get_queryset(self):
        return _solicitacoes_no_escopo(self.request.user)

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao = self.get_object()
        solicitacao.business.aceitar(
            usuario=request.user,
            hora_autorizada=serializer_data.get('hora_autorizada'),
            observacao=serializer_data.get('observacao', ''),
        )
        solicitacao.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SolicitacaoAcessoDetalheSerializer(
                solicitacao, context={'request': request},
            ).data,
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['AcessoCampus'],
    summary='Recusar solicitação de acesso',
    description=f'''
    Recusa uma solicitação pendente. Não preenche o horário autorizado.

    {PERMISSOES}
    ''',
    request=RecusarSolicitacaoSerializer,
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoDetalheSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Solicitação não está pendente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem analisar_solicitacoes.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação inexistente ou fora do escopo.'},
    },
)
class RecusarSolicitacaoView(PodeAnalisarAcessoCampusMixin, BasicPostAPIView):
    serializer_class = RecusarSolicitacaoSerializer
    mensagem_sucesso = 'Solicitação recusada com sucesso.'

    def get_queryset(self):
        return _solicitacoes_no_escopo(self.request.user)

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao = self.get_object()
        solicitacao.business.recusar(
            usuario=request.user,
            observacao=serializer_data.get('observacao', ''),
        )
        solicitacao.refresh_from_db()
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SolicitacaoAcessoDetalheSerializer(
                solicitacao, context={'request': request},
            ).data,
            'status_code': status.HTTP_200_OK,
        }
