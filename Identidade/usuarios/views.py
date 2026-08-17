import logging

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AllowAnyMixin, IsAdminMixin, IsOwnerOrAdminMixin, IsAuthenticatedMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicPutAPIView,
    BasicRetrieveAPIView,
    BasicDeleteAPIView,
)

from .models import Usuario
from .serializers import (
    AdicionarItemColetivoSerializer,
    AtualizarUsuarioSerializer,
    AtualizarFotoPrimariaSerializer,
    AtualizarFotoSecundariaSerializer,
    CriarUsuarioSerializer,
    SerializerVazio,
    SubstituirUsuarioColetivoSerializer,
    UsuarioColetivoSerializer,
    UsuarioSerializer,
    ArquivoImportacaoUsuariosSerializer,
    ImportacaoUsuariosPreviewResponseSerializer,
    ImportacaoUsuariosResponseSerializer,
    StatusImportacaoLoteSerializer,
)
from .access import escopar_queryset_cortex
from .documentacao import PermissaoDocumentacao
from .querysets import queryset_usuario_com_perfis

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Identidade'],
    summary='Documentação de permissões por módulo',
    description='''
    Retorna a documentação narrativa e estruturada das permissões de cada módulo registrado.

    Inclui **cortex** (níveis L1–L3) e **infraestrutura** (capacidades booleanas, secoes
    estruturadas, acesso total de admin/superuser, elegibilidade do solicitante). Novos módulos
    entram automaticamente ao implementar `documentacao_<modulo>()`.

    **Permissões:** Qualquer usuário autenticado.

    **Manutenção:** toda alteração de regra de permissão deve atualizar o método
    `documentacao_<modulo>()` correspondente em `Identidade.usuarios.documentacao`.
    ''',
    responses={
        status.HTTP_200_OK: {'description': 'Documentação obtida com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
    },
)
class DocumentarPermissoesView(IsAuthenticatedMixin, BasicGetAPIView):
    """GET /cortex/identidade/permissoes/documentacao/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Documentação de permissões obtida com sucesso.'

    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'success',
            'mensagem': self.mensagem_sucesso,
            'dados': {
                'modulos': PermissaoDocumentacao.compilar_documentacao(),
            },
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Identidade'],
    summary='Listar usuários',
    description='''
    Retorna a lista paginada de usuários do sistema.

    **Permissões:** Autenticado. L2+ (LER_TUDO) lista todos; L1 (EDITAR_EU) vê apenas o próprio registro.

    **Query params:**
    - `ativo` (bool, opcional): filtra por status — `true` (ativos) ou `false` (inativos).
      Omitindo o parâmetro, retorna todos.
    - `nome` (str, opcional): filtra por parte do nome (ignorando maiúsculas e minúsculas).
    - `cpf` (str, opcional): filtra por parte do CPF.
    - `email` (str, opcional): filtra por parte do e-mail (ignorando maiúsculas e minúsculas).
    - `tipo_perfil` (str, opcional): filtra por tipo de perfil: `alunos` (ou `aluno`), `terceirizados` (ou `terceirizado`) ou `servidores` (ou `servidor`).
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
            'nome', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do nome do usuário.',
        ),
        OpenApiParameter(
            'cpf', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do CPF do usuário.',
        ),
        OpenApiParameter(
            'email', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por parte do e-mail do usuário.',
        ),
        OpenApiParameter(
            'tipo_perfil', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra por tipo de perfil: alunos, terceirizados ou servidores.',
            enum=['aluno', 'terceirizado', 'servidor'],
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: UsuarioSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ListarUsuariosView(IsOwnerOrAdminMixin, BasicGetAPIView):
    """GET /cortex/identidade/usuarios/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuários listados com sucesso.'

    def get_queryset(self):
        qs = queryset_usuario_com_perfis()
        qs = escopar_queryset_cortex(self.request.user, qs, campo_dono='id')

        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
            
        nome = self.request.query_params.get('nome')
        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
            
        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(cpf__icontains=cpf)
            
        email = self.request.query_params.get('email')
        if email:
            qs = qs.filter(email__unaccent__icontains=email)
            
        tipo_perfil = self.request.query_params.get('tipo_perfil')
        if tipo_perfil:
            tipo_perfil = tipo_perfil.lower()
            if tipo_perfil in ('aluno'):
                qs = qs.filter(aluno__isnull=False)
            elif tipo_perfil in ('terceirizado'):
                qs = qs.filter(terceirizado__isnull=False)
            elif tipo_perfil in ('servidor'):
                qs = qs.filter(servidor__isnull=False)
                
        return qs


