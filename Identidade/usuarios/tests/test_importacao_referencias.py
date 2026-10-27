from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from Academico.cursos.models import Curso
from AppCore.common.util.util import normalizar_chave_texto, normalizar_cnpj
from Identidade.usuarios.importacao.importacao_dtos import (
    ArquivoImportacaoUsuariosDTO,
    LinhaCargoReferenciaImportacaoDTO,
    LinhaCursoImportacaoDTO,
    LinhaEmpresaReferenciaImportacaoDTO,
    LinhaFuncaoReferenciaImportacaoDTO,
    LinhaSetorLotacaoImportacaoDTO,
    LinhaSetorReferenciaImportacaoDTO,
    LinhaUsuarioImportacaoDTO,
    ReferenciasImportacaoDTO,
)
from Identidade.usuarios.models import ImportacaoLote, StatusImportacao, Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao


class ImportacaoReferenciasUtilTests(APITestCase):
    def test_normalizar_chave_texto_remove_acento_caixa_e_espacos(self):
        self.assertEqual(
            normalizar_chave_texto('  Professor do Ensino  Básico '),
            normalizar_chave_texto('PROFESSOR DO ENSINO BASICO'),
        )
        self.assertEqual(normalizar_chave_texto(''), '')
        self.assertEqual(normalizar_chave_texto(None), '')

    def test_normalizar_cnpj_digitos_zfill_e_ponto_zero(self):
        self.assertEqual(normalizar_cnpj('12.345.678/0001-99'), '12345678000199')
        self.assertEqual(normalizar_cnpj('12345678000199.0'), '12345678000199')
        self.assertIsNone(normalizar_cnpj(None))
        self.assertIsNone(normalizar_cnpj(''))
        self.assertIsNone(normalizar_cnpj('NULL'))
        longo = normalizar_cnpj('123456780001991')
        self.assertEqual(longo, '123456780001991')
        self.assertEqual(len(longo), 15)


class ImportacaoReferenciasBusinessTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()

    def _criar_importacao_lote(self):
        ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO).update(
            status=StatusImportacao.CONCLUIDA,
        )
        return ImportacaoLote.objects.create(
            arquivo=SimpleUploadedFile('test.ods', b'test'),
            status=StatusImportacao.EM_ANDAMENTO,
            total_linhas=0,
            linhas_processadas=0,
        )

    def _contar_cargos_por_chave(self, nome):
        chave = normalizar_chave_texto(nome)
        return sum(
            1 for cargo in Cargo.objects.all()
            if normalizar_chave_texto(cargo.nome) == chave
        )

    def _usuario_minimo(self, cpf, usuario_id=1, numero_linha=10):
        return LinhaUsuarioImportacaoDTO(
            numero_linha=numero_linha,
            usuario_id_planilha=usuario_id,
            cpf=cpf,
            nome='Usuário Referência Teste',
            ativo=True,
        )

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_deve_criar_setor_funcao_cargo_e_empresa_ausentes(self, mock_parse):
        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={1: 'SETIMP01'},
            mapa_funcao_id_para_papel={'1': 'Função Importação XYZ'},
            mapa_cargo_id_para_nome={1: 'Cargo Importação XYZ'},
            mapa_empresa_id_para_nome={1: 'Empresa Importação XYZ'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=1,
                    nome='  Setor   Importação  ',
                    sigla='SETIMP01',
                    ativo=True,
                )
            ],
            funcoes=[
                LinhaFuncaoReferenciaImportacaoDTO(
                    numero_linha=2,
                    funcao_id_planilha='1',
                    papel_funcao='Função Importação XYZ',
                    descricao='Descrição teste',
                    categoria='Diretor',
                    ativo=True,
                )
            ],
            cargos=[
                LinhaCargoReferenciaImportacaoDTO(
                    numero_linha=2,
                    cargo_id_planilha=1,
                    nome='Cargo Importação XYZ',
                    ativo=True,
                )
            ],
            empresas=[
                LinhaEmpresaReferenciaImportacaoDTO(
                    numero_linha=2,
                    empresa_instituicao_id_planilha=1,
                    nome='  Empresa   Importação  XYZ  ',
                    cnpj='11222333000181',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11001001001', numero_linha=11),
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.setores_criados, 1)
        self.assertEqual(resultado.resumo.funcoes_criadas, 1)
        self.assertEqual(resultado.resumo.cargos_criados, 1)
        self.assertEqual(resultado.resumo.empresas_criadas, 1)
        self.assertEqual(resultado.resumo.usuarios_criados, 1)

        setor = Setor.objects.get(sigla='SETIMP01')
        self.assertEqual(setor.nome, 'Setor Importação')
        funcao = Funcao.objects.get(papel_funcao='Função Importação XYZ')
        self.assertEqual(funcao.categoria, 'diretor')
        cargo = Cargo.objects.get(nome='Cargo Importação XYZ')
        self.assertTrue(cargo.ativo)
        empresa = EmpresaInstituicao.objects.get(cnpj='11222333000181')
        self.assertEqual(empresa.nome, 'Empresa Importação XYZ')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_nao_duplica_quando_caixa_e_acento_diferem(self, mock_parse):
        Cargo.objects.create(nome='PROFESSOR DO ENSINO BASICO TESTE', ativo=True)
        EmpresaInstituicao.objects.create(nome='Empresa Banco Única LTDA', ativo=True)

        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={10: 'napne'},
            mapa_funcao_id_para_papel={'2': 'diretor(a) geral'},
            mapa_cargo_id_para_nome={1: 'Administrador', 2: 'Professor do Ensino Básico Teste'},
            mapa_empresa_id_para_nome={1: 'empresa banco unica ltda'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=10,
                    nome='Qualquer Nome Setor',
                    sigla='napne',
                    ativo=True,
                )
            ],
            funcoes=[
                LinhaFuncaoReferenciaImportacaoDTO(
                    numero_linha=2,
                    funcao_id_planilha='2',
                    papel_funcao='diretor(a) geral',
                    categoria='Diretor',
                    ativo=True,
                )
            ],
            cargos=[
                LinhaCargoReferenciaImportacaoDTO(
                    numero_linha=3,
                    cargo_id_planilha=1,
                    nome='Administrador',
                    ativo=True,
                ),
                LinhaCargoReferenciaImportacaoDTO(
                    numero_linha=4,
                    cargo_id_planilha=2,
                    nome='Professor do Ensino Básico Teste',
                    ativo=True,
                ),
            ],
            empresas=[
                LinhaEmpresaReferenciaImportacaoDTO(
                    numero_linha=2,
                    empresa_instituicao_id_planilha=1,
                    nome='empresa banco unica ltda',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11002002002', numero_linha=20),
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.cargos_criados, 0)
        self.assertEqual(self._contar_cargos_por_chave('ADMINISTRADOR'), 1)
        self.assertEqual(self._contar_cargos_por_chave('Professor do Ensino Básico Teste'), 1)
        self.assertEqual(resultado.resumo.setores_criados, 0)
        self.assertEqual(Setor.objects.filter(sigla='NAPNE').count(), 1)
        self.assertFalse(Setor.objects.filter(sigla='napne').exists())
        self.assertEqual(resultado.resumo.funcoes_criadas, 0)
        self.assertEqual(resultado.resumo.empresas_criadas, 0)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_empresa_casa_por_cnpj_mesmo_com_nome_diferente(self, mock_parse):
        EmpresaInstituicao.objects.create(
            nome='Empresa CNPJ Banco',
            cnpj='99888777000166',
            ativo=True,
        )
        referencias = ReferenciasImportacaoDTO(
            mapa_empresa_id_para_nome={5: 'Outro Nome Fantasia'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            empresas=[
                LinhaEmpresaReferenciaImportacaoDTO(
                    numero_linha=2,
                    empresa_instituicao_id_planilha=5,
                    nome='Outro Nome Fantasia',
                    cnpj='99.888.777/0001-66',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11003003003', numero_linha=12),
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.empresas_criadas, 0)
        self.assertEqual(EmpresaInstituicao.objects.filter(cnpj='99888777000166').count(), 1)
        empresa = EmpresaInstituicao.objects.get(cnpj='99888777000166')
        self.assertEqual(empresa.nome, 'Empresa CNPJ Banco')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_reimportacao_de_referencias_eh_idempotente(self, mock_parse):
        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={7: 'SETIDEM01'},
            mapa_cargo_id_para_nome={3: 'Cargo Idempotente XYZ'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=7,
                    nome='Setor Idempotente',
                    sigla='SETIDEM01',
                    ativo=True,
                )
            ],
            cargos=[
                LinhaCargoReferenciaImportacaoDTO(
                    numero_linha=2,
                    cargo_id_planilha=3,
                    nome='Cargo Idempotente XYZ',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11004004004', numero_linha=13),
            ],
        )
        mock_parse.return_value = estrutura

        primeiro = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )
        setores_apos_primeiro = Setor.objects.count()
        cargos_apos_primeiro = Cargo.objects.count()

        segundo = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(primeiro.resumo.setores_criados, 1)
        self.assertEqual(primeiro.resumo.cargos_criados, 1)
        self.assertEqual(segundo.resumo.setores_criados, 0)
        self.assertEqual(segundo.resumo.cargos_criados, 0)
        self.assertEqual(Setor.objects.count(), setores_apos_primeiro)
        self.assertEqual(Cargo.objects.count(), cargos_apos_primeiro)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_curso_e_lotacao_usam_setor_criado_na_mesma_importacao(self, mock_parse):
        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={88: 'SETLOT99'},
            mapa_curso_id_para_codigo={1: 'CUR-LOT99'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=88,
                    nome='Setor Lotação Curso',
                    sigla='SETLOT99',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11005005005', numero_linha=14),
            ],
            cursos=[
                LinhaCursoImportacaoDTO(
                    numero_linha=3,
                    curso_id_planilha=1,
                    setor_id_planilha=88,
                    nome='Curso Lotação Teste',
                    codigo_curso='CUR-LOT99',
                    ativo=True,
                )
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=4,
                    usuario_id_planilha=1,
                    setor_id_planilha=88,
                    funcao_id_planilha='',
                    responsavel=False,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.setores_criados, 1)
        self.assertEqual(resultado.resumo.cursos_criados, 1)
        self.assertEqual(resultado.resumo.lotacoes_criadas, 1)

        setor = Setor.objects.get(sigla='SETLOT99')
        curso = Curso.objects.get(codigo_curso='CUR-LOT99')
        self.assertEqual(curso.setor_id, setor.pk)
        usuario = self.User.objects.get(cpf='11005005005')
        vinculo = SetorVinculo.objects.get(usuario=usuario)
        self.assertEqual(vinculo.setor_id, setor.pk)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_erro_linha_setor_sem_nome_e_funcao_categoria_invalida(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=ReferenciasImportacaoDTO(),
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=1,
                    nome='',
                    sigla='SETSNNOM',
                    ativo=True,
                )
            ],
            funcoes=[
                LinhaFuncaoReferenciaImportacaoDTO(
                    numero_linha=3,
                    funcao_id_planilha='9',
                    papel_funcao='Função Categoria Inválida',
                    categoria='gerente',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11006006006', numero_linha=15),
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertFalse(resultado.sucesso)
        self.assertEqual(resultado.resumo.setores_criados, 0)
        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        self.assertTrue(self.User.objects.filter(cpf='11006006006').exists())

        erros_setor = [e for e in resultado.erros if e.aba == 'Setor' and e.campo == 'nome']
        self.assertEqual(len(erros_setor), 1)
        erros_funcao = [e for e in resultado.erros if e.aba == 'Funcao' and e.campo == 'categoria']
        self.assertEqual(len(erros_funcao), 1)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_id_operacional_sem_referencia_continua_erro(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=ReferenciasImportacaoDTO(),
            usuarios=[
                self._usuario_minimo('11007007007', numero_linha=16),
            ],
            setores_lotacao=[
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=17,
                    usuario_id_planilha=1,
                    setor_id_planilha=99,
                    funcao_id_planilha='',
                )
            ],
        )
        mock_parse.return_value = estrutura

        vinculos_antes = SetorVinculo.objects.filter(
            usuario__cpf='11007007007',
        ).count()

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertFalse(resultado.sucesso)
        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(resultado.erros[0].aba, 'Setor_Lotacao')
        self.assertEqual(resultado.erros[0].campo, 'setor_id')
        vinculos_depois = SetorVinculo.objects.filter(
            usuario__cpf='11007007007',
        ).count()
        self.assertEqual(vinculos_depois, vinculos_antes)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_progresso_do_lote_fecha_em_total_linhas(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=ReferenciasImportacaoDTO(
                mapa_setor_id_para_sigla={3: 'SETPROG01'},
            ),
            setores=[
                LinhaSetorReferenciaImportacaoDTO(
                    numero_linha=2,
                    setor_id_planilha=3,
                    nome='Setor Progresso',
                    sigla='SETPROG01',
                    ativo=True,
                )
            ],
            usuarios=[
                self._usuario_minimo('11008008008', numero_linha=18),
            ],
        )
        mock_parse.return_value = estrutura
        lote = self._criar_importacao_lote()

        resultado = Usuario().business.importar_usuarios_em_lote(importacao_lote=lote)

        lote.refresh_from_db()
        self.assertEqual(resultado.resumo.total_linhas_processadas, 2)
        self.assertEqual(lote.total_linhas, 2)
        self.assertEqual(lote.linhas_processadas, 2)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_curso_casa_codigo_com_caixa_diferente(self, mock_parse):
        setor_napne = Setor.objects.get(sigla='NAPNE')
        Curso.objects.create(
            codigo_curso='IMP-CASE',
            nome='Antigo',
            setor=setor_napne,
            ativo=True,
        )
        referencias = ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={setor_napne.pk: 'NAPNE'},
            mapa_curso_id_para_codigo={2: 'imp-case'},
        )
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=referencias,
            usuarios=[
                self._usuario_minimo('11009009009', numero_linha=19),
            ],
            cursos=[
                LinhaCursoImportacaoDTO(
                    numero_linha=3,
                    curso_id_planilha=2,
                    setor_id_planilha=setor_napne.pk,
                    nome='Novo Nome',
                    codigo_curso='imp-case',
                    ativo=True,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.resumo.cursos_criados, 0)
        self.assertEqual(resultado.resumo.cursos_atualizados, 1)
        curso = Curso.objects.get(codigo_curso='IMP-CASE')
        self.assertEqual(curso.nome, 'Novo Nome')
