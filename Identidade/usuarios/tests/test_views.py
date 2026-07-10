from io import BytesIO

from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Identidade.usuarios.importacao.importacao_parser import ImportacaoUsuariosParser
from Identidade.usuarios.importacao.importacao_dtos import (
    ArquivoImportacaoUsuariosDTO,
    LinhaUsuarioImportacaoDTO,
    ResumoImportacaoDTO,
    ResultadoImportacaoDTO,
)


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False, **kwargs):
    """Cria e retorna um Usuario para uso nos testes."""
    usuario = Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
        is_admin=is_admin,
        **kwargs,
    )
    return usuario


def criar_arquivo_imagem_teste(nome='foto.png'):
    """Retorna um arquivo de imagem válido para testes de upload."""
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new('RGB', (1, 1), color='red').save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(nome, buffer.read(), content_type='image/png')


class ListarUsuariosViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True, is_staff=True)
        self.usuario_comum = criar_usuario('00000000002', nome='Comum')
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.usuario_comum)
        self.url = reverse('identidade:usuario-list')

    def test_admin_lista_usuarios_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], 'success')
        self.assertIn('dados', resposta.data)

    def test_usuario_comum_ve_apenas_proprio(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(cpfs, [self.usuario_comum.cpf])

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_ativo_true_retorna_somente_ativos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        self.usuario_comum.ativo = False
        self.usuario_comum.save()
        resposta = self.client.get(self.url, {'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertNotIn(self.usuario_comum.cpf, cpfs)

    def test_filtro_ativo_false_retorna_somente_inativos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        self.usuario_comum.ativo = False
        self.usuario_comum.save()
        resposta = self.client.get(self.url, {'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertIn(self.usuario_comum.cpf, cpfs)

    def test_filtro_ativo_invalido_e_ignorado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url, {'ativo': 'invalido'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


class CriarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario_comum = criar_usuario('00000000002', nome='Comum')
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.usuario_comum)
        self.url = reverse('identidade:usuario-list')
        self.payload_valido = {
            'cpf': '11111111111',
            'nome': 'Novo Usuário',
            'password': 'Senha@123',
        }

    def test_admin_cria_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['dados']['cpf'], '11111111111')

    def test_usuario_comum_nao_pode_criar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cpf_duplicado_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'cpf': self.admin.cpf}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_senha_fraca_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'password': '123'}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cria_usuario_com_email_opcional(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'email': 'novo@exemplo.com'}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_admin_cria_usuario_apenas_com_matricula(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {
            'nome': 'Usuário Sem CPF',
            'matricula': 'MATR12345',
            'password': 'Senha@123',
        }
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertIsNone(resposta.data['dados']['cpf'])
        # Verificar que a matrícula foi criada no banco
        usuario_criado = Usuario.objects.get(id=resposta.data['dados']['id'])
        self.assertTrue(usuario_criado.matriculas.filter(matricula='MATR12345').exists())

    def test_criar_usuario_sem_cpf_e_sem_matricula_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {
            'nome': 'Usuário Sem Nada',
            'password': 'Senha@123',
        }
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('Identidade.usuarios.models.Usuario.objects.create_user')
    @patch('Identidade.usuarios.business.logger')
    @patch('AppCore.basics.decorators.decorators.logger')
    def test_database_integrity_error_does_not_mask_with_transaction_management_error(
        self, mock_decorator_logger, mock_business_logger, mock_create_user
    ):
        from django.db.utils import IntegrityError
        mock_create_user.side_effect = IntegrityError("Unique constraint violation")

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)



class DetalheUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Usuário')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario.pk})

    def test_admin_obtem_qualquer_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['cpf'], self.usuario.cpf)

    def test_proprio_usuario_obtem_seus_dados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_outro_usuario_nao_tem_acesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:usuario-detail', kwargs={'pk': 99999})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AtualizarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Original')
        self.outro = criar_usuario('00000000003', nome='Outro')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario.pk})

    def test_admin_atualiza_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'nome': 'Atualizado'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['nome'], 'Atualizado')

    def test_proprio_usuario_atualiza_seus_dados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'nome': 'Novo Nome'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_outro_usuario_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.patch(self.url, {'nome': 'Invasor'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'nome': 'Teste'})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_campos_parciais_sao_aceitos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'email': 'novo@exemplo.com'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


class DesativarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Ativo')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.url = reverse('identidade:usuario-desativar', kwargs={'pk': self.usuario.pk})

    def test_admin_desativa_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.ativo)

    def test_usuario_ja_inativo_retorna_400(self):
        self.usuario.ativo = False
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_comum_nao_pode_desativar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:usuario-desativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class ReativarUsuarioViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario = criar_usuario('00000000002', nome='Inativo')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.usuario.ativo = False
        self.usuario.save(update_fields=['ativo'])
        self.url = reverse('identidade:usuario-reativar', kwargs={'pk': self.usuario.pk})

    def test_admin_reativa_usuario_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.ativo)

    def test_usuario_ja_ativo_retorna_400(self):
        self.usuario.ativo = True
        self.usuario.save(update_fields=['ativo'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_comum_nao_pode_reativar(self):
        # Usuário inativo não consegue autenticar (JWT rejeita is_active=False) → 401
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse('identidade:usuario-reativar', kwargs={'pk': 99999})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class ImportacaoUsuariosParserTests(TestCase):

    @patch('Identidade.usuarios.importacao.importacao_parser.get_data')
    def test_deve_fazer_parse_da_aba_usuario_com_sucesso(self, mock_get_data):
        parser = ImportacaoUsuariosParser()

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        mock_get_data.return_value = {
            'Usuario': [
                [
                    'usuario_id\n(int, PK)',
                    'cpf\n(String)',
                    'nome\n(String)',
                    'foto\n(String)',
                    'deficiencia\n(String)',
                    'ativo\n(boolean)',
                    'ultimo_login\n(Date)',
                ],
                [1, '12345678901', 'Usuário Teste', '', '', True, None],
            ]
        }

        resultado = parser.parse(arquivo)

        self.assertEqual(len(resultado.usuarios), 1)
        self.assertEqual(resultado.usuarios[0].usuario_id_planilha, 1)
        self.assertEqual(resultado.usuarios[0].cpf, '12345678901')
        self.assertEqual(resultado.usuarios[0].nome, 'Usuário Teste')

    @patch('Identidade.usuarios.importacao.importacao_parser.get_data')
    def test_deve_ignorar_linhas_vazias(self, mock_get_data):
        parser = ImportacaoUsuariosParser()

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        mock_get_data.return_value = {
            'Usuario': [
                [
                    'usuario_id\n(int, PK)',
                    'cpf\n(String)',
                    'nome\n(String)',
                    'foto\n(String)',
                    'deficiencia\n(String)',
                    'ativo\n(boolean)',
                    'ultimo_login\n(Date)',
                ],
                ['', '', '', '', '', '', ''],
                [2, '98765432100', 'Outro Usuário', '', '', True, None],
            ]
        }

        resultado = parser.parse(arquivo)

        self.assertEqual(len(resultado.usuarios), 1)
        self.assertEqual(resultado.usuarios[0].usuario_id_planilha, 2)

    def test_deve_rejeitar_extensao_invalida(self):
        parser = ImportacaoUsuariosParser()

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.xlsx',
            b'fake-content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with self.assertRaises(Exception) as exc:
            parser.parse(arquivo)

        self.assertIn('Extensão', str(exc.exception))


class ImportacaoUsuariosBusinessPreviewTests(TestCase):

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_retornar_preview_com_sucesso(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Usuário Preview',
                )
            ]
        )
        mock_parse.return_value = estrutura

        business = UsuarioBusiness()
        resultado = business.pre_visualizar_importacao(arquivo=BytesIO(b'test'))

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.total_abas_processadas, 1)
        self.assertEqual(resultado.resumo.total_linhas_processadas, 1)
        self.assertEqual(len(resultado.erros), 0)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_preview_deve_retornar_erro_quando_nao_ha_usuarios(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO()
        mock_parse.return_value = estrutura

        business = UsuarioBusiness()
        resultado = business.pre_visualizar_importacao(arquivo=BytesIO(b'test'))

        self.assertFalse(resultado.sucesso)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].aba, '__arquivo__')


