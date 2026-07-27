from io import BytesIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from Identidade.usuarios.importacao.importacao_dtos import (
    ArquivoImportacaoUsuariosDTO,
    LinhaSetorLotacaoImportacaoDTO,
    LinhaUsuarioImportacaoDTO,
    ReferenciasImportacaoDTO,
)
from Identidade.usuarios.importacao.importacao_parser import ImportacaoUsuariosParser
from Identidade.usuarios.importacao.importacao_resolucao import (
    ImportacaoReferenciasResolver,
    normalizar_id_referencia,
)
from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


class ImportacaoReferenciasParserTests(TestCase):
    @patch('Identidade.usuarios.importacao.importacao_parser.get_data')
    def test_deve_parsear_abas_de_referencia(self, mock_get_data):
        mock_get_data.return_value = {
            'Usuario': [
                ['usuario_id\n(int, PK)', 'cpf\n(String)', 'nome\n(String)', 'foto\n(String)',
                 'deficiencia\n(String)', 'ativo\n(boolean)', 'ultimo_login\n(Date)',
                 'colaborador_externo\n(Booleano)'],
                [1, '12345678901', 'Usuário Teste', '', '', 'true', '', 'false'],
            ],
            'Setor': [
                ['setor_id\n(int, PK)', 'nome\n(String)', 'sigla\n(String)', 'ativo\n(boolean)'],
                [99, 'Setor Teste', 'NAPNE/FLO', 'true'],
            ],
            'Funcao': [
                ['funcao_id\n(String, PK)', 'papel_funcao\n(String)', 'descricao\n(String)',
                 'ativo\n(boolean)', 'categoria\n(String)'],
                [1, 'Diretor Geral', 'Descrição', 'true', 'Diretor'],
            ],
            'Setor_Lotacao': [
                ['usuario_id\n(int, FK)', 'setor_id\n(int, FK)', 'funcao_id\n(String, FK)',
                 'responsavel\n(boolean)', 'monitor\n(boolean)'],
                [1, 99, 1, 'false', 'false'],
            ],
        }

        arquivo = BytesIO(b'test')
        arquivo.name = 'modelo-importacao-usuarios.ods'
        resultado = ImportacaoUsuariosParser().parse(arquivo)

        self.assertEqual(resultado.referencias.mapa_setor_id_para_sigla[99], 'NAPNE')
        self.assertEqual(resultado.referencias.mapa_funcao_id_para_papel['1'], 'Diretor Geral')
        self.assertEqual(len(resultado.setores_lotacao), 1)
        self.assertEqual(resultado.setores_lotacao[0].funcao_id_planilha, '1')


class ImportacaoReferenciasResolverTests(TestCase):
    def test_normalizar_id_referencia_converte_float_inteiro(self):
        self.assertEqual(normalizar_id_referencia(1.0), '1')
        self.assertEqual(normalizar_id_referencia(1), '1')

    def test_resolver_setor_usa_sigla_e_nao_pk(self):
        setor = Setor.objects.create(nome='Setor Resolver', sigla='SIGTEST', ativo=True)
        referencias = ReferenciasImportacaoDTO(mapa_setor_id_para_sigla={99: 'SIGTEST'})
        resolver = ImportacaoReferenciasResolver(referencias)

        self.assertEqual(resolver.resolver_setor(99), setor)
        self.assertIsNone(resolver.resolver_setor(100))
        self.assertNotEqual(setor.pk, 99)

    def test_resolver_funcao_usa_mapa_da_aba_referencia(self):
        funcao = Funcao.objects.create(
            papel_funcao='Função Resolver',
            descricao='Teste',
            ativo=True,
        )
        referencias = ReferenciasImportacaoDTO(mapa_funcao_id_para_papel={'1': 'Função Resolver'})
        resolver = ImportacaoReferenciasResolver(referencias)

        self.assertEqual(resolver.resolver_funcao('1'), funcao)
        self.assertIsNone(resolver.resolver_funcao('999'))


class ImportacaoSetorLotacaoBusinessTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def _criar_importacao_mock(self):
        importacao_mock = MagicMock()
        importacao_mock.id = 999
        importacao_mock.arquivo = BytesIO(b'test')
        importacao_mock.linhas_processadas = 0
        importacao_mock.total_linhas = 0
        return importacao_mock

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_importar_lotacao_com_ids_internos_diferentes_das_pks(self, mock_parse):
        setor = Setor.objects.create(nome='Diretoria Teste', sigla='DIRTEST', ativo=True)
        funcao = Funcao.objects.create(
            papel_funcao='Coordenador Teste',
            descricao='Teste',
            ativo=True,
        )

        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={42: 'DIRTEST'},
            mapa_funcao_id_para_papel={'7': 'Coordenador Teste'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='98765432100',
                    nome='Usuário Lotação',
                    ativo=True,
                )
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    setor_id_planilha=42,
                    funcao_id_planilha='7',
                    responsavel=True,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(importacao_lote=self._criar_importacao_mock())

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.lotacoes_criadas, 1)

        usuario = self.User.objects.get(cpf='98765432100')
        vinculo = SetorVinculo.objects.get(usuario=usuario)
        self.assertEqual(vinculo.setor_id, setor.id)
        self.assertEqual(vinculo.funcao_id, funcao.id)
        self.assertTrue(vinculo.responsavel)
        self.assertNotEqual(setor.pk, 42)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_reportar_erro_em_setor_id_inexistente(self, mock_parse):
        Funcao.objects.create(papel_funcao='Função Teste', descricao='Teste', ativo=True)

        referencias = ReferenciasImportacaoDTO(
            mapa_funcao_id_para_papel={'1': 'Função Teste'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='11122233344',
                    nome='Usuário Erro Setor',
                    ativo=True,
                )
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    setor_id_planilha=99,
                    funcao_id_planilha='1',
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(importacao_lote=self._criar_importacao_mock())

        self.assertFalse(resultado.sucesso)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].campo, 'setor_id')
        self.assertEqual(resultado.erros[0].aba, 'Setor_Lotacao')
        self.assertEqual(SetorVinculo.objects.count(), 0)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_reportar_erro_em_funcao_id_inexistente(self, mock_parse):
        Setor.objects.create(nome='Setor Erro', sigla='SERRO', ativo=True)

        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={1: 'SERRO'},
            mapa_funcao_id_para_papel={'1': 'Função Inexistente'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='55566677788',
                    nome='Usuário Erro Função',
                    ativo=True,
                )
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    setor_id_planilha=1,
                    funcao_id_planilha='1',
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(importacao_lote=self._criar_importacao_mock())

        self.assertFalse(resultado.sucesso)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].campo, 'funcao_id')
        self.assertEqual(SetorVinculo.objects.count(), 0)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_reimportacao_de_lotacao_eh_idempotente(self, mock_parse):
        setor = Setor.objects.create(nome='Setor Idempotente', sigla='SIDEM', ativo=True)
        funcao = Funcao.objects.create(
            papel_funcao='Função Idempotente',
            descricao='Teste',
            ativo=True,
        )
        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={5: 'SIDEM'},
            mapa_funcao_id_para_papel={'3': 'Função Idempotente'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='44455566677',
                    nome='Usuário Idempotente',
                    ativo=True,
                )
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    setor_id_planilha=5,
                    funcao_id_planilha='3',
                    responsavel=False,
                )
            ],
        )
        mock_parse.return_value = estrutura
        importacao_mock = self._criar_importacao_mock()

        primeiro = Usuario().business.importar_usuarios_em_lote(importacao_lote=importacao_mock)
        segundo = Usuario().business.importar_usuarios_em_lote(importacao_lote=importacao_mock)

        self.assertEqual(primeiro.resumo.lotacoes_criadas, 1)
        self.assertEqual(segundo.resumo.lotacoes_criadas, 0)
        self.assertEqual(SetorVinculo.objects.count(), 1)

        vinculo = SetorVinculo.objects.get()
        self.assertEqual(vinculo.setor_id, setor.id)
        self.assertEqual(vinculo.funcao_id, funcao.id)
