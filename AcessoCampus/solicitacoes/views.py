from django.db.models import F
from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)
from AcessoCampus.permissoes.access import PodeAnalisarAcessoCampusMixin, PodeSolicitarAcessoCampusMixin

from .choices import StatusSolicitacaoAcesso
from .constantes import ORDENACAO_PADRAO_ALUNO, ORDENACOES_ALUNO
from .escopo import vinculos_no_escopo
from .models import SolicitacaoAcesso
from .serializers import (
    AceitarSolicitacaoSerializer,
    AlunoElegivelSerializer,
    AutorizarAcessoSerializer,
    RecusarSolicitacaoSerializer,
    SerializerVazio,
    SolicitacaoAcessoDetalheSerializer,
    SolicitacaoAcessoSerializer,
    SolicitarAcessoAlunoSerializer,
    TurmaElegivelSerializer,
)

PERMISSOES = '''
    **Permissões:** `analisar_solicitacoes` ou L3 (EDITAR_TUDO).

    **Filtros:** os query params apenas reduzem o conjunto — nunca expandem o acesso além do escopo.
    '''


def _solicitacoes_no_escopo(usuario):
    return SolicitacaoAcesso.objects.filter(
        aluno_curso__in=vinculos_no_escopo(usuario),
    ).select_related('avaliada_por', 'liberado_por', 'aluno__usuario', 'aluno_curso', 'tipo')


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


# ----------------------------------------------------------------------
# Aluno: pedidos próprios (rotas minhas-solicitacoes/) e comprovante
# ----------------------------------------------------------------------

PERMISSAO_ALUNO = (
    '**Permissões:** Capacidade `solicitar` do AcessoCampus (aluno de Ensino Médio elegível, L1), '
    'compilada em `permissoes_acesso_campus()`.'
)

PERMISSAO_ALUNO_CONSULTA = (
    '**Permissões:** Usuário autenticado (L1). Escopo restrito às solicitações do próprio aluno, '
    'inclusive as autorizações registradas pela gestão. Não exige `solicitar`, para que o aluno '
    'que deixou de ser elegível continue consultando o que já pediu.'
)


