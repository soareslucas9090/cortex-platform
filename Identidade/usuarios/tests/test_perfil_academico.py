"""
Testes de integração — Etapa 5.2 da Milestone 5
Valida a exposição do campo `tem_perfil_aluno` no domínio Identidade,
garantindo que a integração com o domínio Acadêmico ocorra exclusivamente
via reverse relation nativa do Django, sem acoplamento de código de produção.
"""
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


def criar_perfil_aluno(usuario):
    """Cria o Aluno diretamente, via model do domínio Acadêmico."""
    from Academico.alunos.models import Aluno
    return Aluno.objects.create(usuario=usuario)


class TemPerfilAlunoSerializerTest(APITestCase):
    """
    Garante que o campo tem_perfil_aluno reflete corretamente a existência
    (ou ausência) de um perfil de Aluno vinculado ao Usuário.
    """

    def setUp(self):
        self.admin = criar_usuario('00000000001', nome='Admin', is_admin=True)
        self.usuario_sem_perfil = criar_usuario('00000000002', nome='Sem Perfil')
        self.usuario_com_perfil = criar_usuario('00000000003', nome='Com Perfil')
        criar_perfil_aluno(self.usuario_com_perfil)
        self.token_admin = obter_tokens(self.admin)

    def test_usuario_sem_perfil_aluno_retorna_false(self):
        """Usuário sem Aluno associado deve ter tem_perfil_aluno=False."""
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_sem_perfil.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(resposta.data['dados']['tem_perfil_aluno'])

    def test_usuario_com_perfil_aluno_retorna_true(self):
        """Usuário com Aluno associado deve ter tem_perfil_aluno=True."""
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_com_perfil.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['tem_perfil_aluno'])

    def test_campo_presente_na_listagem(self):
        """O campo tem_perfil_aluno deve estar presente em cada objeto da listagem."""
        url = reverse('identidade:usuario-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        for usuario in resposta.data['dados']:
            self.assertIn('tem_perfil_aluno', usuario)

    def test_campo_e_booleano(self):
        """O campo tem_perfil_aluno deve ser do tipo bool, não None ou string."""
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_sem_perfil.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(url)
        valor = resposta.data['dados']['tem_perfil_aluno']
        self.assertIsInstance(valor, bool)

    def test_campo_atualiza_apos_criacao_do_perfil(self):
        """
        Após criar o perfil de Aluno para um usuário que não tinha,
        a API deve refletir tem_perfil_aluno=True imediatamente.
        """
        url = reverse('identidade:usuario-detail', kwargs={'pk': self.usuario_sem_perfil.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')

        resposta_antes = self.client.get(url)
        self.assertFalse(resposta_antes.data['dados']['tem_perfil_aluno'])

        criar_perfil_aluno(self.usuario_sem_perfil)

        resposta_depois = self.client.get(url)
        self.assertTrue(resposta_depois.data['dados']['tem_perfil_aluno'])
