from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from Infraestrutura.blocos.models import Bloco
from Infraestrutura.importacoes.importacao.importacao_dtos import (
    ArquivoImportacaoInfraestruturaDTO,
    LinhaBlocoImportacaoDTO,
    LinhaRecursoImportacaoDTO,
    LinhaSalaImportacaoDTO,
    ResumoImportacaoDTO,
    ResultadoImportacaoDTO,
)
from Infraestrutura.importacoes.importacao.importacao_parser import (
    ImportacaoInfraestruturaParser,
)
from Infraestrutura.importacoes.models import ImportacaoLote, StatusImportacao
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala
from Infraestrutura.tests.test_cadastro_views import (
    conceder_capacidade_cadastrar,
    criar_usuario,
    obter_tokens,
)


class ImportacaoInfraestruturaParserTests(TestCase):

    @patch('Infraestrutura.importacoes.importacao.importacao_parser.get_data')
    def test_deve_fazer_parse_das_tres_abas(self, mock_get_data):
        parser = ImportacaoInfraestruturaParser()
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )
        mock_get_data.return_value = {
            'Bloco': [
                ['bloco_id', 'nome'],
                [1, 'Bloco A'],
            ],
            'Sala': [
                ['sala_id', 'bloco_id', 'nome'],
                [1, 1, 'Sala 101'],
            ],
            'Recurso': [
                ['sala_id', 'descricao', 'codigo', 'avaria', 'tipo', 'foto'],
                [1, 'Projetor', 'PROJ-01', 'não', 'midia', ''],
            ],
        }

        resultado = parser.parse(arquivo)

        self.assertEqual(len(resultado.blocos), 1)
        self.assertEqual(resultado.blocos[0].nome, 'Bloco A')
        self.assertEqual(len(resultado.salas), 1)
        self.assertEqual(resultado.salas[0].nome, 'Sala 101')
        self.assertEqual(len(resultado.recursos), 1)
        self.assertEqual(resultado.recursos[0].codigo, 'PROJ-01')
        self.assertFalse(resultado.recursos[0].em_avaria)

    @patch('Infraestrutura.importacoes.importacao.importacao_parser.get_data')
    def test_deve_normalizar_nomes_de_abas_para_minusculo(self, mock_get_data):
        parser = ImportacaoInfraestruturaParser()
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )
        mock_get_data.return_value = {
            'BLOCO': [
                ['bloco_id', 'nome'],
                [1, 'Bloco B'],
            ],
        }

        resultado = parser.parse(arquivo)

        self.assertEqual(len(resultado.blocos), 1)
        self.assertEqual(resultado.blocos[0].nome, 'Bloco B')

    def test_deve_rejeitar_extensao_invalida(self):
        parser = ImportacaoInfraestruturaParser()
        arquivo = SimpleUploadedFile(
            'modelo.xlsx',
            b'fake-content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with self.assertRaises(Exception):
            parser.parse(arquivo)


class ImportacaoInfraestruturaBusinessPreviewTests(TestCase):

    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_deve_retornar_preview_com_sucesso(self, mock_parse):
        estrutura = ArquivoImportacaoInfraestruturaDTO(
            blocos=[
                LinhaBlocoImportacaoDTO(
                    numero_linha=2,
                    bloco_id_planilha=1,
                    nome='Bloco Preview',
                )
            ]
        )
        mock_parse.return_value = estrutura

        resultado = ImportacaoLote().business.pre_visualizar_importacao(arquivo=BytesIO(b'test'))

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.total_abas_processadas, 1)
        self.assertEqual(resultado.resumo.total_linhas_processadas, 1)
        self.assertEqual(resultado.metadados['modo'], 'preview')

    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_preview_deve_retornar_erro_quando_nao_ha_blocos(self, mock_parse):
        mock_parse.return_value = ArquivoImportacaoInfraestruturaDTO()

        resultado = ImportacaoLote().business.pre_visualizar_importacao(arquivo=BytesIO(b'test'))

        self.assertFalse(resultado.sucesso)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].aba, '__arquivo__')


