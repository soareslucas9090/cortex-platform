from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao


def obter_tokens(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_usuario(cpf, nome='Usuário Teste', is_admin=False, **kwargs):
    return Usuario.objects.create_user(
        cpf=cpf,
        password='Senha@123',
        nome=nome,
        is_admin=is_admin,
        **kwargs,
    )


class UsuarioColetivoViewsTest(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('40000000001', nome='Admin Coletivo', is_admin=True, is_staff=True)
        self.comum = criar_usuario('40000000002', nome='Comum')
        self.conta = criar_usuario('40000000003', nome='Guarita', usuario_coletivo=True)
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)

        self.empresa = EmpresaInstituicao.objects.create(nome='Empresa Pool')
        self.cargo = Cargo.objects.create(nome='Cargo Pool', ativo=True)
        self.funcao = Funcao.objects.create(papel_funcao='GUARD', descricao='Guarda')
        self.setor = Setor.objects.create(sigla='GUA', nome='Guarita')

        self.url_coletivo = reverse('identidade:usuario-coletivo', kwargs={'pk': self.conta.pk})
        self.url_itens = reverse('identidade:usuario-coletivo-itens', kwargs={'pk': self.conta.pk})

    def test_criar_usuario_aceita_apenas_flag_coletivo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(reverse('identidade:usuario-list'), {
            'cpf': '40000000004',
            'nome': 'Nova Guarita',
            'usuario_coletivo': True,
            'empresas_coletivo_ids': [self.empresa.pk],
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        usuario = Usuario.objects.get(cpf='40000000004')
        self.assertTrue(usuario.usuario_coletivo)
        self.assertEqual(usuario.empresas_coletivo.count(), 0)

    def test_criar_usuario_coletivo_sem_cpf_exige_matricula(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(reverse('identidade:usuario-list'), {
            'nome': 'Guarita Sem CPF',
            'usuario_coletivo': True,
            'matricula': 'GUA001',
            'password': 'Senha@123',
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resposta.data['dados']['cpf'])
        self.assertTrue(resposta.data['dados']['usuario_coletivo'])
        usuario = Usuario.objects.get(id=resposta.data['dados']['id'])
        self.assertTrue(usuario.matriculas.filter(matricula='GUA001').exists())

    def test_criar_usuario_coletivo_sem_cpf_sem_matricula_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(reverse('identidade:usuario-list'), {
            'nome': 'Guarita Sem Identificador',
            'usuario_coletivo': True,
            'password': 'Senha@123',
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nao_admin_nao_acessa_coletivo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url_coletivo)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_obter_e_substituir_pool(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url_coletivo)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['usuario_coletivo'])
        self.assertEqual(resposta.data['dados']['empresas'], [])

        resposta = self.client.put(self.url_coletivo, {
            'empresas_ids': [self.empresa.pk],
            'cargos_ids': [self.cargo.pk],
            'funcoes_ids': [self.funcao.pk],
            'setores_ids': [self.setor.pk],
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']['empresas']), 1)
        self.assertEqual(resposta.data['dados']['empresas'][0]['id'], self.empresa.pk)
        self.assertEqual(len(resposta.data['dados']['setores']), 1)

        self.conta.refresh_from_db()
        self.assertEqual(self.conta.empresas_coletivo.count(), 1)
        self.assertEqual(self.conta.setores_coletivo.count(), 1)

    def test_substituir_exige_usuario_coletivo(self):
        url = reverse('identidade:usuario-coletivo', kwargs={'pk': self.comum.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.put(url, {
            'setores_ids': [self.setor.pk],
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adicionar_e_remover_item(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url_itens, {
            'tipo': 'setor',
            'id': self.setor.pk,
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.data['dados']['setores']), 1)

        url_remover = reverse(
            'identidade:usuario-coletivo-item-remover',
            kwargs={'pk': self.conta.pk, 'tipo': 'setor', 'item_id': self.setor.pk},
        )
        resposta = self.client.delete(url_remover)
        self.assertEqual(resposta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.conta.setores_coletivo.count(), 0)

    def test_desativar_flag_limpa_pool(self):
        self.conta.setores_coletivo.add(self.setor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(
            reverse('identidade:usuario-detail', kwargs={'pk': self.conta.pk}),
            {'usuario_coletivo': False},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.conta.refresh_from_db()
        self.assertFalse(self.conta.usuario_coletivo)
        self.assertEqual(self.conta.setores_coletivo.count(), 0)
