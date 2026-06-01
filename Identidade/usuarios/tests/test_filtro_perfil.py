from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.urls import reverse
from Identidade.usuarios.models import Usuario

def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123', is_admin=False, **kwargs):
    return Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
        is_admin=is_admin,
        **kwargs,
    )

def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)

class FiltroPerfilUsuariosViewTest(APITestCase):

    def setUp(self):
        # Admin para realizar as consultas
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.token_admin = obter_tokens(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        self.url = reverse('identidade:usuario-list')

        # Usuário 1: Apenas Usuário (sem perfil)
        self.usuario_comum = criar_usuario('00000000002', nome='Comum')

        # Usuário 2: Aluno
        self.usuario_aluno = criar_usuario('00000000003', nome='Aluno Teste')
        from Academico.alunos.models import Aluno
        Aluno.objects.create(usuario=self.usuario_aluno)

        # Usuário 3: Terceirizado
        self.usuario_terceirizado = criar_usuario('00000000004', nome='Terceirizado Teste')
        from PessoasInstitucionais.terceirizados.models import Terceirizado
        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
        self.empresa = EmpresaInstituicao.objects.create(nome="Empresa Teste", cnpj="12345678901234")
        Terceirizado.objects.create(
            usuario=self.usuario_terceirizado, 
            empresa_instituicao=self.empresa, 
            cargo_funcao="Serviços Gerais"
        )

        # Usuário 4: Servidor
        self.usuario_servidor = criar_usuario('00000000005', nome='Servidor Teste')
        from PessoasInstitucionais.servidores.models import Servidor
        from PessoasInstitucionais.cargos.models import Cargo
        self.cargo = Cargo.objects.create(nome="Cargo Teste", ativo=True)
        Servidor.objects.create(
            usuario=self.usuario_servidor, 
            cargo=self.cargo, 
            categoria=1 # CategoriaServidor.DOCENTE
        )

    def test_sem_filtro_retorna_todos(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        # Deve conter todos os 5 usuários (admin, comum, aluno, terceirizado, servidor)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(len(cpfs), 5)
        self.assertIn(self.usuario_comum.cpf, cpfs)
        self.assertIn(self.usuario_aluno.cpf, cpfs)
        self.assertIn(self.usuario_terceirizado.cpf, cpfs)
        self.assertIn(self.usuario_servidor.cpf, cpfs)

    def test_filtro_alunos_singular(self):
        resposta = self.client.get(self.url, {'tipo_perfil': 'aluno'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(len(cpfs), 1)
        self.assertIn(self.usuario_aluno.cpf, cpfs)

    def test_filtro_terceirizados_singular(self):
        resposta = self.client.get(self.url, {'tipo_perfil': 'terceirizado'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(len(cpfs), 1)
        self.assertIn(self.usuario_terceirizado.cpf, cpfs)

    def test_filtro_servidores_singular(self):
        resposta = self.client.get(self.url, {'tipo_perfil': 'servidor'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        cpfs = [u['cpf'] for u in resposta.data['dados']]
        self.assertEqual(len(cpfs), 1)
        self.assertIn(self.usuario_servidor.cpf, cpfs)

    def test_filtro_perfil_combinado_com_ativo(self):
        # Desativa o aluno
        self.usuario_aluno.ativo = False
        self.usuario_aluno.save()

        resposta = self.client.get(self.url, {'tipo_perfil': 'aluno', 'ativo': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 0)

        resposta = self.client.get(self.url, {'tipo_perfil': 'aluno', 'ativo': 'false'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['cpf'], self.usuario_aluno.cpf)

    def test_filtro_perfil_combinado_com_nome(self):
        resposta = self.client.get(self.url, {'tipo_perfil': 'servidor', 'nome': 'Servidor'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

        resposta = self.client.get(self.url, {'tipo_perfil': 'servidor', 'nome': 'Aluno'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 0)
