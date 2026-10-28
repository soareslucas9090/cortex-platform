from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from Identidade.usuarios.importacao.importacao_constants import (
    ABA_ALUNO,
    ABA_ALUNO_CURSO,
    ABA_CARGO,
    ABA_CONTATO,
    ABA_CURSO,
    ABA_SERVIDOR,
    ABA_SETOR_LOTACAO,
    ABA_USUARIO,
    MAX_ERROS_PLANOS_API,
    MAX_GRUPOS_ERRO_API,
    MAX_IMPACTOS_POR_GRUPO_API,
    PAPEL_ERRO_CAUSA,
    PAPEL_ERRO_IMPACTO,
    TIPO_GRUPO_FALHA_ENTIDADE,
    TIPO_GRUPO_LINHA,
    TIPO_GRUPO_REFERENCIA_INEXISTENTE,
)
from Identidade.usuarios.importacao.importacao_dtos import (
    ArquivoImportacaoUsuariosDTO,
    LinhaAlunoCursoImportacaoDTO,
    LinhaAlunoImportacaoDTO,
    LinhaCargoReferenciaImportacaoDTO,
    LinhaContatoImportacaoDTO,
    LinhaCursoImportacaoDTO,
    LinhaEnderecoImportacaoDTO,
    LinhaServidorImportacaoDTO,
    LinhaSetorLotacaoImportacaoDTO,
    LinhaUsuarioImportacaoDTO,
    ReferenciasImportacaoDTO,
)
from Identidade.usuarios.importacao.importacao_erros import (
    ColetorErrosImportacao,
    truncar_resultado_json,
)
from Identidade.usuarios.models import ImportacaoLote, StatusImportacao, Usuario
from Identidade.usuarios.serializers import StatusImportacaoLoteSerializer
from Organizacional.setores.models import Setor
from PessoasInstitucionais.cargos.models import Cargo


