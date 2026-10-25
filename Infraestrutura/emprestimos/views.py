from rest_framework import status

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from AppCore.basics.mixins.mixins import IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicPostAPIView, BasicRetrieveAPIView

from Infraestrutura.permissoes.access import PodeOperarInfraestruturaMixin
from Identidade.usuarios.models import Usuario

from .models import Emprestimo, SolicitacaoTrocaTitular
from .serializers import (
    AceitarSolicitacaoTrocaTitularRespostaSerializer,
    CriarSolicitacaoTrocaTitularSerializer,
    DevolverItensSerializer,
    EmprestimoSerializer,
    ListarEmprestimosQuerySerializer,
    ORDENACOES_EMPRESTIMOS,
    RealizarEmprestimoSerializer,
    SerializerVazio,
    SolicitacaoTrocaTitularSerializer,
    TrocarTitularSerializer,
    UsuarioResumoSerializer,
)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar solicitantes elegíveis para recurso(s)',
    description='''
    Retorna usuários que podem ser solicitantes de empréstimo para **todos** os recursos
    informados, conforme as regras de elegibilidade (retirada irrestrita, servidor,
    terceirizado em chaves, SalaSetor, autorização).

    Informe um ou mais IDs em `recurso_id` e/ou `recurso_ids` (repetidos ou separados
    por vírgula). A resposta contém apenas usuários elegíveis a cada recurso enviado.

    **Permissões:** Capacidade `operar` em Infraestrutura para a consulta administrativa.
    Contas pessoais também podem consultar servidores para recursos pertencentes a um
    empréstimo aberto no próprio nome.
    ''',
    parameters=[
        OpenApiParameter(
            'recurso_id',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='ID de um recurso (pode repetir o parâmetro para vários recursos).',
        ),
        OpenApiParameter(
            'recurso_ids',
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            required=False,
            description='IDs de recursos (repetir o parâmetro ou separar por vírgula).',
        ),
        OpenApiParameter(
            'nome',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Filtra por parte do nome do solicitante.',
        ),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: UsuarioResumoSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: {'description': 'Recursos inválidos ou não informados.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem autorização para estes recursos.'},
    },
)
class ListarSolicitantesElegiveisView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/emprestimos/solicitantes-elegiveis/"""

    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioResumoSerializer
    mensagem_sucesso = 'Solicitantes elegíveis listados com sucesso.'

    def get_queryset(self):
        params = self.request.query_params
        nome = self.request.query_params.get('nome')
        return Emprestimo().business.listar_solicitantes_elegiveis(
            self.request.user, params.getlist('recurso_ids'), params.getlist('recurso_id'), nome=nome or None
        )


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar responsáveis elegíveis',
    description='''
    Retorna usuários que podem ser **responsáveis** (quem entrega o recurso) no empréstimo.

    - Conta **não coletiva**: apenas o próprio usuário autenticado.
    - Conta **coletiva** (`usuario_coletivo`): pool definido pelas associações
      (empresas, cargos, funções, setores) da conta.

    Query params apenas **reduzem** o conjunto retornado; nunca expandem o acesso
    além do pool permitido para a conta autenticada.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    parameters=[
        OpenApiParameter('nome', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('cpf', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('empresa_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('cargo_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('setor_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('funcao_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('tipo_perfil', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: UsuarioResumoSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade para operar empréstimos.'},
    },
)
class ListarResponsaveisElegiveisView(PodeOperarInfraestruturaMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/emprestimos/responsaveis-elegiveis/"""

    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioResumoSerializer
    mensagem_sucesso = 'Responsáveis elegíveis listados com sucesso.'

    def get_queryset(self):
        params = self.request.query_params
        filtros = {'nome': params.get('nome') or None}

        for chave in ('cpf', 'tipo_perfil'):
            valor = params.get(chave)
            if valor:
                filtros[chave] = valor

        for chave in ('empresa_id', 'cargo_id', 'setor_id', 'funcao_id'):
            valor = params.get(chave)
            if valor and valor.isdigit():
                filtros[chave] = int(valor)

        return Usuario().business.listar_responsaveis_do_coletivo(self.request.user, **filtros)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Listar empréstimos',
    description='''
    Com `operar`: consulta ampla com filtros.
    Sem `operar`: empréstimos do próprio solicitante e empréstimos com solicitação
    de troca pendente recebida pelo usuário. Nesse escopo, `ativo=true` retorna os
    pendentes, `ativo=false` retorna os concluídos e a ausência de `ativo` retorna ambos.
    Contas coletivas enxergam apenas empréstimos da própria origem (`guarita` ou `codis`).
    Administradores e superusuários mantêm acesso a todas as origens.

    Ordenação padrão: solicitações de troca pendentes relacionadas ao usuário primeiro;
    depois empréstimos **abertos**, data de retirada mais recente e ID como desempate.
    A ordenação é aplicada antes da paginação.

    **Permissões:** Usuário autenticado (escopo conforme capacidade `operar`).

    **Segurança:** Os query params apenas reduzem o conjunto já autorizado e nunca
    expandem o acesso. `atrasado=true` retorna ativos há mais de 24 horas;
    `atrasado=false` retorna os demais empréstimos.

    Datas e horários são avaliados em `America/Sao_Paulo`. Parâmetros malformados são
    ignorados; intervalos cuja hora inicial seja maior que a final retornam 400.
    Em empréstimos parcialmente devolvidos, busca e filtros de recurso, sala e tipo
    consideram somente itens ainda abertos. Em empréstimos concluídos, consideram todo
    o histórico de itens.
    ''',
    parameters=[
        OpenApiParameter(
            'ativo',
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            required=False,
            description=(
                'Use true para empréstimos pendentes e false para concluídos. '
                'Sem o parâmetro, retorna ambos dentro do escopo autorizado.'
            ),
        ),
        OpenApiParameter('solicitante_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('responsavel_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('recurso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('sala_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter(
            'tipo_recurso',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            enum=['chave', 'midia', 'material_didatico'],
        ),
        OpenApiParameter(
            'busca',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Busca sem diferença de caixa ou acentos nos dados do empréstimo, recurso, sala e bloco.',
        ),
        OpenApiParameter(
            'retirada_data',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=False,
            description='Data local da retirada no formato YYYY-MM-DD.',
        ),
        OpenApiParameter(
            'retirada_hora_inicio',
            OpenApiTypes.TIME,
            OpenApiParameter.QUERY,
            required=False,
            description='Hora local mínima da retirada, inclusiva, no formato HH:mm.',
        ),
        OpenApiParameter(
            'retirada_hora_fim',
            OpenApiTypes.TIME,
            OpenApiParameter.QUERY,
            required=False,
            description='Hora local máxima da retirada, inclusiva, no formato HH:mm.',
        ),
        OpenApiParameter(
            'devolucao_data',
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=False,
            description='Data local da devolução de algum item no formato YYYY-MM-DD.',
        ),
        OpenApiParameter(
            'devolucao_hora_inicio',
            OpenApiTypes.TIME,
            OpenApiParameter.QUERY,
            required=False,
            description='Hora local mínima da devolução, inclusiva, no formato HH:mm.',
        ),
        OpenApiParameter(
            'devolucao_hora_fim',
            OpenApiTypes.TIME,
            OpenApiParameter.QUERY,
            required=False,
            description='Hora local máxima da devolução, inclusiva, no formato HH:mm.',
        ),
        OpenApiParameter(
            'ordenacao',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            enum=ORDENACOES_EMPRESTIMOS,
            description='Prefixe com - para ordem decrescente. Solicitações de troca pendentes permanecem prioritárias.',
        ),
        OpenApiParameter(
            'atrasado',
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            required=False,
            description=(
                'Filtra empréstimos atrasados (ativos há mais de 24 horas). '
                'Use false para retornar os que não estão atrasados.'
            ),
        ),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: EmprestimoSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: {'description': 'Intervalo de horários inválido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarEmprestimosView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/infraestrutura/emprestimos/"""

    pagination_class = PaginacaoCustomizada
    serializer_class = EmprestimoSerializer
    mensagem_sucesso = 'Empréstimos listados com sucesso.'

    def validate_get(self, request, *args, **kwargs):
        serializer = ListarEmprestimosQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        self.filtros_validados = serializer.validated_data

    def get_queryset(self):
        filtros = getattr(self, 'filtros_validados', {})
        return Emprestimo().business.listar_para_usuario(self.request.user, **filtros)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Realizar empréstimo',
    description='''
    Registra retirada multi-item para um solicitante.

  - Conta não coletiva: o responsável é o próprio usuário autenticado.
  - Conta coletiva: informe `responsavel_id` com um usuário do pool elegível.
    A origem coletiva é determinada pelo backend e não pode ser enviada pelo cliente.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=RealizarEmprestimoSerializer,
    responses={
        status.HTTP_201_CREATED: EmprestimoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Payload ou regra de negócio inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem capacidade para operar empréstimos.'},
    },
)
class RealizarEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/"""

    serializer_class = RealizarEmprestimoSerializer
    mensagem_sucesso = 'Empréstimo realizado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo = Emprestimo().business.realizar_emprestimo(conta_autenticada=request.user, **serializer_data)
        emprestimo = Emprestimo().business.obter_detalhado(emprestimo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmprestimoSerializer(emprestimo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Detalhe do empréstimo',
    description='''
    Com `operar`: qualquer empréstimo.
    Sem `operar`: empréstimos próprios, pendentes ou concluídos, e empréstimos com
    solicitação de troca pendente recebida pelo usuário.
    Contas coletivas ficam restritas à origem correspondente ao seu tipo; administradores
    e superusuários podem consultar todas as origens.

    **Permissões:** Usuário autenticado (escopo conforme capacidade `operar`).
    ''',
    responses={
        status.HTTP_200_OK: EmprestimoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Empréstimo fora do escopo autorizado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Empréstimo não encontrado.'},
    },
)
class DetalheEmprestimoView(IsAuthenticatedMixin, BasicRetrieveAPIView):
    """GET /cortex/infraestrutura/emprestimos/<pk>/"""

    serializer_class = EmprestimoSerializer
    mensagem_sucesso = 'Empréstimo obtido com sucesso.'

    def get_queryset(self):
        return Emprestimo().business.listar_detalhados(usuario=self.request.user)

    def validate_retrieve(self, request, *args, **kwargs):
        self.object.business.verificar_consulta(request.user)


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Devolver itens',
    description='''
    Devolução parcial de itens. O empréstimo encerra quando todos forem devolvidos.
    Contas coletivas só podem devolver empréstimos da própria origem.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=DevolverItensSerializer,
    responses={
        status.HTTP_200_OK: EmprestimoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Itens inválidos ou empréstimo encerrado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão ou empréstimo fora do escopo autorizado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Empréstimo não encontrado.'},
    },
)
class DevolverItensEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/<pk>/devolver/"""

    serializer_class = DevolverItensSerializer
    mensagem_sucesso = 'Itens devolvidos com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo = Emprestimo().business.obter_detalhado(kwargs['pk'])
        emprestimo.business.devolver_itens(request.user, serializer_data['item_ids'])
        emprestimo = Emprestimo().business.obter_detalhado(emprestimo.pk)
        return {'mensagem': self.mensagem_sucesso, 'dados': EmprestimoSerializer(emprestimo).data}


@extend_schema(
    tags=['Infraestrutura · Empréstimos'],
    summary='Trocar titular',
    description='''
    Devolve itens em aberto e registra novo empréstimo para outro solicitante
    (encerra o atual e abre outro).

    - Conta não coletiva: o responsável do novo empréstimo é o próprio usuário autenticado.
    - Conta coletiva: informe `responsavel_id` com um usuário do pool elegível
      (mesma regra do realizar empréstimo).
    - A nova origem é determinada exclusivamente pela conta autenticada.

    **Permissões:** Capacidade `operar` em Infraestrutura.
    ''',
    request=TrocarTitularSerializer,
    responses={
        status.HTTP_201_CREATED: EmprestimoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Payload ou regra de negócio inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão ou empréstimo fora do escopo autorizado.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Empréstimo não encontrado.'},
    },
)
class TrocarTitularEmprestimoView(PodeOperarInfraestruturaMixin, BasicPostAPIView):
    """POST /cortex/infraestrutura/emprestimos/<pk>/trocar-titular/"""

    serializer_class = TrocarTitularSerializer
    mensagem_sucesso = 'Titular trocado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        emprestimo_anterior = Emprestimo().business.obter_detalhado(kwargs['pk'])
        novo_emprestimo = emprestimo_anterior.business.trocar_titular(conta_autenticada=request.user, **serializer_data)
        novo_emprestimo = Emprestimo().business.obter_detalhado(novo_emprestimo.pk)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': EmprestimoSerializer(novo_emprestimo).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Solicitações de troca'],
    summary='Criar solicitação de troca de titular',
    description='''
    Solicita que outro servidor assuma os itens abertos do empréstimo.

    **Permissões:** Qualquer usuário autenticado (L1–L3) que seja o titular atual.
    Contas coletivas não podem utilizar este fluxo.
    ''',
    request=CriarSolicitacaoTrocaTitularSerializer,
    responses={
        status.HTTP_201_CREATED: SolicitacaoTrocaTitularSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Regra de negócio inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem autorização.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Empréstimo não encontrado.'},
    },
)
class CriarSolicitacaoTrocaTitularView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = CriarSolicitacaoTrocaTitularSerializer
    mensagem_sucesso = 'Solicitação de troca de titular criada com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao = SolicitacaoTrocaTitular().business.criar_solicitacao(
            emprestimo_id=kwargs['emprestimo_id'], solicitante=request.user, **serializer_data
        )
        solicitacao = SolicitacaoTrocaTitular().business.obter_detalhada(solicitacao.pk)
        return {
            'dados': SolicitacaoTrocaTitularSerializer(solicitacao, context={'request': request}).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Infraestrutura · Solicitações de troca'],
    summary='Listar solicitações de troca de titular',
    description='''
    Lista somente solicitações enviadas ou recebidas pelo usuário autenticado.
    Query params apenas reduzem o conjunto e nunca expandem o acesso.

    **Permissões:** Qualquer usuário autenticado (L1–L3).
    ''',
    parameters=[
        OpenApiParameter(
            'status',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            enum=['1', '2', '3', '4', 'PENDENTE', 'ACEITA', 'RECUSADA', 'CANCELADA'],
            description='Aceita o código numérico ou, por compatibilidade, o nome do status.',
        ),
        OpenApiParameter(
            'direcao', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, enum=['recebidas', 'enviadas']
        ),
        OpenApiParameter('emprestimo_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        OpenApiParameter('paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    ],
    responses={
        status.HTTP_200_OK: SolicitacaoTrocaTitularSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class ListarSolicitacoesTrocaTitularView(IsAuthenticatedMixin, BasicGetAPIView):
    serializer_class = SolicitacaoTrocaTitularSerializer
    pagination_class = PaginacaoCustomizada
    mensagem_sucesso = 'Solicitações de troca de titular listadas com sucesso.'

    def get_queryset(self):
        params = self.request.query_params
        filtros = {'status': params.get('status') or None, 'direcao': (params.get('direcao') or '').lower() or None}
        emprestimo_id = params.get('emprestimo_id')
        if emprestimo_id and emprestimo_id.isdigit():
            filtros['emprestimo_id'] = int(emprestimo_id)
        return SolicitacaoTrocaTitular().business.listar_para_usuario(self.request.user, **filtros)


@extend_schema(
    tags=['Infraestrutura · Solicitações de troca'],
    summary='Aceitar solicitação de troca de titular',
    description='''
    Encerra os itens abertos do empréstimo original e cria um novo empréstimo
    para o destinatário.

    **Permissões:** Somente o destinatário autenticado da solicitação pendente.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_201_CREATED: AceitarSolicitacaoTrocaTitularRespostaSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Solicitação inválida ou já processada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem autorização.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação não encontrada.'},
    },
)
class AceitarSolicitacaoTrocaTitularView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Solicitação aceita e titular alterado com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao, novo_emprestimo = SolicitacaoTrocaTitular().business.aceitar(kwargs['pk'], request.user)
        solicitacao = SolicitacaoTrocaTitular().business.obter_detalhada(solicitacao.pk)
        novo_emprestimo = Emprestimo().business.obter_detalhado(novo_emprestimo.pk)
        return {
            'dados': {
                'solicitacao': SolicitacaoTrocaTitularSerializer(solicitacao, context={'request': request}).data,
                'novo_emprestimo': EmprestimoSerializer(novo_emprestimo, context={'request': request}).data,
            },
            'status_code': status.HTTP_201_CREATED,
        }


class AcaoSolicitacaoTrocaTitularView(IsAuthenticatedMixin, BasicPostAPIView):
    serializer_class = SerializerVazio
    acao_business = None

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        solicitacao = getattr(SolicitacaoTrocaTitular().business, self.acao_business)(kwargs['pk'], request.user)
        solicitacao = SolicitacaoTrocaTitular().business.obter_detalhada(solicitacao.pk)
        return {'dados': SolicitacaoTrocaTitularSerializer(solicitacao, context={'request': request}).data}


@extend_schema(
    tags=['Infraestrutura · Solicitações de troca'],
    summary='Recusar solicitação de troca de titular',
    description='''
    Recusa uma solicitação pendente sem alterar o empréstimo.

    **Permissões:** Somente o destinatário autenticado da solicitação.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: SolicitacaoTrocaTitularSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Solicitação já processada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem autorização.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação não encontrada.'},
    },
)
class RecusarSolicitacaoTrocaTitularView(AcaoSolicitacaoTrocaTitularView):
    mensagem_sucesso = 'Solicitação recusada com sucesso.'
    acao_business = 'recusar'


@extend_schema(
    tags=['Infraestrutura · Solicitações de troca'],
    summary='Cancelar solicitação de troca de titular',
    description='''
    Cancela uma solicitação pendente sem alterar o empréstimo.

    **Permissões:** Somente o solicitante autenticado da solicitação.
    ''',
    request=SerializerVazio,
    responses={
        status.HTTP_200_OK: SolicitacaoTrocaTitularSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Solicitação já processada.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem autorização.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Solicitação não encontrada.'},
    },
)
class CancelarSolicitacaoTrocaTitularView(AcaoSolicitacaoTrocaTitularView):
    mensagem_sucesso = 'Solicitação cancelada com sucesso.'
    acao_business = 'cancelar'