@extend_schema(
    tags=['Identidade'],
    summary='Criar usuário',
    description='''
    Cria um novo usuário no sistema.

    **Permissões:** Apenas administradores.

    Não há auto-cadastro — usuários são sempre criados por administradores,
    individualmente ou em lote via JSON.

    **Normalização de Deficiência (campo `deficiencia`):**
    O campo é normalizado automaticamente no save (removendo acentos, convertendo para caixa baixa e substituindo espaços por `_`).
    - Opções válidas resultantes: `deficiencia_intelectual`, `deficiencia_visual`, `deficiencia_auditiva`, `deficiencia_multipla`, `deficiencia_fisica`.
    - Se a string enviada (ex: "Deficiência Múltipla") equivaler a uma das chaves após a normalização, ela será associada.
    - Se não houver correspondência, o valor será gravado como `null`.
    ''',
    request=CriarUsuarioSerializer,
    responses={
        status.HTTP_201_CREATED: UsuarioSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou CPF já cadastrado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class CriarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/"""
    serializer_class = CriarUsuarioSerializer
    mensagem_sucesso = 'Usuário criado com sucesso.'

    def do_action_post(self, serializer_data, request):
        usuario = Usuario().business.criar_usuario(
            cpf=serializer_data.get('cpf'),
            matricula=serializer_data.get('matricula'),
            nome=serializer_data['nome'],
            password=serializer_data.get('password'),
            email=serializer_data.get('email'),
            deficiencia=serializer_data.get('deficiencia', ''),
            colaborador_externo=serializer_data.get('colaborador_externo', False),
            usuario_coletivo=serializer_data.get('usuario_coletivo', False),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(usuario, context={'request': request}).data,
            'status_code': status.HTTP_201_CREATED,
        }


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
class DetalheUsuarioView(IsOwnerOrAdminMixin, BasicRetrieveAPIView):
    """GET /cortex/identidade/usuarios/{pk}/"""
    queryset = queryset_usuario_com_perfis()
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuário obtido com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj


@extend_schema(
    tags=['Identidade'],
    summary='Atualizar dados do usuário',
    description='''
    Atualiza parcialmente os dados básicos do usuário (nome, e-mail, deficiência,
    colaborador_externo, usuario_coletivo).

    A flag `usuario_coletivo` pode ser alterada aqui; o pool de associações é mantido
    em `GET/PUT /usuarios/{pk}/coletivo/`. Ao desativar a flag, o pool é limpo.

    **Permissões:** O próprio usuário ou administradores.

    CPF não é alterável neste endpoint.

    **Normalização de Deficiência (campo `deficiencia`):**
    O campo é normalizado automaticamente no save (removendo acentos, convertendo para caixa baixa e substituindo espaços por `_`).
    - Opções válidas resultantes: `deficiencia_intelectual`, `deficiencia_visual`, `deficiencia_auditiva`, `deficiencia_multipla`, `deficiencia_fisica`.
    - Se a string enviada (ex: "Deficiência Múltipla") equivaler a uma das chaves após a normalização, ela será associada.
    - Se não houver correspondência, o valor será gravado como `null`.
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
class AtualizarUsuarioView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/identidade/usuarios/{pk}/"""
    queryset = Usuario.objects.all()
    serializer_class = AtualizarUsuarioSerializer
    mensagem_sucesso = 'Usuário atualizado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_patch(self, serializer_data, request, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(self.object, context={'request': request}).data,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Obter configuração do usuário coletivo',
    description='''
    Retorna o pool do usuário coletivo (empresas, cargos, funções e setores).

    A flag `usuario_coletivo` é definida na criação/edição do usuário; as associações
    do pool são mantidas apenas por estes endpoints dedicados.

    **Permissões:** Administradores (L3).
    ''',
    responses={
        status.HTTP_200_OK: UsuarioColetivoSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ObterUsuarioColetivoView(IsAdminMixin, BasicRetrieveAPIView):
    """GET /cortex/identidade/usuarios/{pk}/coletivo/"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioColetivoSerializer
    mensagem_sucesso = 'Configuração do usuário coletivo obtida com sucesso.'

    def get_serializer(self, instance=None, *args, **kwargs):
        if instance is not None and hasattr(instance, 'helper'):
            instance = instance.helper.obter_configuracao_coletivo()
        return super().get_serializer(instance, *args, **kwargs)


@extend_schema(
    tags=['Identidade'],
    summary='Substituir pool do usuário coletivo',
    description='''
    Substitui integralmente as associações do pool (empresas, cargos, funções, setores).

    O usuário precisa estar com `usuario_coletivo=true`. Listas omitidas são tratadas
    como vazias nesta operação de substituição.

    **Permissões:** Administradores (L3).
    ''',
    request=SubstituirUsuarioColetivoSerializer,
    responses={
        status.HTTP_200_OK: UsuarioColetivoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou usuário não coletivo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class SubstituirUsuarioColetivoView(IsAdminMixin, BasicPutAPIView):
    """PUT /cortex/identidade/usuarios/{pk}/coletivo/"""
    queryset = Usuario.objects.all()
    serializer_class = SubstituirUsuarioColetivoSerializer
    mensagem_sucesso = 'Pool do usuário coletivo atualizado com sucesso.'

    def do_action_put(self, serializer_data, request, *args, **kwargs):
        dados = self.object.business.substituir_associacoes_coletivo(**serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioColetivoSerializer(dados).data,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Adicionar item ao pool do usuário coletivo',
    description='''
    Adiciona uma empresa, cargo, função ou setor ao pool.

    Body: `{"tipo": "empresa"|"cargo"|"funcao"|"setor", "id": <int>}`.

    **Permissões:** Administradores (L3).
    ''',
    request=AdicionarItemColetivoSerializer,
    responses={
        status.HTTP_201_CREATED: UsuarioColetivoSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Dados inválidos ou usuário não coletivo.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AdicionarItemColetivoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{pk}/coletivo/itens/"""
    serializer_class = AdicionarItemColetivoSerializer
    mensagem_sucesso = 'Item adicionado ao pool do usuário coletivo com sucesso.'

    def do_action_post(self, serializer_data, request, *args, **kwargs):
        from AppCore.core.exceptions.exceptions import NotFoundException

        usuario = Usuario.objects.filter(pk=self.kwargs['pk']).first()
        if usuario is None:
            raise NotFoundException('Usuário não encontrado.')
        dados = usuario.business.adicionar_associacao_coletiva(
            tipo=serializer_data['tipo'],
            item_id=serializer_data['id'],
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioColetivoSerializer(dados).data,
            'status_code': status.HTTP_201_CREATED,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Remover item do pool do usuário coletivo',
    description='''
    Remove uma empresa, cargo, função ou setor do pool.

    `tipo` deve ser `empresa`, `cargo`, `funcao` ou `setor`.

    **Permissões:** Administradores (L3).
    ''',
    responses={
        status.HTTP_204_NO_CONTENT: {'description': 'Item removido com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Tipo inválido ou item não associado.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário ou item não encontrado.'},
    },
)
class RemoverItemColetivoView(IsAdminMixin, BasicDeleteAPIView):
    """DELETE /cortex/identidade/usuarios/{pk}/coletivo/itens/{tipo}/{item_id}/"""
    queryset = Usuario.objects.all()
    mensagem_sucesso = 'Item removido do pool do usuário coletivo com sucesso.'

    def do_action_delete(self, request, *args, **kwargs):
        self.object.business.remover_associacao_coletiva(
            tipo=self.kwargs['tipo'],
            item_id=int(self.kwargs['item_id']),
        )


@extend_schema(
    tags=['Identidade'],
    summary='Atualizar foto primária do usuário',
    description='''
    Atualiza a URL da foto primária do usuário (origem em outros sistemas).

    **Permissões:** Apenas L3 (`EDITAR_TUDO`) / administradores.

    Para exibição no frontend, prefira `foto_secundaria` quando preenchida; caso contrário, use `foto`.
    ''',
    request=AtualizarFotoPrimariaSerializer,
    responses={
        status.HTTP_200_OK: UsuarioSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'URL inválida.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AtualizarFotoPrimariaView(IsAdminMixin, BasicPatchAPIView):
    """PATCH /cortex/identidade/usuarios/{pk}/foto-primaria/"""
    queryset = Usuario.objects.all()
    serializer_class = AtualizarFotoPrimariaSerializer
    mensagem_sucesso = 'Foto primária atualizada com sucesso.'

    def do_action_patch(self, serializer_data, request, **kwargs):
        self.object.business.atualizar_foto_primaria(serializer_data.get('foto'))
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(self.object, context={'request': request}).data,
        }


class ObterFotoSecundariaView(AllowAnyMixin, BasicRetrieveAPIView):
    """GET /cortex/identidade/usuarios/{pk}/foto-secundaria/"""
    queryset = Usuario.objects.all()
    serializer_class = SerializerVazio

    @extend_schema(
        tags=['Identidade'],
        summary='Obter foto secundária do usuário',
        description='''
        Retorna o arquivo de imagem da foto secundária via proxy da API.

        **Permissões:** Público (não requer autenticação).

        O bucket S3 permanece privado; este endpoint faz o stream da imagem para o navegador.
        ''',
        responses={
            status.HTTP_200_OK: {
                'description': 'Imagem retornada com sucesso.',
                'content': {
                    'image/jpeg': {},
                    'image/png': {},
                    'image/webp': {},
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Usuário ou foto não encontrados.'},
        },
    )
    @handle_exceptions
    def get(self, request, *args, **kwargs):
        stream, content_type = self.get_object().business.obter_stream_foto_secundaria()
        response = StreamingHttpResponse(stream, content_type=content_type)
        response['Cache-Control'] = 'public, max-age=86400'
        return response


@extend_schema(
    tags=['Identidade'],
    summary='Enviar foto secundária do usuário',
    description='''
    Faz upload da foto secundária para o S3 e persiste a referência no usuário.

    **Permissões:** O próprio usuário ou administradores.

    **Limites do arquivo:** JPEG, PNG ou WebP, com tamanho máximo de 3 MB.

    A resposta inclui `foto_secundaria` com a URL pública do proxy da API para exibição no frontend.
    Prefira `foto_secundaria` quando preenchida; caso contrário, use `foto`.
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'foto': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo de imagem (JPEG, PNG ou WebP, até 3 MB).',
                }
            },
            'required': ['foto'],
        }
    },
    responses={
        status.HTTP_200_OK: UsuarioSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Arquivo inválido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class AtualizarFotoSecundariaView(IsOwnerOrAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{pk}/foto-secundaria/"""
    queryset = Usuario.objects.all()
    parser_classes = (MultiPartParser,)
    serializer_class = AtualizarFotoSecundariaSerializer
    mensagem_sucesso = 'Foto secundária atualizada com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_post(self, serializer_data, request, **kwargs):
        usuario = self.get_object()
        usuario.business.atualizar_foto_secundaria(serializer_data['foto'])
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(usuario, context={'request': request}).data,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Remover foto secundária do usuário',
    description='''
    Remove a foto secundária do usuário e tenta apagar o arquivo correspondente no S3.

    **Permissões:** O próprio usuário ou administradores.
    ''',
    request=None,
    responses={
        status.HTTP_204_NO_CONTENT: {'description': 'Foto secundária removida com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class RemoverFotoSecundariaView(IsOwnerOrAdminMixin, BasicDeleteAPIView):
    """DELETE /cortex/identidade/usuarios/{pk}/foto-secundaria/"""
    queryset = Usuario.objects.all()
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Foto secundária removida com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_delete(self, request, *args, **kwargs):
        self.object.business.remover_foto_secundaria()


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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class DesativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{pk}/desativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário desativado com sucesso.'
    queryset = Usuario.objects.all()

    def do_action_post(self, serializer_data, request, **kwargs):
        self.get_object().business.desativar()


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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ReativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/{pk}/reativar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Usuário reativado com sucesso.'
    queryset = Usuario.objects.all()

    def do_action_post(self, serializer_data, request, **kwargs):
        self.get_object().business.reativar()


@extend_schema(
    tags=['Identidade'],
    summary='Baixar modelo da planilha de importação',
    description='''
    Realiza o download do arquivo modelo `.ods` utilizado como base para a importação em lote de usuários.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: {'description': 'Arquivo retornado com sucesso.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Arquivo modelo não encontrado.'},
    },
)
class BaixarModeloImportacaoUsuariosView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/identidade/usuarios/importacao/modelo/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Modelo de importação localizado com sucesso.'

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        stream, content_type = Usuario().business.obter_arquivo_modelo_importacao()
        response = StreamingHttpResponse(stream, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="modelo-importacao-usuarios.ods"'
        return response


@extend_schema(
    tags=['Identidade'],
    summary='Pré-visualizar importação em lote de usuários',
    description='''
    Recebe um arquivo `.ods` multiaba e executa a validação estrutural e prévia da importação,
    sem persistir dados no banco.

    **Permissões:** Apenas administradores.
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo para upload'
                }
            },
            'required': ['file']
        }
    },
    responses={
        status.HTTP_200_OK: ImportacaoUsuariosPreviewResponseSerializer,
        status.HTTP_400_BAD_REQUEST: {'description': 'Arquivo inválido ou estrutura inconsistente.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class PreVisualizarImportacaoUsuariosView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/importacao/pre-visualizar/"""
    parser_classes = (MultiPartParser,)
    serializer_class = ArquivoImportacaoUsuariosSerializer
    mensagem_sucesso = 'Pré-visualização concluída com sucesso.'

    def do_action_post(self, serializer_data, request):
        from .models import ImportacaoLote, StatusImportacao
        from rest_framework.exceptions import ValidationError

        if ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO).exists():
            raise ValidationError('Já existe uma importação em andamento. Aguarde o término.')

        resultado = Usuario().business.pre_visualizar_importacao(
            arquivo=serializer_data['file']
        )
        return {
            'mensagem': resultado.mensagem,
            'dados': {
                'sucesso': resultado.sucesso,
                'mensagem': resultado.mensagem,
                'resumo': resultado.resumo.__dict__,
                'erros': [erro.__dict__ for erro in resultado.erros],
                'metadados': resultado.metadados,
            },
            'status_code': status.HTTP_200_OK,
        }


from rest_framework import parsers


@extend_schema(
    tags=['Identidade'],
    summary='Importar usuários em lote (Assíncrono)',
    description='''
    Inicia o processo de importação em lote de usuários enviando o arquivo `.ods`.
    O processamento ocorre em background (Celery).

    **Permissões:** Apenas administradores.
    ''',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo para upload'
                }
            },
            'required': ['file']
        }
    },
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Importação enviada para fila de processamento.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Já existe uma importação em andamento ou arquivo inválido.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class ImportarUsuariosLoteView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/importacao/"""
    parser_classes = (MultiPartParser, parsers.FormParser)
    serializer_class = ArquivoImportacaoUsuariosSerializer
    mensagem_sucesso = 'Importação enviada para fila de processamento.'

    def do_action_post(self, serializer_data, request):
        from .models import ImportacaoLote, StatusImportacao
        from .tasks import processar_importacao_usuarios_task
        from rest_framework.exceptions import ValidationError

        if ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO).exists():
            raise ValidationError('Já existe uma importação em andamento. Aguarde o término.')

        importacao = ImportacaoLote.objects.create(
            arquivo=serializer_data['file']
        )
        
        # Faz upload para o S3 para compartilhar o arquivo com o container do worker Celery
        from .importacao.s3_helper import upload_importacao_to_s3
        upload_importacao_to_s3(importacao)
        
        transaction.on_commit(lambda: processar_importacao_usuarios_task.delay(importacao.id))

        return {
            'mensagem': self.mensagem_sucesso,
            'dados': {'importacao_id': importacao.id},
            'status_code': status.HTTP_202_ACCEPTED,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Consultar status da importação de usuários',
    description='''
    Retorna o status da importação atual ou da última importação realizada.
    Inclui a porcentagem de conclusão se estiver em andamento.

    **Permissões:** Apenas administradores.
    ''',
    responses={
        status.HTTP_200_OK: StatusImportacaoLoteSerializer,
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Nenhuma importação encontrada.'},
    },
)
class StatusImportacaoLoteView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/identidade/usuarios/importacao/status/"""
    serializer_class = StatusImportacaoLoteSerializer
    mensagem_sucesso = 'Status retornado com sucesso.'

    def get_queryset(self):
        from .models import ImportacaoLote
        return ImportacaoLote.objects.all()

    def get(self, request, *args, **kwargs):
        from django.http import Http404
        ultima_importacao = self.get_queryset().first()
        if not ultima_importacao:
            raise Http404('Nenhuma importação encontrada.')

        return Response(self.serializer_class(ultima_importacao).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Identidade'],
    summary='Cancelar importação em lote de usuários',
    description='''
    Cancela uma importação que esteja travada com status EM_ANDAMENTO.

    **Permissões:** Apenas administradores.
    ''',
    request=None,
    responses={
        status.HTTP_200_OK: {'description': 'Importação cancelada com sucesso.'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Não há importação em andamento.'},
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class CancelarImportacaoView(IsAdminMixin, BasicPostAPIView):
    """POST /cortex/identidade/usuarios/importacao/cancelar/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Importação cancelada com sucesso.'

    def do_action_post(self, serializer_data, request):
        from .models import ImportacaoLote, StatusImportacao
        from rest_framework.exceptions import ValidationError

        importacoes_travadas = ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO)
        
        if not importacoes_travadas.exists():
            raise ValidationError('Não há nenhuma importação em andamento para ser cancelada.')

        for importacao in importacoes_travadas:
            importacao.status = StatusImportacao.ERRO
            
            # Se já existir algum resultado, preserva e adiciona o erro fatal
            resultado = importacao.resultado_json or {}
            resultado['erro_fatal'] = 'Importação cancelada manualmente pelo administrador.'
            
            importacao.resultado_json = resultado
            importacao.save()
            
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': {},
            'status_code': status.HTTP_200_OK,
        }


@extend_schema(
    tags=['Identidade'],
    summary='Histórico de importações de usuários',
    description='''
    Retorna a lista paginada do histórico de importações de usuários.

    **Permissões:** Apenas administradores.

    **Query params:**
    - `status` (str, opcional): filtra pelo status da importação. Valores: EM_ANDAMENTO, CONCLUIDA, ERRO.
    - `paginacao` (int, opcional): tamanho da página, entre 1 e 100. Padrão: 10.
    ''',
    parameters=[
        OpenApiParameter(
            'status', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filtra pelo status (EM_ANDAMENTO, CONCLUIDA, ERRO).',
            enum=['EM_ANDAMENTO', 'CONCLUIDA', 'ERRO'],
        ),
        OpenApiParameter(
            'paginacao', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Tamanho da página (1–100, padrão 10).',
        ),
    ],
    responses={
        status.HTTP_200_OK: StatusImportacaoLoteSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão.'},
    },
)
class HistoricoImportacaoLoteView(IsAdminMixin, BasicGetAPIView):
    """GET /cortex/identidade/usuarios/importacao/historico/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = StatusImportacaoLoteSerializer
    mensagem_sucesso = 'Histórico de importações listado com sucesso.'

    def get_queryset(self):
        from .models import ImportacaoLote
        qs = ImportacaoLote.objects.all()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs
