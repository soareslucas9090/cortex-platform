import logging, os
from pathlib import Path

from django.db import transaction
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from AppCore.basics.mixins.mixins import IsAdminMixin, IsOwnerOrAdminMixin
from AppCore.basics.pagination.pagination import PaginacaoCustomizada
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicPatchAPIView,
    BasicPostAPIView,
    BasicRetrieveAPIView,
)

from .business import UsuarioBusiness
from .models import Usuario
from .serializers import (
    AtualizarUsuarioSerializer,
    CriarUsuarioSerializer,
    SerializerVazio,
    UsuarioSerializer,
    ArquivoImportacaoUsuariosSerializer,
    ImportacaoUsuariosPreviewResponseSerializer,
    ImportacaoUsuariosResponseSerializer,
    StatusImportacaoLoteSerializer,
)

logger = logging.getLogger(__name__)


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
class ListarUsuariosView(IsAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuários listados com sucesso.'

    def get_queryset(self):
        qs = Usuario.objects.all()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and ativo.lower() in ('true', 'false'):
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs


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
class CriarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/"""
    serializer_class = CriarUsuarioSerializer
    mensagem_sucesso = 'Usuário criado com sucesso.'

    def do_action_post(self, serializer_data, request):
        usuario = UsuarioBusiness().criar_usuario(
            cpf=serializer_data.get('cpf'),
            matricula=serializer_data.get('matricula'),
            nome=serializer_data['nome'],
            password=serializer_data.get('password'),
            email=serializer_data.get('email'),
            deficiencia=serializer_data.get('deficiencia', ''),
        )
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(usuario).data,
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
    """GET /identidade/usuarios/{pk}/"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    mensagem_sucesso = 'Usuário obtido com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj


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
class AtualizarUsuarioView(IsOwnerOrAdminMixin, BasicPatchAPIView):
    """PATCH /identidade/usuarios/{pk}/"""
    queryset = Usuario.objects.all()
    serializer_class = AtualizarUsuarioSerializer
    mensagem_sucesso = 'Usuário atualizado com sucesso.'

    def obter_usuario_dono(self, obj):
        return obj

    def do_action_patch(self, serializer_data, request, **kwargs):
        self.object.business.atualizar_dados(serializer_data)
        return {
            'mensagem': self.mensagem_sucesso,
            'dados': UsuarioSerializer(self.object).data,
        }


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
class DesativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/desativar/"""
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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Usuário não encontrado.'},
    },
)
class ReativarUsuarioView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/{pk}/reativar/"""
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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Arquivo modelo não encontrado.'},
    },
)
class BaixarModeloImportacaoUsuariosView(IsAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/importacao/modelo/"""
    serializer_class = SerializerVazio
    mensagem_sucesso = 'Modelo de importação localizado com sucesso.'

    def get(self, request, *args, **kwargs):
        base_dir = Path(__file__).resolve().parents[2]
        caminho_arquivo = base_dir / 'docs' / 'seeds' / 'import' / 'modelo-importacao-usuarios.ods'

        if not caminho_arquivo.exists() or not caminho_arquivo.is_file():
            raise Http404('Arquivo modelo de importação não encontrado.')

        return FileResponse(
            open(caminho_arquivo, 'rb'),
            as_attachment=True,
            filename=os.path.basename(caminho_arquivo),
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )


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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class PreVisualizarImportacaoUsuariosView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/importacao/pre-visualizar/"""
    parser_classes = (MultiPartParser,)
    serializer_class = ArquivoImportacaoUsuariosSerializer
    mensagem_sucesso = 'Pré-visualização concluída com sucesso.'

    def do_action_post(self, serializer_data, request):
        from .models import ImportacaoLote, StatusImportacao
        from rest_framework.exceptions import ValidationError

        if ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO).exists():
            raise ValidationError('Já existe uma importação em andamento. Aguarde o término.')

        resultado = UsuarioBusiness().pre_visualizar_importacao(
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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class ImportarUsuariosLoteView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/importacao/"""
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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
        status.HTTP_404_NOT_FOUND: {'description': 'Nenhuma importação encontrada.'},
    },
)
class StatusImportacaoLoteView(IsAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/importacao/status/"""
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
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class CancelarImportacaoView(IsAdminMixin, BasicPostAPIView):
    """POST /identidade/usuarios/importacao/cancelar/"""
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
    ''',
    responses={
        status.HTTP_200_OK: StatusImportacaoLoteSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Não autenticado.'},
        status.HTTP_403_FORBIDDEN: {'description': 'Sem permissão de administrador.'},
    },
)
class HistoricoImportacaoLoteView(IsAdminMixin, BasicGetAPIView):
    """GET /identidade/usuarios/importacao/historico/"""
    pagination_class = PaginacaoCustomizada
    serializer_class = StatusImportacaoLoteSerializer
    mensagem_sucesso = 'Histórico de importações listado com sucesso.'

    def get_queryset(self):
        from .models import ImportacaoLote
        return ImportacaoLote.objects.all()
