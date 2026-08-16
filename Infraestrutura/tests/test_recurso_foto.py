from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.common.textos.mensagens import RESPONSE_ERRO_INTERNO_SERVIDOR
from AppCore.core.exceptions.exceptions import NotFoundException
from Identidade.usuarios.models import Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.constantes import ANEXO_FOTO
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_cadastrar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'CAD_{usuario.cpf}', descricao='Cadastrador')
    setor = Setor.objects.create(sigla=f'S{usuario.cpf[-3:]}', nome='Setor Teste')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, cadastrar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


def criar_arquivo_imagem(nome='foto.jpg', tamanho=(600, 800), formato='JPEG'):
    buffer = BytesIO()
    Image.new('RGB', tamanho, color='red').save(buffer, format=formato)
    buffer.seek(0)
    content_type = {
        'JPEG': 'image/jpeg',
        'PNG': 'image/png',
        'WEBP': 'image/webp',
    }.get(formato, 'image/jpeg')
    return SimpleUploadedFile(nome, buffer.read(), content_type=content_type)


def criar_arquivo_gif(nome='foto.gif', tamanho=(600, 800), content_type='image/jpeg'):
    buffer = BytesIO()
    Image.new('RGB', tamanho, color='red').save(buffer, format='GIF')
    buffer.seek(0)
    return SimpleUploadedFile(nome, buffer.read(), content_type=content_type)


