# Organizacional/vinculos/tests/test_integracao_milestone_5.py
"""
Suite de validação funcional mínima — Etapa 5.6 da Milestone 5.

Cobre os fluxos centrais entre Identidade, PessoasInstitucionais, Academico
e Organizacional, alinhados a docs/project/test-users-and-seed-scenarios.md
e à checklist de validação funcional mínima.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from Academico.aluno_cursos.models import AlunoCurso
from Academico.alunos.models import Aluno
from Academico.cursos.models import Curso
from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from Organizacional.vinculos.tests.test_views import criar_admin, obter_tokens
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.servidores.choices import CategoriaServidor
from PessoasInstitucionais.servidores.models import Servidor
from PessoasInstitucionais.terceirizados.models import Terceirizado


class ValidacaoIntegracaoMilestone5Test(APITestCase):
    """Cenários interdomínio prioritários (responsável, monitor, terceirizado)."""

    def setUp(self):
        self.admin = criar_admin(cpf='00000000001')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(self.admin)}')

        self.setor = Setor.objects.create(sigla='TEST_CCTI', nome='Coordenação de TI', ativo=True)
        self.setor_b = Setor.objects.create(sigla='TEST_DIAP', nome='DIAP', ativo=True)
        self.funcao_chefe = Funcao.objects.create(
            papel_funcao='TEST_CHEFE', descricao='Chefe de Setor', ativo=True, e_gratificada=True,
        )
        self.funcao_monitor = Funcao.objects.create(
            papel_funcao='TEST_MON', descricao='Monitor', ativo=True, exige_aluno=True,
        )
        self.funcao_comum = Funcao.objects.create(
            papel_funcao='TEST_AUX', descricao='Auxiliar Administrativo', ativo=True,
        )
        self.funcao_membro = Funcao.objects.create(
            papel_funcao='TEST_MEM', descricao='Membro', ativo=True,
        )

        self.url_criar_vinculo = reverse(
            'organizacional:vinculos', kwargs={'setor_pk': self.setor.pk},
        )

    def test_fluxo_servidor_responsavel_valido(self):
        """Cenário 2: servidor com cargo assume responsabilidade do setor."""
        usuario_servidor = Usuario.objects.create_user(
            cpf='11111111111', password='Senha@123', nome='Servidor Prof',
        )
        cargo = Cargo.objects.create(nome='PROFESSOR EBTT', ativo=True)
        Servidor.objects.create(usuario=usuario_servidor, cargo=cargo, categoria=1)

        resposta = self.client.post(self.url_criar_vinculo, {
            'usuario': usuario_servidor.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True,
        })

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['responsavel'])
        vinculo = SetorVinculo.objects.get(pk=resposta.data['dados']['id'])
        self.assertEqual(vinculo.usuario.nome, 'Servidor Prof')

    def test_fluxo_servidor_multiplos_vinculos(self):
        """Cenário 3: mesmo servidor com vínculos em setores distintos."""
        usuario = Usuario.objects.create_user(
            cpf='22222222222', password='Senha@123', nome='Tecnico MultiSetor',
        )
        cargo = Cargo.objects.create(nome='TECNICO DE TI', ativo=True)
        Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=2)

        url_a = reverse('organizacional:vinculos', kwargs={'setor_pk': self.setor.pk})
        url_b = reverse('organizacional:vinculos', kwargs={'setor_pk': self.setor_b.pk})

        r1 = self.client.post(url_a, {
            'usuario': usuario.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': False,
        })
        r2 = self.client.post(url_b, {
            'usuario': usuario.pk,
            'funcao': self.funcao_membro.pk,
            'responsavel': False,
        })

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.data)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED, r2.data)
        self.assertEqual(SetorVinculo.objects.filter(usuario=usuario).count(), 2)

    def test_fluxo_aluno_regular_com_curso(self):
        """Aluno regular com vínculo acadêmico, sem obrigação organizacional."""
        usuario = Usuario.objects.create_user(
            cpf='44444444444', password='Senha@123', nome='Aluno Regular',
        )
        aluno = Aluno.objects.create(usuario=usuario, ativo=True)
        curso = Curso.objects.create(nome='ADS', codigo_curso='ADS56')

        resposta = self.client.post('/cortex/academico/aluno-cursos/', {
            'aluno': aluno.pk,
            'curso': curso.pk,
        }, format='json')

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        self.assertTrue(
            AlunoCurso.objects.filter(aluno=aluno, curso=curso, ativo=True).exists()
        )
        self.assertFalse(
            SetorVinculo.objects.filter(usuario=usuario).exists()
        )

    def test_fluxo_aluno_monitor_valido_e_invariante_responsavel(self):
        """Cenário 4: monitoria no organizacional; aluno não pode ser responsável."""
        usuario_aluno = Usuario.objects.create_user(
            cpf='55555555555', password='Senha@123', nome='Aluno Monitor',
        )
        curso = Curso.objects.create(nome='Licenciatura em Matemática', codigo_curso='MAT')
        aluno = Aluno.objects.create(usuario=usuario_aluno, ativo=True)
        AlunoCurso.objects.create(aluno=aluno, curso=curso)

        resposta_ok = self.client.post(self.url_criar_vinculo, {
            'usuario': usuario_aluno.pk,
            'funcao': self.funcao_monitor.pk,
            'responsavel': False,
        })
        self.assertEqual(resposta_ok.status_code, status.HTTP_201_CREATED)

        resposta_erro = self.client.post(self.url_criar_vinculo, {
            'usuario': usuario_aluno.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True,
        })
        self.assertEqual(resposta_erro.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fluxo_terceirizado_valido_e_invariante_responsavel(self):
        """Cenário 5: terceirizado entra no setor, mas não assume responsabilidade."""
        usuario_terceirizado = Usuario.objects.create_user(
            cpf='66666666666', password='Senha@123', nome='Terceiro Limpeza',
        )
        empresa = EmpresaInstituicao.objects.create(
            nome='Limp LTDA', cnpj='00000000000100', ativo=True,
        )
        cargo = Cargo.objects.create(nome='Zelador', ativo=True)
        Terceirizado.objects.create(
            usuario=usuario_terceirizado,
            empresa_instituicao=empresa,
            cargo=cargo,
            data_inicio='2026-01-01',
        )

        resposta_ok = self.client.post(self.url_criar_vinculo, {
            'usuario': usuario_terceirizado.pk,
            'funcao': self.funcao_comum.pk,
            'responsavel': False,
        })
        self.assertEqual(resposta_ok.status_code, status.HTTP_201_CREATED)

        resposta_erro = self.client.post(self.url_criar_vinculo, {
            'usuario': usuario_terceirizado.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True,
        })
        self.assertEqual(resposta_erro.status_code, status.HTTP_400_BAD_REQUEST)


class ValidacaoFuncionalMinimaE2ETest(APITestCase):
    """
    Percorre via API os itens da checklist de validação funcional mínima:
    usuário → catálogos → servidor/responsável → aluno/curso/monitor → terceirizado.
    """

    def setUp(self):
        self.admin = criar_admin(cpf='00000000099')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(self.admin)}')

    def test_checklist_validacao_funcional_minima_via_api(self):
        # 1. Criar usuário com CPF (servidor futuro)
        r_usuario_servidor = self.client.post(
            reverse('identidade:usuario-list'),
            {'cpf': '11111111111', 'nome': 'Professor Responsavel', 'password': 'Senha@123'},
        )
        self.assertEqual(r_usuario_servidor.status_code, status.HTTP_201_CREATED, r_usuario_servidor.data)
        usuario_servidor_id = r_usuario_servidor.data['dados']['id']

        # 2. Catálogos: cargo, setor, funções, curso, empresa
        r_cargo = self.client.post(
            reverse('pessoas-institucionais:cargo-list'),
            {'nome': 'PROFESSOR EBTT'},
            format='json',
        )
        self.assertEqual(r_cargo.status_code, status.HTTP_201_CREATED, r_cargo.data)
        cargo_id = r_cargo.data['dados']['id']

        r_setor = self.client.post(
            reverse('organizacional:setores'),
            {'nome': 'Coordenação de Sistemas', 'sigla': 'CODIS56'},
        )
        self.assertEqual(r_setor.status_code, status.HTTP_201_CREATED, r_setor.data)
        setor_id = r_setor.data['dados']['id']

        r_funcao_coord = self.client.post(
            reverse('organizacional:funcoes'),
            {
                'papel_funcao': 'COORD_56',
                'categoria': 'coordenador',
                'descricao': 'Coordenador',
                'e_gratificada': True,
            },
        )
        self.assertEqual(r_funcao_coord.status_code, status.HTTP_201_CREATED, r_funcao_coord.data)
        funcao_coord_id = r_funcao_coord.data['dados']['id']

        r_funcao_monitor = self.client.post(
            reverse('organizacional:funcoes'),
            {
                'papel_funcao': 'MONITOR_56',
                'categoria': 'coordenador',
                'descricao': 'Monitor',
                'exige_aluno': True,
            },
        )
        self.assertEqual(r_funcao_monitor.status_code, status.HTTP_201_CREATED, r_funcao_monitor.data)
        funcao_monitor_id = r_funcao_monitor.data['dados']['id']

        r_curso = self.client.post(
            reverse('academico:curso-list'),
            {'nome': 'Análise e Desenvolvimento de Sistemas', 'codigo_curso': 'ADS-56'},
            format='json',
        )
        self.assertEqual(r_curso.status_code, status.HTTP_201_CREATED, r_curso.data)
        curso_id = r_curso.data['dados']['id']

        r_empresa = self.client.post(
            reverse('pessoas-institucionais:empresa-list'),
            {'nome': 'EMPRESA LIMPEZA IFPI', 'cnpj': '11222333000181'},
            format='json',
        )
        self.assertEqual(r_empresa.status_code, status.HTTP_201_CREATED, r_empresa.data)
        empresa_id = r_empresa.data['dados']['id']

        # 3. Criar servidor com cargo
        r_servidor = self.client.post(
            reverse('pessoas-institucionais:servidor-list'),
            {
                'usuario_pk': usuario_servidor_id,
                'cargo_pk': cargo_id,
                'categoria': CategoriaServidor.DOCENTE,
            },
            format='json',
        )
        self.assertEqual(r_servidor.status_code, status.HTTP_201_CREATED, r_servidor.data)
        self.assertTrue(Servidor.objects.filter(usuario_id=usuario_servidor_id).exists())

        # 4–5. Vincular servidor ao setor com função e definir responsável
        url_vinculos = reverse('organizacional:vinculos', kwargs={'setor_pk': setor_id})
        r_vinculo_resp = self.client.post(url_vinculos, {
            'usuario': usuario_servidor_id,
            'funcao': funcao_coord_id,
            'responsavel': True,
        })
        self.assertEqual(r_vinculo_resp.status_code, status.HTTP_201_CREATED, r_vinculo_resp.data)
        self.assertTrue(r_vinculo_resp.data['dados']['responsavel'])

        # 6–7. Criar aluno e vincular a curso
        r_usuario_aluno = self.client.post(
            reverse('identidade:usuario-list'),
            {'cpf': '55555555555', 'nome': 'Aluno Monitor', 'password': 'Senha@123'},
        )
        self.assertEqual(r_usuario_aluno.status_code, status.HTTP_201_CREATED, r_usuario_aluno.data)
        usuario_aluno_id = r_usuario_aluno.data['dados']['id']

        r_aluno = self.client.post(
            '/cortex/academico/alunos/',
            {'usuario': usuario_aluno_id, 'ativo': True},
            format='json',
        )
        self.assertEqual(r_aluno.status_code, status.HTTP_201_CREATED, r_aluno.data)
        aluno_id = r_aluno.data['dados']['usuario_id']

        r_aluno_curso = self.client.post(
            '/cortex/academico/aluno-cursos/',
            {'aluno': aluno_id, 'curso': curso_id},
            format='json',
        )
        self.assertEqual(r_aluno_curso.status_code, status.HTTP_201_CREATED, r_aluno_curso.data)

        # 8. Vincular aluno monitor ao setor com função monitor
        r_monitor = self.client.post(url_vinculos, {
            'usuario': usuario_aluno_id,
            'funcao': funcao_monitor_id,
            'responsavel': False,
        })
        self.assertEqual(r_monitor.status_code, status.HTTP_201_CREATED, r_monitor.data)

        # 9. Criar terceirizado com empresa
        r_usuario_terc = self.client.post(
            reverse('identidade:usuario-list'),
            {'cpf': '66666666666', 'nome': 'Terceirizado Limpeza', 'password': 'Senha@123'},
        )
        self.assertEqual(r_usuario_terc.status_code, status.HTTP_201_CREATED, r_usuario_terc.data)
        usuario_terc_id = r_usuario_terc.data['dados']['id']

        r_terceirizado = self.client.post(
            reverse('pessoas-institucionais:terceirizado-list'),
            {
                'usuario_pk': usuario_terc_id,
                'empresa_pk': empresa_id,
                'data_inicio': '2026-01-01',
            },
            format='json',
        )
        self.assertEqual(r_terceirizado.status_code, status.HTTP_201_CREATED, r_terceirizado.data)
        self.assertTrue(Terceirizado.objects.filter(usuario_id=usuario_terc_id).exists())

        # Coerência final: identidade expõe perfis; monitoria permanece no organizacional
        r_detalhe_servidor = self.client.get(
            reverse('identidade:usuario-detail', kwargs={'pk': usuario_servidor_id}),
        )
        self.assertEqual(r_detalhe_servidor.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(r_detalhe_servidor.data['dados']['servidor'])
        self.assertFalse(r_detalhe_servidor.data['dados']['tem_perfil_aluno'])

        r_detalhe_aluno = self.client.get(
            reverse('identidade:usuario-detail', kwargs={'pk': usuario_aluno_id}),
        )
        self.assertEqual(r_detalhe_aluno.status_code, status.HTTP_200_OK)
        self.assertTrue(r_detalhe_aluno.data['dados']['tem_perfil_aluno'])
        self.assertIsNone(r_detalhe_aluno.data['dados']['servidor'])

        self.assertEqual(SetorVinculo.objects.filter(setor_id=setor_id).count(), 2)
        self.assertTrue(
            SetorVinculo.objects.filter(
                setor_id=setor_id, usuario_id=usuario_servidor_id, responsavel=True,
            ).exists()
        )
        self.assertTrue(
            SetorVinculo.objects.filter(
                setor_id=setor_id,
                usuario_id=usuario_aluno_id,
                funcao_id=funcao_monitor_id,
                responsavel=False,
            ).exists()
        )

    def test_login_por_cpf_apos_criacao_via_api(self):
        """Garante login híbrido por CPF após criação do usuário."""
        cpf = '77777777777'
        password = 'Senha@123'
        r_usuario = self.client.post(
            reverse('identidade:usuario-list'),
            {'cpf': cpf, 'nome': 'Usuario Login CPF', 'password': password},
        )
        self.assertEqual(r_usuario.status_code, status.HTTP_201_CREATED, r_usuario.data)

        self.client.credentials()
        r_login = self.client.post(
            '/cortex/auth/token_jwt/',
            {'login': cpf, 'password': password},
            format='json',
        )
        self.assertEqual(r_login.status_code, status.HTTP_200_OK, r_login.data)
        self.assertIn('access', r_login.data.get('dados', r_login.data))


class ValidacaoInvariantesCruzadasTest(APITestCase):
    """Erros mínimos cruzados já definidos nos cenários de seed."""

    def setUp(self):
        self.admin = criar_admin(cpf='00000000088')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(self.admin)}')
        self.setor = Setor.objects.create(sigla='INV56', nome='Setor Invariantes', ativo=True)
        self.funcao = Funcao.objects.create(
            papel_funcao='INV_AUX', descricao='Auxiliar', ativo=True,
        )
        self.url_vinculos = reverse(
            'organizacional:vinculos', kwargs={'setor_pk': self.setor.pk},
        )

    def test_vinculo_sem_funcao_falha(self):
        usuario = Usuario.objects.create_user(
            cpf='88888888881', password='Senha@123', nome='Sem Funcao',
        )
        resposta = self.client.post(self.url_vinculos, {'usuario': usuario.pk})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_servidor_sem_cargo_falha(self):
        usuario = Usuario.objects.create_user(
            cpf='88888888882', password='Senha@123', nome='Sem Cargo',
        )
        resposta = self.client.post(
            reverse('pessoas-institucionais:servidor-list'),
            {'usuario_pk': usuario.pk, 'categoria': CategoriaServidor.DOCENTE},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_terceirizado_sem_empresa_falha(self):
        usuario = Usuario.objects.create_user(
            cpf='88888888883', password='Senha@123', nome='Sem Empresa',
        )
        resposta = self.client.post(
            reverse('pessoas-institucionais:terceirizado-list'),
            {'usuario_pk': usuario.pk, 'data_inicio': '2026-01-01'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cpf_duplicado_falha(self):
        Usuario.objects.create_user(
            cpf='88888888884', password='Senha@123', nome='Existente',
        )
        resposta = self.client.post(
            reverse('identidade:usuario-list'),
            {'cpf': '88888888884', 'nome': 'Duplicado', 'password': 'Senha@123'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remover_unico_responsavel_falha(self):
        usuario = Usuario.objects.create_user(
            cpf='88888888885', password='Senha@123', nome='Unico Responsavel',
        )
        cargo = Cargo.objects.create(nome='Cargo Unico', ativo=True)
        Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1)
        vinculo = SetorVinculo.objects.create(
            usuario=usuario,
            setor=self.setor,
            funcao=self.funcao,
            responsavel=True,
        )

        url = reverse(
            'organizacional:vinculo-remover-responsavel',
            kwargs={'setor_pk': self.setor.pk, 'pk': vinculo.pk},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        vinculo.refresh_from_db()
        self.assertTrue(vinculo.responsavel)