@extend_schema(
    tags=['AcessoCampus'],
    summary='Listar minhas solicitações de acesso',
    description=(
        'Lista os pedidos do aluno autenticado e as autorizações que a gestão registrou para ele. '
        'Por padrão, das mais recentes para as mais antigas.\n\n'
        f'{PERMISSAO_ALUNO_CONSULTA}\n\n'
        '**Segurança:** os query params apenas reduzem ou reordenam o conjunto do próprio aluno, '
        'nunca expandem o acesso; valores inválidos são ignorados.'
    ),
    parameters=[
        OpenApiParameter(
            'status', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='1 = Pendente, 2 = Aceito, 3 = Recusado.',
            enum=list(StatusSolicitacaoAcesso.values),
        ),
        OpenApiParameter(
            'tipo', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Id do tipo de autorização (catálogo `tipos/`).',
        ),
        OpenApiParameter(
            'busca', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description='Busca no motivo e no nome de quem avaliou (ignora acentos).',
        ),
        OpenApiParameter(
            'ordenacao', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            enum=list(ORDENACOES_ALUNO),
            description=(
                'Ordenação da lista; `-` inverte a direção. `data_liberacao` é a data do acesso; '
                '`tipo` ordena pelo nome do tipo; sem avaliador fica no fim em `avaliado_por`. '
                f'Valor fora do enum usa o padrão (`{ORDENACAO_PADRAO_ALUNO}`).'
            ),
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
            description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoDetalheSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarMinhasSolicitacoesAcessoView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/acesso-campus/minhas-solicitacoes/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = SolicitacaoAcessoDetalheSerializer
    mensagem_sucesso = 'Solicitações de acesso listadas com sucesso.'

    def get_queryset(self):
        params = self.request.query_params
        return SolicitacaoAcesso().business.listar_do_aluno(
            self.request.user,
            status=self.obter_inteiro_do_query_param('status', StatusSolicitacaoAcesso.values),
            tipo=self.obter_inteiro_do_query_param('tipo'),
            busca=(params.get('busca') or '').strip() or None,
            ordenacao=params.get('ordenacao'),
        )

    def obter_inteiro_do_query_param(self, nome, valores_validos=None):
        """Inteiro do query param; valor inválido ou fora do domínio é ignorado (None)."""
        valor = self.request.query_params.get(nome)
        try:
            inteiro = int(valor)
        except (TypeError, ValueError):
            return None
        if valores_validos is not None and inteiro not in valores_validos:
            return None
        return inteiro


@extend_schema(
    tags=['AcessoCampus'],
    summary='Solicitar autorização de acesso',
    description=(
        'Registra um pedido PENDENTE de entrada ou saída para avaliação da gestão.\n\n'
        '- `aluno_curso` deve ser um vínculo ativo do próprio aluno em curso de Ensino Médio.\n'
        '- `tipo` é o id de um tipo-base do catálogo (`Entrada no campus` ou `Saída do campus`); '
        'os tipos criados pela gestão não são aceitos no pedido do aluno.\n'
        '- Entrada para o próprio dia só pode ser pedida até 07:00 (America/Fortaleza).\n'
        '- Datas passadas, horário já passado no próprio dia e pedido para dia e tipo em que o '
        'aluno já tem autorização aceita são recusados. Pedidos pendentes não bloqueiam.\n'
        '- `anexo` (obrigatório): comprovante PDF, JPG ou PNG de até 5 MB, conferido pelo '
        'conteúdo. Envie `multipart/form-data`.\n\n'
        f'{PERMISSAO_ALUNO}'
    ),
    request={'multipart/form-data': SolicitarAcessoAlunoSerializer},
    responses={
        status.HTTP_201_CREATED: SolicitacaoAcessoDetalheSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou regra de negócio não atendida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem a capacidade solicitar.'},
    },
)
class SolicitarAcessoView(PodeSolicitarAcessoCampusMixin, BasicPostAPIView):
    """POST /cortex/acesso-campus/minhas-solicitacoes/"""
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = SolicitarAcessoAlunoSerializer
    mensagem_sucesso = 'Solicitação de acesso registrada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao = SolicitacaoAcesso().business.solicitar(request.user, **serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': SolicitacaoAcessoDetalheSerializer(solicitacao, context={'request': request}).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['AcessoCampus'],
    summary='Detalhar minha solicitação de acesso',
    description=f'Retorna a solicitação do próprio aluno com o histórico.\n\n{PERMISSAO_ALUNO_CONSULTA}',
    responses={
        status.HTTP_200_OK: SolicitacaoAcessoDetalheSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação inexistente ou de outro aluno.'},
    },
)
class DetalharMinhaSolicitacaoAcessoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/acesso-campus/minhas-solicitacoes/{pk}/"""
    serializer_class = SolicitacaoAcessoDetalheSerializer
    mensagem_sucesso = 'Solicitação de acesso obtida com sucesso.'

    def get_queryset(self):
        return SolicitacaoAcesso().business.listar_do_aluno(self.request.user)


class ObterAnexoSolicitacaoAcessoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/acesso-campus/solicitacoes/{pk}/anexo/"""
    serializer_class = SerializerVazio

    def get_queryset(self):
        return SolicitacaoAcesso().business.listar_com_anexo_visivel(self.request.user)

    @extend_schema(
        tags=['AcessoCampus'],
        summary='Obter comprovante da solicitação',
        description=(
            'Retorna o comprovante anexado pelo aluno via proxy da API (bucket S3 privado).\n\n'
            '**Permissões:** Autenticado. L1 (EDITAR_EU) abre só o comprovante das próprias '
            'solicitações; a gestão com `analisar_solicitacoes` abre os do seu escopo de cursos; '
            'L3 (EDITAR_TUDO) abre todos. Fora disso responde 404.'
        ),
        responses={
            status.HTTP_200_OK: {
                'description': 'Arquivo retornado com sucesso.',
                'content': {'application/pdf': {}, 'image/jpeg': {}, 'image/png': {}},
            },
            status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
            status.HTTP_404_NOT_FOUND: {'description': 'Solicitação ou comprovante não encontrado.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        stream, content_type = self.get_object().business.obter_stream_anexo()
        response = StreamingHttpResponse(stream, content_type=content_type)
        response['Cache-Control'] = 'private, no-store'
        response['Content-Disposition'] = 'inline'
        return response
