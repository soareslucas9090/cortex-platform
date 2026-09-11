from django.test import TestCase

from Academico.alunos.models import Aluno
from Academico.aluno_cursos.models import AlunoCurso
from Academico.cursos.models import Curso
from AppCore.common.util.util import normalizar_matricula
from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.servidores.choices import CategoriaServidor
from PessoasInstitucionais.servidores.models import Servidor
from PessoasInstitucionais.terceirizados.models import Terceirizado


class MatriculaHelperTestCase(TestCase):

    def setUp(self):
        self.usuario_aluno = Usuario.objects.create_user(
            cpf='11111111111',
            password='Senha@123',
            nome='Aluno Teste',
        )
        self.aluno = Aluno.objects.create(usuario=self.usuario_aluno)
        self.curso = Curso.objects.create(nome='Curso A', codigo_curso='CA01')

        self.usuario_servidor = Usuario.objects.create_user(
            cpf='22222222222',
            password='Senha@123',
            nome='Servidor Teste',
        )
        self.cargo = Cargo.objects.create(nome='Cargo Teste')

        self.usuario_terceirizado = Usuario.objects.create_user(
            cpf='33333333333',
            password='Senha@123',
            nome='Terceirizado Teste',
        )
        self.empresa = EmpresaInstituicao.objects.create(nome='Empresa Teste')

    def test_normalizar_matricula_trata_null_e_vazio(self):
        self.assertIsNone(normalizar_matricula(None))
        self.assertIsNone(normalizar_matricula(''))
        self.assertIsNone(normalizar_matricula('NULL'))
        self.assertIsNone(normalizar_matricula('null'))
        self.assertEqual(normalizar_matricula(' 2026001 '), '2026001')

    def test_unicidade_cruzada_aluno_curso_servidor(self):
        AlunoCurso().business.criar_vinculo(
            aluno_id=self.aluno.pk,
            curso_id=self.curso.pk,
            matricula='MAT-001',
        )
        with self.assertRaises(BusinessRuleException):
            Servidor().business.criar_servidor(
                usuario_pk=self.usuario_servidor.pk,
                cargo_pk=self.cargo.pk,
                categoria=CategoriaServidor.DOCENTE,
                matricula='MAT-001',
            )

    def test_unicidade_cruzada_servidor_terceirizado(self):
        Servidor().business.criar_servidor(
            usuario_pk=self.usuario_servidor.pk,
            cargo_pk=self.cargo.pk,
            categoria=CategoriaServidor.DOCENTE,
            matricula='MAT-002',
        )
        with self.assertRaises(BusinessRuleException):
            Terceirizado().business.criar_terceirizado(
                usuario_pk=self.usuario_terceirizado.pk,
                empresa_pk=self.empresa.pk,
                data_inicio='2024-01-01',
                matricula='MAT-002',
            )

    def test_tem_matricula_valida_respeita_ativo(self):
        vinculo = AlunoCurso().business.criar_vinculo(
            aluno_id=self.aluno.pk,
            curso_id=self.curso.pk,
            matricula='MAT-003',
        )
        self.assertTrue(self.usuario_aluno.helper.tem_matricula_valida())
        vinculo.business.encerrar(ano_conclusao=2025)
        self.assertFalse(self.usuario_aluno.helper.tem_matricula_valida())

    def test_buscar_por_matricula_valida(self):
        AlunoCurso().business.criar_vinculo(
            aluno_id=self.aluno.pk,
            curso_id=self.curso.pk,
            matricula='MAT-004',
        )
        usuario = Usuario().helper.buscar_por_matricula_valida('MAT-004')
        self.assertEqual(usuario, self.usuario_aluno)

    def test_buscar_por_matricula_inativa_retorna_none(self):
        vinculo = AlunoCurso().business.criar_vinculo(
            aluno_id=self.aluno.pk,
            curso_id=self.curso.pk,
            matricula='MAT-005',
        )
        vinculo.business.encerrar(ano_conclusao=2025)
        self.assertIsNone(Usuario().helper.buscar_por_matricula_valida('MAT-005'))