class ImportacaoUsuariosBusinessImportacaoTests(TestCase):

    def setUp(self):
        self.User = get_user_model()

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_importar_usuario_novo_com_sucesso(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Usuário Importado',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        from unittest.mock import MagicMock
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0
        
        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        self.assertEqual(self.User.objects.filter(cpf='12345678901').count(), 1)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_atualizar_usuario_existente(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        usuario = self.User.objects.create(
            cpf='12345678901',
            nome='Nome Antigo',
            ativo=True,
        )

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Nome Atualizado',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        from unittest.mock import MagicMock
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        usuario.refresh_from_db()

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_atualizados, 1)
        self.assertEqual(usuario.nome, 'Nome Atualizado')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_importar_usuario_sem_cpf_com_matricula_com_sucesso(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness
        from Identidade.usuarios.importacao.importacao_dtos import LinhaMatriculaImportacaoDTO

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='',
                    nome='Usuário Sem CPF Importado',
                    ativo=True,
                )
            ],
            matriculas=[
                LinhaMatriculaImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    matricula='MATR999888',
                    situacao='1',
                )
            ]
        )
        mock_parse.return_value = estrutura

        from unittest.mock import MagicMock
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0
        
        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        
        # Verificar que o usuário foi criado e não possui CPF
        usuario_criado = self.User.objects.filter(nome='Usuário Sem CPF Importado').first()
        self.assertIsNotNone(usuario_criado)
        self.assertIsNone(usuario_criado.cpf)
        
        # Verificar que a matrícula correspondente foi criada
        self.assertTrue(usuario_criado.matriculas.filter(matricula='MATR999888').exists())

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_retornar_erro_se_cpf_for_invalido(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12',
                    nome='Usuário Inválido',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        from unittest.mock import MagicMock
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        self.assertFalse(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_criados, 0)
        self.assertEqual(resultado.resumo.total_linhas_com_erro, 1)
        self.assertEqual(resultado.erros[0].aba, 'Usuario')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_importar_usuario_com_cpf_curto_preenchendo_zeros(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='123',
                    nome='Usuário CPF Curto',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        from unittest.mock import MagicMock
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        self.assertEqual(self.User.objects.filter(cpf='00000000123').count(), 1)



class ImportacaoUsuariosApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

        self.admin = self.User.objects.create(
            cpf='11122233344',
            nome='Administrador',
            ativo=True,
            is_admin=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.admin)

    @patch('Identidade.usuarios.views.UsuarioBusiness.pre_visualizar_importacao')
    def test_endpoint_preview_deve_retornar_200(self, mock_preview):
        mock_preview.return_value = ResultadoImportacaoDTO(
            sucesso=True,
            mensagem='Pré-visualização concluída.',
            resumo=ResumoImportacaoDTO(
                total_abas_processadas=1,
                total_linhas_processadas=1,
                total_linhas_com_erro=0,
            ),
            erros=[],
            metadados={'modo': 'preview'},
        )

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('identidade:usuarios-importacao-pre-visualizar'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('dados', response.data)

    @patch('Identidade.usuarios.views.UsuarioBusiness.importar_usuarios_em_lote')
    def test_endpoint_importacao_deve_retornar_200(self, mock_importar):
        mock_importar.return_value = ResultadoImportacaoDTO(
            sucesso=True,
            mensagem='Importação concluída com sucesso.',
            resumo=ResumoImportacaoDTO(
                total_abas_processadas=1,
                total_linhas_processadas=1,
                total_linhas_com_erro=0,
                usuarios_criados=1,
            ),
            erros=[],
            metadados={'modo': 'importacao'},
        )

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('identidade:usuarios-importacao'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('dados', response.data)

    def test_endpoint_preview_deve_exigir_autenticacao(self):
        self.client.force_authenticate(user=None)

        arquivo = SimpleUploadedFile(
            'modelo-importacao-usuarios.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('identidade:usuarios-importacao-pre-visualizar'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertIn(response.status_code, [401, 403])

    @patch('boto3.client')
    def test_endpoint_download_modelo_sucesso(self, mock_boto_client):
        from unittest.mock import MagicMock
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        def mock_download(bucket, key, fileobj):
            fileobj.write(b'fake ods spreadsheet content')
            
        mock_s3.download_fileobj.side_effect = mock_download
        
        response = self.client.get(reverse('identidade:usuarios-importacao-modelo'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/vnd.oasis.opendocument.spreadsheet')
        self.assertEqual(b''.join(response.streaming_content), b'fake ods spreadsheet content')

    @patch('boto3.client')
    @patch('Identidade.usuarios.views.logger')
    def test_endpoint_download_modelo_falha_s3(self, mock_views_logger, mock_boto_client):
        from unittest.mock import MagicMock
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.download_fileobj.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}},
            operation_name='GetObject'
        )
        
        response = self.client.get(reverse('identidade:usuarios-importacao-modelo'))
        self.assertEqual(response.status_code, 404)


class CancelarImportacaoViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

        self.admin = self.User.objects.create(
            cpf='11122233344',
            nome='Administrador',
            ativo=True,
            is_admin=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_deve_cancelar_importacao_em_andamento(self):
        from Identidade.usuarios.models import ImportacaoLote, StatusImportacao
        importacao = ImportacaoLote.objects.create(
            status=StatusImportacao.EM_ANDAMENTO,
            arquivo='dummy.ods',
        )

        response = self.client.post(reverse('identidade:usuarios-importacao-cancelar'))
        
        self.assertEqual(response.status_code, 200)
        importacao.refresh_from_db()
        self.assertEqual(importacao.status, StatusImportacao.ERRO)
        self.assertIn('erro_fatal', importacao.resultado_json)

    def test_deve_retornar_erro_se_nao_ha_importacao_em_andamento(self):
        response = self.client.post(reverse('identidade:usuarios-importacao-cancelar'))
        self.assertEqual(response.status_code, 400)


class AutenticacaoUsuarioTest(APITestCase):

    def setUp(self):
        from Identidade.matriculas.models import Matricula
        from Identidade.matriculas.choices import SituacaoMatricula
        self.User = get_user_model()
        self.url = reverse('auth:token-jwt:login')

        # Criar usuário com CPF e testar login
        self.usuario_cpf = self.User.objects.create_user(
            cpf='22222222222',
            nome='Usuario CPF',
            password='Password123'
        )

        # Criar usuário apenas com matrícula e testar login
        self.usuario_matricula = self.User.objects.create_user(
            cpf=None,
            nome='Usuario Matricula',
            password='PasswordMatricula123'
        )
        Matricula.objects.create(
            usuario=self.usuario_matricula,
            matricula='MATRICULA999',
            situacao=SituacaoMatricula.ATIVA
        )

    def test_login_por_cpf_com_sucesso(self):
        payload = {
            'login': '22222222222',
            'password': 'Password123'
        }
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('access', resposta.data)

    def test_login_por_matricula_com_sucesso(self):
        payload = {
            'login': 'MATRICULA999',
            'password': 'PasswordMatricula123'
        }
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('access', resposta.data)

    def test_login_por_matricula_inativa_falha(self):
        from Identidade.matriculas.models import Matricula
        from Identidade.matriculas.choices import SituacaoMatricula

        # Inativar a matrícula
        matricula_obj = self.usuario_matricula.matriculas.first()
        matricula_obj.situacao = SituacaoMatricula.INATIVA
        matricula_obj.save()

        payload = {
            'login': 'MATRICULA999',
            'password': 'PasswordMatricula123'
        }
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)


class UsuarioPermissoesTest(APITestCase):

    def setUp(self):
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao

        # Criar objetos básicos para os perfis
        self.cargo = Cargo.objects.create(nome='Cargo de Teste')
        self.empresa = EmpresaInstituicao.objects.create(nome='Empresa de Teste')

    def test_usuario_somente_aluno_tem_permissao_editar_eu(self):
        from Academico.alunos.models import Aluno

        user = criar_usuario('11111111111', nome='Aluno Teste')
        Aluno.objects.create(usuario=user, ativo=True)

        self.assertEqual(user.permissoes, {'cortex': 'EDITAR_EU'})

    def test_usuario_servidor_ativo_tem_permissao_ler_tudo(self):
        from PessoasInstitucionais.servidores.models import Servidor

        user = criar_usuario('22222222222', nome='Servidor Teste')
        Servidor.objects.create(usuario=user, cargo=self.cargo, categoria=1, ativo=True)

        self.assertEqual(user.permissoes, {'cortex': 'LER_TUDO'})

    def test_usuario_servidor_inativo_e_aluno_tem_permissao_editar_eu(self):
        from Academico.alunos.models import Aluno
        from PessoasInstitucionais.servidores.models import Servidor

        user = criar_usuario('33333333333', nome='Servidor Inativo')
        Aluno.objects.create(usuario=user, ativo=True)
        Servidor.objects.create(usuario=user, cargo=self.cargo, categoria=1, ativo=False)

        self.assertEqual(user.permissoes, {'cortex': 'EDITAR_EU'})

    def test_usuario_terceirizado_ativo_tem_permissao_ler_tudo(self):
        from PessoasInstitucionais.terceirizados.models import Terceirizado

        user = criar_usuario('44444444444', nome='Terceirizado Teste')
        Terceirizado.objects.create(usuario=user, empresa_instituicao=self.empresa, cargo=self.cargo, ativo=True)

        self.assertEqual(user.permissoes, {'cortex': 'LER_TUDO'})

    def test_usuario_staff_tem_permissao_editar_tudo(self):
        user = criar_usuario('55555555555', nome='Staff Teste')
        user.is_staff = True
        user.save()

        self.assertEqual(user.permissoes, {'cortex': 'EDITAR_TUDO'})

    def test_login_retorna_permissoes_no_payload(self):
        user = criar_usuario('66666666666', nome='Login Perms Teste', password='Password123')
        user.is_staff = True
        user.save()

        url_login = reverse('auth:token-jwt:login')
        resposta = self.client.post(url_login, {'login': '66666666666', 'password': 'Password123'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('permissoes', resposta.data)
        self.assertEqual(resposta.data['permissoes'], {'cortex': 'EDITAR_TUDO'})

    def test_endpoint_me_retorna_permissoes(self):
        user = criar_usuario('77777777777', nome='Me Perms Teste', password='Password123')
        token = obter_tokens(user)

        url_me = reverse('auth:token-jwt:me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resposta = self.client.get(url_me)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        
        data = resposta.data['dados'] if 'dados' in resposta.data else resposta.data
        self.assertIn('permissoes', data)
        self.assertEqual(data['permissoes'], {'cortex': 'EDITAR_EU'})


class CortexPermissoesEscopoViewTest(APITestCase):

    def setUp(self):
        from Academico.alunos.models import Aluno
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
        from PessoasInstitucionais.servidores.models import Servidor

        self.cargo = Cargo.objects.create(nome='Cargo Teste')
        self.empresa = EmpresaInstituicao.objects.create(nome='Empresa Teste')

        self.aluno_user = criar_usuario('88888888881', nome='Aluno Escopo')
        Aluno.objects.create(usuario=self.aluno_user, ativo=True)

        self.servidor_user = criar_usuario('88888888882', nome='Servidor Escopo')
        Servidor.objects.create(
            usuario=self.servidor_user, cargo=self.cargo, categoria=1, ativo=True,
        )

        self.staff_user = criar_usuario('88888888883', nome='Staff Escopo', is_staff=True)

        self.token_aluno = obter_tokens(self.aluno_user)
        self.token_servidor = obter_tokens(self.servidor_user)
        self.token_staff = obter_tokens(self.staff_user)

    def test_l1_lista_apenas_proprio_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_aluno}')
        resposta = self.client.get(reverse('identidade:usuario-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(cpfs, [self.aluno_user.cpf])

    def test_l2_lista_todos_usuarios(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_servidor}')
        resposta = self.client.get(reverse('identidade:usuario-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resposta.data['dados']), 1)

    def test_l1_nao_lista_empresas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_aluno}')
        resposta = self.client.get(reverse('pessoas-institucionais:empresa-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])

    def test_l2_lista_empresas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_servidor}')
        resposta = self.client.get(reverse('pessoas-institucionais:empresa-list'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resposta.data['dados']), 1)

    def test_l1_pode_listar_catalogo_setores(self):
        from Organizacional.setores.models import Setor

        Setor.objects.create(sigla='TST', nome='Setor Teste')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_aluno}')
        resposta = self.client.get(reverse('organizacional:setores'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resposta.data['dados']), 1)

    def test_l2_nao_pode_criar_setor(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_servidor}')
        resposta = self.client.post(
            reverse('organizacional:setores'),
            {'sigla': 'NOV', 'nome': 'Novo Setor'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l3_pode_criar_setor(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_staff}')
        resposta = self.client.post(
            reverse('organizacional:setores'),
            {'sigla': 'STF', 'nome': 'Setor Staff'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)


class DocumentarPermissoesViewTest(APITestCase):

    def setUp(self):
        self.usuario = criar_usuario('99999999999', nome='Docs Teste')
        self.token = obter_tokens(self.usuario)
        self.url = reverse('identidade:permissoes-documentacao')

    def test_autenticado_obtem_documentacao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        modulos = resposta.data['dados']['modulos']
        self.assertEqual(len(modulos), 1)
        self.assertEqual(modulos[0]['chave'], 'cortex')
        self.assertEqual(len(modulos[0]['niveis']), 3)
        self.assertGreaterEqual(len(modulos[0]['exemplos']), 1)
        self.assertIn('texto', modulos[0])

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)


class AtualizarFotoPrimariaViewTest(APITestCase):

    def setUp(self):
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.servidores.models import Servidor

        self.admin = criar_usuario('10000000001', nome='Admin Foto', is_admin=True)
        self.usuario = criar_usuario('10000000002', nome='Usuario Foto')
        self.outro = criar_usuario('10000000003', nome='Outro Foto')

        cargo = Cargo.objects.create(nome='Cargo Foto')
        self.servidor = criar_usuario('10000000004', nome='Servidor Foto')
        Servidor.objects.create(usuario=self.servidor, cargo=cargo, categoria=1, ativo=True)

        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.token_servidor = obter_tokens(self.servidor)
        self.url = reverse('identidade:usuario-foto-primaria', kwargs={'pk': self.usuario.pk})
        self.url_primaria_valida = 'https://sistema-externo.example/fotos/usuario.jpg'

    def test_admin_atualiza_foto_primaria(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'foto': self.url_primaria_valida}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto'], self.url_primaria_valida)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.foto, self.url_primaria_valida)

    def test_admin_pode_limpar_foto_primaria(self):
        self.usuario.foto = self.url_primaria_valida
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'foto': None}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertIsNone(self.usuario.foto)

    def test_usuario_comum_nao_pode_atualizar_foto_primaria(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.patch(self.url, {'foto': self.url_primaria_valida}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_servidor_l2_nao_pode_atualizar_foto_primaria(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_servidor}')
        resposta = self.client.patch(self.url, {'foto': self.url_primaria_valida}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_url_invalida_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'foto': 'nao-e-uma-url'}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_detalhe_retorna_foto_primaria(self):
        self.usuario.foto = self.url_primaria_valida
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        url_detalhe = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario.pk})
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto'], self.url_primaria_valida)


class AtualizarFotoSecundariaViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('20000000001', nome='Admin Foto 2', is_admin=True)
        self.usuario = criar_usuario('20000000002', nome='Usuario Foto 2')
        self.outro = criar_usuario('20000000003', nome='Outro Foto 2')
        self.token_admin = obter_tokens(self.admin)
        self.token_usuario = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url = reverse('identidade:usuario-foto-secundaria', kwargs={'pk': self.usuario.pk})
        self.url_primaria = 'https://sistema-externo.example/fotos/usuario.jpg'
        self.url_secundaria = 'https://bucket.example/Cortex/usuarios/fotos/2/abc.jpg'
        self.arquivo_imagem = criar_arquivo_imagem_teste()

    def _mock_upload(self, usuario_id, arquivo):
        return self.url_secundaria

    @patch('Identidade.usuarios.fotos.s3_helper.upload_foto_secundaria')
    def test_dono_envia_foto_secundaria(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.post(self.url, {'foto': self.arquivo_imagem}, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto_secundaria'], self.url_secundaria)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.foto_secundaria, self.url_secundaria)
        mock_upload.assert_called_once()

    @patch('Identidade.usuarios.fotos.s3_helper.upload_foto_secundaria')
    def test_admin_pode_enviar_foto_secundaria_de_outro_usuario(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'foto': self.arquivo_imagem}, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto_secundaria'], self.url_secundaria)

    def test_outro_usuario_nao_pode_enviar_foto_secundaria(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_outro}')
        resposta = self.client.post(self.url, {'foto': self.arquivo_imagem}, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    @patch('Identidade.usuarios.fotos.s3_helper.remover_foto_secundaria_do_s3')
    def test_dono_remove_foto_secundaria(self, mock_remover):
        self.usuario.foto_secundaria = self.url_secundaria
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        resposta = self.client.delete(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_204_NO_CONTENT)
        self.usuario.refresh_from_db()
        self.assertIsNone(self.usuario.foto_secundaria)
        mock_remover.assert_called_once_with(self.url_secundaria)

    def test_get_detalhe_retorna_ambas_fotos(self):
        self.usuario.foto = self.url_primaria
        self.usuario.foto_secundaria = self.url_secundaria
        self.usuario.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        url_detalhe = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario.pk})
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto'], self.url_primaria)
        self.assertEqual(resposta.data['dados']['foto_secundaria'], self.url_secundaria)

    def test_patch_usuario_nao_atualiza_campo_foto(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario}')
        url_detalhe = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario.pk})
        resposta = self.client.patch(url_detalhe, {'foto': self.url_primaria}, format='json')
        self.assertIn(resposta.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))
        self.usuario.refresh_from_db()
        self.assertIsNone(self.usuario.foto)
