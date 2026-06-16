# Organizacional/vinculos/tests/test_integracao_milestone_5.py

from rest_framework import status
from rest_framework.test import APITestCase

from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.terceirizados.models import Terceirizado
from Academico.alunos.models import Aluno
from Academico.cursos.models import Curso
from Organizacional.setores.models import Setor
from Organizacional.funcoes.models import Funcao
from Organizacional.vinculos.models import SetorVinculo
from Organizacional.vinculos.tests.test_views import criar_admin, obter_tokens

class ValidacaoIntegracaoMilestone5Test(APITestCase):
    """
    Suite de Testes de Integração E2E (Milestone 5.6)
    Valida os fluxos centrais entre Identidade, PessoasInstitucionais, Academico e Organizacional.
    """

    def setUp(self):
        # Usuário base para requisições com permissões globais
        self.admin = criar_admin(cpf='00000000001')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_tokens(self.admin)}')

        # Preparação do Domínio Organizacional (Catálogo Base)
        self.setor = Setor.objects.create(sigla='TEST_CCTI', nome='Coordenação de TI', ativo=True)
        self.funcao_chefe = Funcao.objects.create(papel_funcao='TEST_CHEFE', descricao='Chefe de Setor', ativo=True, e_gratificada=True)
        self.funcao_monitor = Funcao.objects.create(papel_funcao='TEST_MON', descricao='Monitor', ativo=True, exige_aluno=True)
        self.funcao_comum = Funcao.objects.create(papel_funcao='TEST_AUX', descricao='Auxiliar Administrativo', ativo=True)

        self.url_criar_vinculo = f'/cortex/organizacional/setores/{self.setor.pk}/vinculos/'

    def test_fluxo_servidor_responsavel_valido(self):
        """
        Cenário 2: Servidor (PessoasInstitucionais) -> Responsável pelo Setor (Organizacional)
        Verifica se um usuário com cargo de servidor pode assumir o setor.
        """
        usuario_servidor = Usuario.objects.create_user(cpf='11111111111', password='123', nome='Servidor Prof')
        cargo = Cargo.objects.create(nome='PROFESSOR EBTT', ativo=True)
        Servidor.objects.create(usuario=usuario_servidor, cargo=cargo, categoria=1)

        payload = {
            'usuario': usuario_servidor.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True
        }
        resposta = self.client.post(self.url_criar_vinculo, payload)
        
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['responsavel'])
        
        vinculo = SetorVinculo.objects.get(pk=resposta.data['dados']['id'])
        self.assertEqual(vinculo.usuario.nome, 'Servidor Prof')

    def test_fluxo_aluno_monitor_valido_e_invariante_responsavel(self):
        """
        Cenário 4: Aluno (Academico) -> Monitoria (Organizacional)
        Verifica a inserção acadêmica em um setor E restringe que ele seja responsável.
        """
        usuario_aluno = Usuario.objects.create_user(cpf='22222222222', password='123', nome='Aluno Monitor')
        curso = Curso.objects.create(nome='Técnico em Informática', codigo_curso='TEC')
        Aluno.objects.create(usuario=usuario_aluno, ativo=True)

        # 1. Aluno assume função de monitor (responsavel=False) -> DEVE PASSAR
        payload_valido = {
            'usuario': usuario_aluno.pk,
            'funcao': self.funcao_monitor.pk,
            'responsavel': False
        }
        resposta_ok = self.client.post(self.url_criar_vinculo, payload_valido)
        self.assertEqual(resposta_ok.status_code, status.HTTP_201_CREATED)

        # 2. Aluno tenta ser responsável do setor -> DEVE FALHAR (Invariante)
        payload_invalido = {
            'usuario': usuario_aluno.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True
        }
        resposta_erro = self.client.post(self.url_criar_vinculo, payload_invalido)
        self.assertEqual(resposta_erro.status_code, status.HTTP_400_BAD_REQUEST)
        # O erro padrão pode variar (ValidationException, BusinessRuleException), validamos que não é 201
        # No test_views.py: assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST) garante.

    def test_fluxo_terceirizado_valido_e_invariante_responsavel(self):
        """
        Cenário 5: Terceirizado (PessoasInstitucionais) -> Setor (Organizacional)
        Garante que perfis empresariais entram no setor, mas não cheifam.
        """
        usuario_terceirizado = Usuario.objects.create_user(cpf='33333333333', password='123', nome='Terceiro Limpeza')
        empresa = EmpresaInstituicao.objects.create(nome='Limp LTDA', cnpj='00000000000100', ativo=True)
        cargo = Cargo.objects.create(nome='Zelador', ativo=True)
        Terceirizado.objects.create(
            usuario=usuario_terceirizado,
            empresa_instituicao=empresa,
            cargo=cargo,
            data_inicio='2026-01-01',
        )

        # 1. Terceirizado no setor (responsavel=False) -> DEVE PASSAR
        payload_valido = {
            'usuario': usuario_terceirizado.pk,
            'funcao': self.funcao_comum.pk,
            'responsavel': False
        }
        resposta_ok = self.client.post(self.url_criar_vinculo, payload_valido)
        self.assertEqual(resposta_ok.status_code, status.HTTP_201_CREATED)

        # 2. Terceirizado tenta ser responsável -> DEVE FALHAR (Invariante)
        payload_invalido = {
            'usuario': usuario_terceirizado.pk,
            'funcao': self.funcao_chefe.pk,
            'responsavel': True
        }
        resposta_erro = self.client.post(self.url_criar_vinculo, payload_invalido)
        self.assertEqual(resposta_erro.status_code, status.HTTP_400_BAD_REQUEST)
