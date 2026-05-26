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
from Identidade.usuarios.importacao_parser import ImportacaoUsuariosParser
from Identidade.usuarios.importacao_dtos import (
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


class ListarUsuariosViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
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

    def test_usuario_comum_nao_pode_listar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

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

    @patch('Identidade.usuarios.importacao_parser.get_data')
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

    @patch('Identidade.usuarios.importacao_parser.get_data')
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

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=BytesIO(b'test'))

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

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=BytesIO(b'test'))

        usuario.refresh_from_db()

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_atualizados, 1)
        self.assertEqual(usuario.nome, 'Nome Atualizado')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_retornar_erro_se_cpf_for_invalido(self, mock_parse):
        from Identidade.usuarios.business import UsuarioBusiness

        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='123',
                    nome='Usuário Inválido',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        business = UsuarioBusiness()
        resultado = business.importar_usuarios_em_lote(importacao_lote=BytesIO(b'test'))

        self.assertFalse(resultado.sucesso)
        self.assertEqual(resultado.resumo.usuarios_criados, 0)
        self.assertEqual(resultado.resumo.total_linhas_com_erro, 1)
        self.assertEqual(resultado.erros[0].aba, 'Usuario')


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
            '/identidade/usuarios/importacao/pre-visualizar/',
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
            '/identidade/usuarios/importacao/',
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
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
            '/identidade/usuarios/importacao/pre-visualizar/',
            {'file': arquivo},
            format='multipart',
        )

        self.assertIn(response.status_code, [401, 403])

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_endpoint_download_modelo_deve_retornar_404_se_arquivo_nao_existir(
        self,
        mock_is_file,
        mock_exists,
    ):
        mock_exists.return_value = False
        mock_is_file.return_value = False

        response = self.client.get('/identidade/usuarios/importacao/modelo/')
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

        response = self.client.post('/identidade/usuarios/importacao/cancelar/')
        
        self.assertEqual(response.status_code, 200)
        importacao.refresh_from_db()
        self.assertEqual(importacao.status, StatusImportacao.ERRO)
        self.assertIn('erro_fatal', importacao.resultado_json)

    def test_deve_retornar_erro_se_nao_ha_importacao_em_andamento(self):
        response = self.client.post('/identidade/usuarios/importacao/cancelar/')
        self.assertEqual(response.status_code, 400)