class RecursoFotoViewTest(APITestCase):

    def setUp(self):
        self.usuario_l1 = criar_usuario('41111111111', nome='Aluno Foto')
        self.cadastrador = conceder_capacidade_cadastrar(
            criar_usuario('42222222222', nome='Cadastrador Foto'),
        )
        self.token_l1 = obter_tokens(self.usuario_l1)
        self.token_cadastrador = obter_tokens(self.cadastrador)
        self.bloco = Bloco.objects.create(nome='Bloco Foto')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Foto')
        self.recurso = Recurso.objects.create(
            codigo='MID-FOTO-001',
            tipo=TipoRecurso.MIDIA,
            sala=self.sala,
        )
        self.url_list = reverse('infraestrutura:recursos-list')
        self.url_detail = reverse('infraestrutura:recurso-detail', kwargs={'pk': self.recurso.pk})
        self.url_foto = reverse('infraestrutura:recurso-foto', kwargs={'pk': self.recurso.pk})
        self.s3_key = f'Cortex/infraestrutura/recursos/fotos/{self.recurso.pk}/abc123.jpg'

    def _url_proxy_esperada(self, recurso_id=None, versao='abc123'):
        pk = recurso_id or self.recurso.pk
        path = reverse('infraestrutura:recurso-foto', kwargs={'pk': pk})
        return f'http://testserver{path}?v={versao}'

    def _mock_upload(self, prefixo, objeto_id, arquivo, **kwargs):
        return f'Cortex/infraestrutura/recursos/fotos/{objeto_id}/abc123.jpg'

    def test_criar_recurso_com_foto_paisagem_nao_persiste(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        codigo = 'MID-FOTO-PAISAGEM'
        resposta = self.client.post(
            self.url_list,
            {
                'codigo': codigo,
                'tipo': TipoRecurso.MIDIA,
                'foto': criar_arquivo_imagem(tamanho=(800, 600)),
            },
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('retrato', str(resposta.data).lower())
        self.assertFalse(Recurso.objects.filter(codigo=codigo).exists())

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_cadastrador_cria_recurso_com_foto_retrato(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_list,
            {
                'codigo': 'MID-FOTO-NOVO',
                'tipo': TipoRecurso.MIDIA,
                'foto': criar_arquivo_imagem(tamanho=(600, 800)),
            },
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        recurso_id = resposta.data['dados']['id']
        self.assertEqual(resposta.data['dados']['foto'], self._url_proxy_esperada(recurso_id))
        recurso = Recurso.objects.get(pk=recurso_id)
        self.assertEqual(recurso.foto, f'Cortex/infraestrutura/recursos/fotos/{recurso_id}/abc123.jpg')
        mock_upload.assert_called_once()

    def test_paisagem_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(tamanho=(800, 600))},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('retrato', str(resposta.data).lower())

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_s3_nao_configurado_retorna_500(self, mock_upload):
        mock_upload.side_effect = ValueError('Configuração de armazenamento S3 inválida.')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem()},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resposta.data['detail'], RESPONSE_ERRO_INTERNO_SERVIDOR)
        self.assertNotIn('Configuração', str(resposta.data))
        self.assertNotIn('S3', str(resposta.data))

    def test_quadrado_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(tamanho=(640, 640))},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('retrato', str(resposta.data).lower())

    def test_retrato_estreito_abaixo_do_minimo_apos_recorte_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(tamanho=(400, 800))},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('480', str(resposta.data))

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_recorte_central_3_4_antes_do_upload(self, mock_upload):
        capturado = {}

        def _upload(prefixo, objeto_id, arquivo, **kwargs):
            arquivo.seek(0)
            imagem = Image.open(arquivo)
            capturado['size'] = imagem.size
            return self._mock_upload(prefixo, objeto_id, arquivo)

        mock_upload.side_effect = _upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(tamanho=(600, 900))},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(capturado['size'], (600, 800))

    @patch('Infraestrutura.recursos.rules.TAMANHO_MAXIMO_FOTO_BYTES', 10)
    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_rejeita_foto_acima_de_3mb(self, mock_upload):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(nome='foto_grande.jpg')},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('3 MB', str(resposta.data))
        mock_upload.assert_not_called()

    def test_tipo_invalido_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        arquivo = SimpleUploadedFile('nota.txt', b'nao-e-imagem', content_type='text/plain')
        resposta = self.client.post(self.url_foto, {'foto': arquivo}, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_rejeita_gif_com_content_type_jpeg(self, mock_upload):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_gif(content_type='image/jpeg')},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Formato de imagem não suportado', str(resposta.data))
        mock_upload.assert_not_called()

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_aceita_png_valido_em_retrato(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(nome='foto.png', formato='PNG')},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        mock_upload.assert_called_once()

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_aceita_webp_valido_em_retrato(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(nome='foto.webp', formato='WEBP')},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        mock_upload.assert_called_once()

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_rejeita_gif_sem_content_type(self, mock_upload):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_gif(content_type='')},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        mock_upload.assert_not_called()

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_rejeita_bmp_sem_content_type(self, mock_upload):
        buffer = BytesIO()
        Image.new('RGB', (600, 800), color='red').save(buffer, format='BMP')
        buffer.seek(0)
        arquivo = SimpleUploadedFile('foto.bmp', buffer.read())
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        resposta = self.client.post(self.url_foto, {'foto': arquivo}, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        mock_upload.assert_not_called()

    def test_l1_nao_pode_enviar_nem_remover_foto(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem()},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
        resposta = self.client.delete(self.url_foto)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    @patch('AppCore.common.storage.s3.remover_objeto_s3')
    def test_cadastrador_envia_substitui_e_remove_foto(self, mock_remover, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')

        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem()},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['foto'], self._url_proxy_esperada())
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.foto, self.s3_key)

        chave_nova = f'Cortex/infraestrutura/recursos/fotos/{self.recurso.pk}/def456.jpg'
        mock_upload.side_effect = lambda prefixo, objeto_id, arquivo, **kwargs: chave_nova
        resposta = self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem(tamanho=(720, 960))},
            format='multipart',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        mock_remover.assert_called_once_with(
            self.s3_key,
            prefixo='Cortex/infraestrutura/recursos/fotos',
        )
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.foto, chave_nova)

        resposta = self.client.delete(self.url_foto)
        self.assertEqual(resposta.status_code, status.HTTP_204_NO_CONTENT)
        self.recurso.refresh_from_db()
        self.assertIsNone(self.recurso.foto)
        mock_remover.assert_called_with(
            chave_nova,
            prefixo='Cortex/infraestrutura/recursos/fotos',
        )

    @patch('AppCore.common.storage.s3.iterar_objeto_s3')
    def test_get_proxy_foto_sem_autenticacao(self, mock_iterar):
        self.recurso.foto = self.s3_key
        self.recurso.save()
        mock_iterar.return_value = (iter([b'fake-image']), 'image/jpeg')

        resposta = self.client.get(self.url_foto)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta['Content-Type'], 'image/jpeg')
        self.assertEqual(b''.join(resposta.streaming_content), b'fake-image')
        mock_iterar.assert_called_once_with(self.s3_key, content_type_padrao='image/jpeg')

    def test_get_proxy_foto_retorna_404_sem_foto(self):
        resposta = self.client.get(self.url_foto)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    @patch('AppCore.common.storage.s3.iterar_objeto_s3')
    def test_iterar_rejeita_chave_fora_do_prefixo(self, mock_iterar):
        chave_invalida = 'Cortex/outro/prefixo/x.jpg'
        with self.assertRaises(NotFoundException):
            ANEXO_FOTO.iterar(chave_invalida, content_type_padrao='image/jpeg')
        mock_iterar.assert_not_called()

    @patch('AppCore.common.storage.s3.remover_objeto_s3')
    def test_remover_ignora_chave_fora_do_prefixo(self, mock_remover):
        ANEXO_FOTO.remover('Cortex/outro/prefixo/x.jpg')
        mock_remover.assert_not_called()

    @patch('AppCore.common.storage.s3.iterar_objeto_s3')
    def test_get_proxy_foto_chave_fora_do_prefixo_retorna_404(self, mock_iterar):
        self.recurso.foto = 'Cortex/outro/prefixo/x.jpg'
        self.recurso.save()
        resposta = self.client.get(self.url_foto)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        mock_iterar.assert_not_called()

    @patch('AppCore.common.storage.s3.enviar_arquivo_s3')
    def test_listagem_e_detalhe_retornam_url_do_proxy(self, mock_upload):
        mock_upload.side_effect = self._mock_upload
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        self.client.post(
            self.url_foto,
            {'foto': criar_arquivo_imagem()},
            format='multipart',
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        detalhe = self.client.get(self.url_detail)
        self.assertEqual(detalhe.status_code, status.HTTP_200_OK)
        self.assertEqual(detalhe.data['dados']['foto'], self._url_proxy_esperada())

        listagem = self.client.get(self.url_list)
        self.assertEqual(listagem.status_code, status.HTTP_200_OK)
        item = next(
            registro for registro in listagem.data['dados']
            if registro['id'] == self.recurso.pk
        )
        self.assertEqual(item['foto'], self._url_proxy_esperada())