class ImportacaoInfraestruturaBusinessImportacaoTests(TestCase):

    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_deve_criar_bloco_sala_e_recurso(self, mock_parse):
        estrutura = ArquivoImportacaoInfraestruturaDTO(
            blocos=[
                LinhaBlocoImportacaoDTO(numero_linha=2, bloco_id_planilha=1, nome='Bloco Novo'),
            ],
            salas=[
                LinhaSalaImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    bloco_id_planilha=1,
                    nome='Sala Nova',
                ),
            ],
            recursos=[
                LinhaRecursoImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    descricao='Chave principal',
                    codigo='CHV-001',
                    em_avaria=False,
                    tipo=TipoRecurso.CHAVE,
                    foto_url='',
                ),
            ],
        )
        mock_parse.return_value = estrutura
        importacao = self._criar_importacao()

        resultado = ImportacaoLote().business.importar_infraestrutura_em_lote(importacao)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.blocos_criados, 1)
        self.assertEqual(resultado.resumo.salas_criadas, 1)
        self.assertEqual(resultado.resumo.recursos_criados, 1)
        self.assertEqual(Bloco.objects.filter(nome='Bloco Novo').count(), 1)
        self.assertEqual(Sala.objects.filter(nome='Sala Nova').count(), 1)
        self.assertEqual(Recurso.objects.filter(codigo='CHV-001').count(), 1)

    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_deve_atualizar_bloco_sala_e_recurso_existentes(self, mock_parse):
        bloco = Bloco.objects.create(nome='Bloco Existente', ativo=True)
        sala = Sala.objects.create(bloco=bloco, nome='Sala Existente', ativo=True)
        Recurso.objects.create(
            codigo='REC-001',
            tipo=TipoRecurso.MIDIA,
            sala=sala,
            descricao='Antiga',
            ativo=True,
        )

        estrutura = ArquivoImportacaoInfraestruturaDTO(
            blocos=[
                LinhaBlocoImportacaoDTO(numero_linha=2, bloco_id_planilha=1, nome='Bloco Existente'),
            ],
            salas=[
                LinhaSalaImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    bloco_id_planilha=1,
                    nome='Sala Existente',
                ),
            ],
            recursos=[
                LinhaRecursoImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    descricao='Atualizada',
                    codigo='rec-001',
                    em_avaria=True,
                    tipo=TipoRecurso.MIDIA,
                    foto_url='',
                ),
            ],
        )
        mock_parse.return_value = estrutura
        importacao = self._criar_importacao()

        resultado = ImportacaoLote().business.importar_infraestrutura_em_lote(importacao)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.blocos_atualizados, 1)
        self.assertEqual(resultado.resumo.salas_atualizadas, 1)
        self.assertEqual(resultado.resumo.recursos_atualizados, 1)
        recurso = Recurso.objects.get(codigo='REC-001')
        self.assertEqual(recurso.descricao, 'Atualizada')
        self.assertTrue(recurso.em_avaria)

    @patch('Infraestrutura.importacoes.business.baixar_imagem_de_url')
    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_foto_com_sucesso_atualiza_recurso(self, mock_parse, mock_baixar):
        bloco = Bloco.objects.create(nome='Bloco Foto')
        sala = Sala.objects.create(bloco=bloco, nome='Sala Foto')
        mock_parse.return_value = ArquivoImportacaoInfraestruturaDTO(
            blocos=[
                LinhaBlocoImportacaoDTO(numero_linha=2, bloco_id_planilha=1, nome='Bloco Foto'),
            ],
            salas=[
                LinhaSalaImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    bloco_id_planilha=1,
                    nome='Sala Foto',
                ),
            ],
            recursos=[
                LinhaRecursoImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    descricao='Com foto',
                    codigo='FOTO-OK',
                    tipo=TipoRecurso.MIDIA,
                    foto_url='https://example.com/foto.jpg',
                ),
            ],
        )
        mock_baixar.return_value = SimpleUploadedFile(
            'foto.jpg', b'fake-image', content_type='image/jpeg'
        )
        importacao = self._criar_importacao()

        with patch(
            'Infraestrutura.recursos.business.RecursoBusiness.atualizar_foto',
            return_value=None,
        ) as mock_atualizar_foto:
            resultado = ImportacaoLote().business.importar_infraestrutura_em_lote(importacao)

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.recursos_criados, 1)
        mock_baixar.assert_called_once()
        mock_atualizar_foto.assert_called_once()

    @patch('Infraestrutura.importacoes.business.baixar_imagem_de_url')
    @patch('Infraestrutura.importacoes.business.ImportacaoInfraestruturaParser.parse')
    def test_falha_na_foto_nao_impede_persistencia_do_recurso(self, mock_parse, mock_baixar):
        mock_parse.return_value = ArquivoImportacaoInfraestruturaDTO(
            blocos=[
                LinhaBlocoImportacaoDTO(numero_linha=2, bloco_id_planilha=1, nome='Bloco Foto Fail'),
            ],
            salas=[
                LinhaSalaImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    bloco_id_planilha=1,
                    nome='Sala Foto Fail',
                ),
            ],
            recursos=[
                LinhaRecursoImportacaoDTO(
                    numero_linha=2,
                    sala_id_planilha=1,
                    descricao='Sem foto',
                    codigo='FOTO-FAIL',
                    tipo=TipoRecurso.MIDIA,
                    foto_url='https://example.com/invalida.jpg',
                ),
            ],
        )
        mock_baixar.side_effect = Exception('Falha no download')
        importacao = self._criar_importacao()

        resultado = ImportacaoLote().business.importar_infraestrutura_em_lote(importacao)

        self.assertEqual(Recurso.objects.filter(codigo='FOTO-FAIL').count(), 1)
        self.assertEqual(resultado.resumo.recursos_criados, 1)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].codigo, 'erro_foto')
        self.assertEqual(resultado.resumo.total_linhas_com_erro, 0)

    def _criar_importacao(self):
        return ImportacaoLote.objects.create(
            status=StatusImportacao.EM_ANDAMENTO,
            arquivo='test.ods',
        )


class ImportacaoInfraestruturaApiTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.usuario_l1 = criar_usuario('33333333333', nome='Sem Permissão')
        self.usuario_cadastrador = conceder_capacidade_cadastrar(
            criar_usuario('44444444444', nome='Cadastrador Importação'),
        )
        self.token_l1 = obter_tokens(self.usuario_l1)
        self.token_cadastrador = obter_tokens(self.usuario_cadastrador)

    @patch('Infraestrutura.importacoes.business.ImportacaoLoteBusiness.pre_visualizar_importacao')
    def test_endpoint_preview_deve_retornar_200(self, mock_preview):
        mock_preview.return_value = ResultadoImportacaoDTO(
            sucesso=True,
            mensagem='Pré-visualização concluída.',
            resumo=ResumoImportacaoDTO(
                total_abas_processadas=1,
                total_linhas_processadas=1,
            ),
            erros=[],
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('infraestrutura:importacao-pre-visualizar'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('Infraestrutura.importacoes.business.ImportacaoLoteBusiness.iniciar_importacao')
    def test_endpoint_importacao_deve_retornar_202(self, mock_iniciar):
        mock_iniciar.return_value = 1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('infraestrutura:importacao'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['dados']['importacao_id'], 1)

    def test_endpoint_importacao_sem_permissao_retorna_403(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('infraestrutura:importacao'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('Infraestrutura.importacoes.importacao.s3_helper.upload_importacao_to_s3')
    def test_segunda_importacao_paralela_retorna_400(self, mock_upload):
        mock_upload.return_value = True
        ImportacaoLote.objects.create(
            status=StatusImportacao.EM_ANDAMENTO,
            arquivo='dummy.ods',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        arquivo = SimpleUploadedFile(
            'modelo-importacao-infraestrutura.ods',
            b'fake-content',
            content_type='application/vnd.oasis.opendocument.spreadsheet',
        )

        response = self.client.post(
            reverse('infraestrutura:importacao'),
            {'file': arquivo},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deve_cancelar_importacao_em_andamento(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')
        importacao = ImportacaoLote.objects.create(
            status=StatusImportacao.EM_ANDAMENTO,
            arquivo='dummy.ods',
        )

        response = self.client.post(reverse('infraestrutura:importacao-cancelar'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        importacao.refresh_from_db()
        self.assertEqual(importacao.status, StatusImportacao.ERRO)
        self.assertIn('erro_fatal', importacao.resultado_json)

    @patch('Infraestrutura.importacoes.business.ImportacaoLoteBusiness.importar_infraestrutura_em_lote')
    def test_task_nao_sobrescreve_status_erro_apos_cancelamento(self, mock_importar):
        from Infraestrutura.importacoes.tasks import processar_importacao_infraestrutura_task

        importacao = ImportacaoLote.objects.create(
            status=StatusImportacao.ERRO,
            arquivo='dummy.ods',
            resultado_json={
                'erro_fatal': 'Importação cancelada manualmente pelo administrador.',
            },
        )

        processar_importacao_infraestrutura_task(importacao.id)

        importacao.refresh_from_db()
        self.assertEqual(importacao.status, StatusImportacao.ERRO)
        mock_importar.assert_not_called()