class ColetorErrosImportacaoTests(SimpleTestCase):
    def test_agrupa_impactos_na_raiz_de_forma_transitiva(self):
        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=7,
                    usuario_id_planilha=12,
                    cpf='12',
                    nome='Maria Silva',
                )
            ],
            alunos=[
                LinhaAlunoImportacaoDTO(
                    numero_linha=4,
                    aluno_id_planilha=5,
                    usuario_id_planilha=12,
                )
            ],
        )
        coletor = ColetorErrosImportacao(estrutura)
        coletor.registrar_falha_linha(
            aba=ABA_USUARIO,
            numero_linha=7,
            campo='cpf',
            valor='12',
            codigo='erro_usuario',
            mensagem='CPF inválido.',
            id_planilha=12,
        )
        self.assertTrue(coletor.registrar_se_pais_falharam(ABA_ALUNO, estrutura.alunos[0], 'erro_aluno'))
        aluno_curso = LinhaAlunoCursoImportacaoDTO(
            numero_linha=9,
            aluno_id_planilha=5,
            curso_id_planilha=10,
        )
        self.assertTrue(coletor.registrar_se_pais_falharam(ABA_ALUNO_CURSO, aluno_curso, 'erro_aluno_curso'))

        erros = coletor.erros
        self.assertEqual(erros[0].papel, PAPEL_ERRO_CAUSA)
        self.assertEqual(erros[0].grupo_id, 'Usuario:12')
        self.assertTrue(all(erro.papel == PAPEL_ERRO_IMPACTO for erro in erros[1:]))
        self.assertEqual(len(erros), 3)

        grupos = coletor.construir_grupos(estrutura)
        self.assertEqual(len(grupos), 1)
        grupo = grupos[0]
        self.assertEqual(grupo.id, 'Usuario:12')
        self.assertEqual(grupo.tipo, TIPO_GRUPO_FALHA_ENTIDADE)
        self.assertEqual(grupo.titulo, 'CPF inválido.')
        self.assertEqual(grupo.causa.rotulo, 'Maria Silva (CPF 12)')
        self.assertEqual(grupo.total_impactos, 2)
        self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO], 1)
        self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO_CURSO], 1)
        self.assertIn('depende de Usuario 12 (linha 7)', grupo.impactos[0].mensagem)
        self.assertIn('depende de Usuario 12 (linha 7)', grupo.impactos[1].mensagem)

    def test_referencia_inexistente_reune_linhas_no_mesmo_grupo(self):
        coletor = ColetorErrosImportacao()
        coletor.registrar_referencia_inexistente(
            aba=ABA_SERVIDOR,
            numero_linha=3,
            campo='cargo_id',
            valor=5,
            codigo='erro_servidor',
            aba_referencia=ABA_CARGO,
            id_referencia=5,
            id_planilha=1,
        )
        coletor.registrar_referencia_inexistente(
            aba=ABA_SERVIDOR,
            numero_linha=4,
            campo='cargo_id',
            valor=5,
            codigo='erro_servidor',
            aba_referencia=ABA_CARGO,
            id_referencia=5,
            id_planilha=2,
        )

        grupos = coletor.construir_grupos()
        self.assertEqual(len(grupos), 1)
        self.assertEqual(grupos[0].id, 'ref:Cargo:5')
        self.assertEqual(grupos[0].tipo, TIPO_GRUPO_REFERENCIA_INEXISTENTE)
        self.assertEqual(grupos[0].total_impactos, 2)
        self.assertEqual(len(coletor.erros), 2)
        self.assertTrue(all(erro.papel == PAPEL_ERRO_IMPACTO for erro in coletor.erros))

    def test_erro_isolado_vira_grupo_de_linha(self):
        coletor = ColetorErrosImportacao()
        coletor.registrar_falha_linha(
            aba=ABA_CONTATO,
            numero_linha=7,
            campo='email_academico',
            valor='invalido',
            codigo='erro_contato',
            mensagem='E-mail inválido.',
        )
        grupos = coletor.construir_grupos()
        self.assertEqual(len(grupos), 1)
        self.assertEqual(grupos[0].id, 'linha:Contato:7')
        self.assertEqual(grupos[0].tipo, TIPO_GRUPO_LINHA)
        self.assertEqual(grupos[0].total_impactos, 0)

    def test_funcao_opcional_vazia_nao_e_dependencia(self):
        coletor = ColetorErrosImportacao()
        linha = LinhaSetorLotacaoImportacaoDTO(
            numero_linha=2,
            usuario_id_planilha=1,
            setor_id_planilha=1,
            funcao_id_planilha='',
        )
        self.assertIsNone(coletor.primeira_dependencia_falha(ABA_SETOR_LOTACAO, linha))


class TruncarResultadoJsonTests(SimpleTestCase):
    def test_trunca_grupos_e_mantem_total_impactos(self):
        grupos = []
        for indice in range(MAX_GRUPOS_ERRO_API + 3):
            impactos = [{'aba': ABA_CONTATO, 'numero_linha': i, 'campo': 'usuario_id', 'mensagem': 'x'} for i in range(MAX_IMPACTOS_POR_GRUPO_API + 5)]
            grupos.append({
                'id': f'Usuario:{indice}',
                'tipo': TIPO_GRUPO_FALHA_ENTIDADE,
                'titulo': 'CPF inválido.',
                'total_impactos': len(impactos),
                'impactos': impactos,
            })
        erros = [{'aba': ABA_USUARIO, 'numero_linha': i} for i in range(MAX_ERROS_PLANOS_API + 10)]
        resultado = truncar_resultado_json({'erros': erros, 'grupos_erro': grupos})

        self.assertEqual(len(resultado['grupos_erro']), MAX_GRUPOS_ERRO_API)
        self.assertEqual(len(resultado['erros']), MAX_ERROS_PLANOS_API)
        self.assertEqual(resultado['grupos_erro'][0]['total_impactos'], MAX_IMPACTOS_POR_GRUPO_API + 5)
        self.assertEqual(len(resultado['grupos_erro'][0]['impactos']), MAX_IMPACTOS_POR_GRUPO_API)
        self.assertIn('grupos de erro', resultado['mensagem_aviso'])
        self.assertIn('erros devido ao tamanho', resultado['mensagem_aviso'])


class ImportacaoErrosAgrupadosBusinessTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.setor = Setor.objects.create(sigla='SETGRP', nome='Setor Agrupamento')
        self.cargo = Cargo.objects.create(nome='Cargo Agrupamento', ativo=True)

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

    def _referencias(self):
        return ReferenciasImportacaoDTO(
            mapa_setor_id_para_sigla={1: 'SETGRP'},
            mapa_cargo_id_para_nome={1: 'Cargo Agrupamento'},
            mapa_curso_id_para_codigo={10: 'CUR-GRP'},
        )

    def _curso(self):
        return LinhaCursoImportacaoDTO(
            numero_linha=2,
            curso_id_planilha=10,
            setor_id_planilha=1,
            nome='Curso Agrupamento',
            codigo_curso='CUR-GRP',
            ativo=True,
        )

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_quatro_cpfs_invalidos_viram_quatro_grupos(self, mock_parse):
        usuarios = []
        contatos = []
        enderecos = []
        alunos = []
        servidores = []
        lotacoes = []
        alunos_cursos = []
        for indice in range(1, 5):
            usuarios.append(
                LinhaUsuarioImportacaoDTO(
                    numero_linha=indice + 1,
                    usuario_id_planilha=indice,
                    cpf=str(indice),
                    nome=f'Usuário Inválido {indice}',
                    ativo=True,
                )
            )
            contatos.append(
                LinhaContatoImportacaoDTO(
                    numero_linha=indice + 1,
                    usuario_id_planilha=indice,
                    email_academico=f'user{indice}@if.edu.br',
                )
            )
            enderecos.append(
                LinhaEnderecoImportacaoDTO(
                    numero_linha=indice + 1,
                    usuario_id_planilha=indice,
                    cidade='Floriano',
                    estado='PI',
                )
            )
            alunos.append(
                LinhaAlunoImportacaoDTO(
                    numero_linha=indice + 1,
                    aluno_id_planilha=indice,
                    usuario_id_planilha=indice,
                )
            )
            servidores.append(
                LinhaServidorImportacaoDTO(
                    numero_linha=indice + 1,
                    servidor_id_planilha=indice,
                    usuario_id_planilha=indice,
                    cargo_id_planilha=1,
                )
            )
            lotacoes.append(
                LinhaSetorLotacaoImportacaoDTO(
                    numero_linha=indice + 1,
                    usuario_id_planilha=indice,
                    setor_id_planilha=1,
                    funcao_id_planilha='',
                )
            )
            alunos_cursos.append(
                LinhaAlunoCursoImportacaoDTO(
                    numero_linha=indice + 1,
                    aluno_id_planilha=indice,
                    curso_id_planilha=10,
                    matricula=f'MAT-INV-{indice}',
                )
            )

        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=self._referencias(),
            usuarios=usuarios,
            contatos=contatos,
            enderecos=enderecos,
            alunos=alunos,
            cursos=[self._curso()],
            alunos_cursos=alunos_cursos,
            servidores=servidores,
            setores_lotacao=lotacoes,
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertFalse(resultado.sucesso)
        self.assertEqual(resultado.resumo.total_grupos_erro, 4)
        self.assertEqual(len(resultado.grupos_erro), 4)
        self.assertEqual(len(resultado.erros), 28)
        self.assertEqual(resultado.resumo.total_linhas_com_erro, 28)
        self.assertEqual(resultado.resumo.cursos_criados, 1)

        ids_grupos = {grupo.id for grupo in resultado.grupos_erro}
        self.assertEqual(ids_grupos, {'Usuario:1', 'Usuario:2', 'Usuario:3', 'Usuario:4'})
        for grupo in resultado.grupos_erro:
            self.assertEqual(grupo.tipo, TIPO_GRUPO_FALHA_ENTIDADE)
            self.assertEqual(grupo.causa.campo, 'cpf')
            self.assertEqual(grupo.total_impactos, 6)
            self.assertEqual(grupo.impactos_por_aba[ABA_CONTATO], 1)
            self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO], 1)
            self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO_CURSO], 1)
            self.assertEqual(grupo.impactos_por_aba[ABA_SERVIDOR], 1)
            self.assertEqual(grupo.impactos_por_aba[ABA_SETOR_LOTACAO], 1)
            self.assertIn('CPF inválido', grupo.titulo)

        causas = [erro for erro in resultado.erros if erro.papel == PAPEL_ERRO_CAUSA]
        impactos = [erro for erro in resultado.erros if erro.papel == PAPEL_ERRO_IMPACTO]
        self.assertEqual(len(causas), 4)
        self.assertEqual(len(impactos), 24)
        self.assertTrue(all(erro.aba == ABA_USUARIO for erro in causas))

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_cadeia_usuario_aluno_aluno_curso_aponta_para_usuario(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=self._referencias(),
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=12,
                    cpf='12',
                    nome='Maria Silva',
                    ativo=True,
                )
            ],
            alunos=[
                LinhaAlunoImportacaoDTO(
                    numero_linha=3,
                    aluno_id_planilha=5,
                    usuario_id_planilha=12,
                )
            ],
            cursos=[self._curso()],
            alunos_cursos=[
                LinhaAlunoCursoImportacaoDTO(
                    numero_linha=9,
                    aluno_id_planilha=5,
                    curso_id_planilha=10,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(len(resultado.grupos_erro), 1)
        grupo = resultado.grupos_erro[0]
        self.assertEqual(grupo.id, 'Usuario:12')
        self.assertEqual(grupo.causa.rotulo, 'Maria Silva (CPF 12)')
        self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO], 1)
        self.assertEqual(grupo.impactos_por_aba[ABA_ALUNO_CURSO], 1)
        mensagem_aluno_curso = next(
            impacto.mensagem for impacto in grupo.impactos if impacto.aba == ABA_ALUNO_CURSO
        )
        self.assertIn('Usuario 12', mensagem_aluno_curso)
        self.assertIn('CPF inválido', mensagem_aluno_curso)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_cargo_do_catalogo_que_falha_agrupa_servidores(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=ReferenciasImportacaoDTO(
                mapa_cargo_id_para_nome={8: ''},
            ),
            cargos=[
                LinhaCargoReferenciaImportacaoDTO(
                    numero_linha=2,
                    cargo_id_planilha=8,
                    nome='',
                    ativo=True,
                )
            ],
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=3,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Servidor Cargo Falho',
                    ativo=True,
                )
            ],
            servidores=[
                LinhaServidorImportacaoDTO(
                    numero_linha=4,
                    servidor_id_planilha=1,
                    usuario_id_planilha=1,
                    cargo_id_planilha=8,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        self.assertEqual(len(resultado.grupos_erro), 1)
        grupo = resultado.grupos_erro[0]
        self.assertEqual(grupo.id, 'Cargo:8')
        self.assertEqual(grupo.causa.aba, ABA_CARGO)
        self.assertEqual(grupo.total_impactos, 1)
        self.assertEqual(grupo.impactos[0].aba, ABA_SERVIDOR)
        self.assertIn('depende de Cargo 8', grupo.impactos[0].mensagem)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_cargo_ausente_gera_grupo_de_referencia(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=ReferenciasImportacaoDTO(),
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Servidor Sem Cargo',
                    ativo=True,
                )
            ],
            servidores=[
                LinhaServidorImportacaoDTO(
                    numero_linha=3,
                    servidor_id_planilha=1,
                    usuario_id_planilha=1,
                    cargo_id_planilha=99,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(len(resultado.grupos_erro), 1)
        grupo = resultado.grupos_erro[0]
        self.assertEqual(grupo.id, 'ref:Cargo:99')
        self.assertEqual(grupo.tipo, TIPO_GRUPO_REFERENCIA_INEXISTENTE)
        self.assertEqual(resultado.erros[0].aba, ABA_SERVIDOR)
        self.assertEqual(resultado.erros[0].campo, 'cargo_id')
        self.assertEqual(resultado.erros[0].papel, PAPEL_ERRO_IMPACTO)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_usuario_orfao_em_contato_gera_grupo_de_referencia(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Usuário Válido',
                    ativo=True,
                )
            ],
            contatos=[
                LinhaContatoImportacaoDTO(
                    numero_linha=3,
                    usuario_id_planilha=99,
                    email_academico='orfao@if.edu.br',
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(resultado.resumo.usuarios_criados, 1)
        self.assertEqual(len(resultado.grupos_erro), 1)
        self.assertEqual(resultado.grupos_erro[0].id, 'ref:Usuario:99')
        self.assertEqual(resultado.erros[0].aba, ABA_CONTATO)
        self.assertEqual(resultado.erros[0].campo, 'usuario_id')

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_curso_que_falha_agrupa_aluno_curso(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            referencias=self._referencias(),
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12345678901',
                    nome='Aluno Curso Falho',
                    ativo=True,
                )
            ],
            alunos=[
                LinhaAlunoImportacaoDTO(
                    numero_linha=3,
                    aluno_id_planilha=1,
                    usuario_id_planilha=1,
                )
            ],
            cursos=[
                LinhaCursoImportacaoDTO(
                    numero_linha=4,
                    curso_id_planilha=10,
                    setor_id_planilha=1,
                    nome='Curso Sem Código',
                    codigo_curso='',
                    ativo=True,
                )
            ],
            alunos_cursos=[
                LinhaAlunoCursoImportacaoDTO(
                    numero_linha=5,
                    aluno_id_planilha=1,
                    curso_id_planilha=10,
                )
            ],
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(resultado.resumo.alunos_criados, 1)
        self.assertEqual(len(resultado.grupos_erro), 1)
        grupo = resultado.grupos_erro[0]
        self.assertEqual(grupo.id, 'Curso:10')
        self.assertEqual(grupo.causa.campo, 'codigo_curso')
        self.assertEqual(grupo.total_impactos, 1)
        self.assertEqual(grupo.impactos[0].aba, ABA_ALUNO_CURSO)

    @patch('Identidade.usuarios.business.ImportacaoUsuariosParser.parse')
    def test_erro_isolado_gera_um_grupo_sem_impactos(self, mock_parse):
        estrutura = ArquivoImportacaoUsuariosDTO(
            usuarios=[
                LinhaUsuarioImportacaoDTO(
                    numero_linha=2,
                    usuario_id_planilha=1,
                    cpf='12',
                    nome='Só CPF',
                    ativo=True,
                )
            ]
        )
        mock_parse.return_value = estrutura

        resultado = Usuario().business.importar_usuarios_em_lote(
            importacao_lote=self._criar_importacao_lote(),
        )

        self.assertEqual(len(resultado.erros), 1)
        self.assertEqual(len(resultado.grupos_erro), 1)
        self.assertEqual(resultado.resumo.total_grupos_erro, 1)
        self.assertEqual(resultado.grupos_erro[0].id, 'Usuario:1')
        self.assertEqual(resultado.grupos_erro[0].total_impactos, 0)
        self.assertEqual(resultado.erros[0].aba, ABA_USUARIO)

    def test_serializer_trunca_por_grupos(self):
        grupos = [
            {
                'id': f'Usuario:{indice}',
                'tipo': TIPO_GRUPO_FALHA_ENTIDADE,
                'titulo': 'CPF inválido.',
                'total_impactos': 3,
                'impactos': [
                    {'aba': ABA_CONTATO, 'numero_linha': 1, 'campo': 'usuario_id', 'mensagem': 'x'},
                    {'aba': ABA_ALUNO, 'numero_linha': 2, 'campo': 'usuario_id', 'mensagem': 'x'},
                    {'aba': ABA_ALUNO_CURSO, 'numero_linha': 3, 'campo': 'aluno_id', 'mensagem': 'x'},
                ],
            }
            for indice in range(MAX_GRUPOS_ERRO_API + 2)
        ]
        lote = ImportacaoLote.objects.create(
            arquivo=SimpleUploadedFile('test.ods', b'test'),
            status=StatusImportacao.CONCLUIDA,
            resultado_json={
                'erros': [{'aba': ABA_USUARIO, 'numero_linha': i} for i in range(MAX_ERROS_PLANOS_API + 4)],
                'grupos_erro': grupos,
            },
        )
        dados = StatusImportacaoLoteSerializer(lote).data
        resultado = dados['resultado_json']
        self.assertEqual(len(resultado['grupos_erro']), MAX_GRUPOS_ERRO_API)
        self.assertEqual(resultado['grupos_erro'][0]['total_impactos'], 3)
        self.assertEqual(len(resultado['erros']), MAX_ERROS_PLANOS_API)
        self.assertIn('mensagem_aviso', resultado)
