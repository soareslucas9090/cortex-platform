from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor


def obter_tokens(usuario):
    """Retorna o access token JWT para o usuário informado."""
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome, is_admin=True)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def criar_setor(sigla='TI', nome='Tecnologia da Informação', ativo=True):
    return Setor.objects.create(sigla=sigla, nome=nome, ativo=ativo)


def criar_funcao(sigla='AUX', descricao='Auxiliar Técnico', ativo=True):
    return Funcao.objects.create(sigla=sigla, descricao=descricao, ativo=ativo)


def criar_vinculo(usuario, setor, funcao, responsavel=False):
    return SetorVinculo.objects.create(
        usuario=usuario, setor=setor, funcao=funcao, responsavel=responsavel,
    )


class ListarVinculosViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.url = reverse('organizacional:vinculos', kwargs={'setor_pk': self.setor.pk})

    def test_admin_lista_vinculos_com_sucesso(self):
        funcao = criar_funcao()
        criar_vinculo(self.admin, self.setor, funcao)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], 'success')
        self.assertIn('dados', resposta.data)

    def test_lista_apenas_vinculos_do_setor_informado(self):
        outro_setor = criar_setor(sigla='RH', nome='Recursos Humanos')
        funcao = criar_funcao()
        criar_vinculo(self.admin, self.setor, funcao)
        criar_vinculo(self.comum, outro_setor, funcao)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids_usuarios = [v['usuario'] for v in resposta.data['dados']]
        self.assertIn(self.admin.pk, ids_usuarios)
        self.assertNotIn(self.comum.pk, ids_usuarios)

    def test_usuario_comum_nao_pode_listar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_sem_vinculos_retorna_lista_vazia(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])


class CriarVinculoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.funcao = criar_funcao()
        self.url = reverse('organizacional:vinculos', kwargs={'setor_pk': self.setor.pk})
        self.payload_valido = {
            'usuario': self.comum.pk,
            'funcao': self.funcao.pk,
        }

    def test_admin_cria_vinculo_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['dados']['usuario'], self.comum.pk)

    def test_cria_vinculo_como_responsavel(self):
        cargo = Cargo.objects.create(nome='Professor')
        Servidor.objects.create(usuario=self.comum, cargo=cargo, categoria=1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {**self.payload_valido, 'responsavel': True}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resposta.data['dados']['responsavel'])

    def test_responsavel_padrao_e_false(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resposta.data['dados']['responsavel'])

    def test_usuario_comum_nao_pode_criar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_inativo_retorna_400(self):
        setor_inativo = criar_setor(sigla='IN', nome='Inativo', ativo=False)
        url = reverse('organizacional:vinculos', kwargs={'setor_pk': setor_inativo.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_funcao_inativa_retorna_400(self):
        funcao_inativa = criar_funcao(sigla='IN', descricao='Inativa', ativo=False)
        payload = {'usuario': self.comum.pk, 'funcao': funcao_inativa.pk}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_duplicado_retorna_400(self):
        criar_vinculo(self.comum, self.setor, self.funcao)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, self.payload_valido)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mesmo_usuario_pode_ter_vinculos_com_funcoes_diferentes(self):
        outra_funcao = criar_funcao(sigla='ADM', descricao='Administrador')
        criar_vinculo(self.comum, self.setor, self.funcao)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        payload = {'usuario': self.comum.pk, 'funcao': outra_funcao.pk}
        resposta = self.client.post(self.url, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_usuario_obrigatorio_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'funcao': self.funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_funcao_obrigatoria_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url, {'usuario': self.comum.pk})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)


class EncerrarVinculoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.funcao = criar_funcao()
        self.vinculo = criar_vinculo(self.comum, self.setor, self.funcao)
        self.url = reverse(
            'organizacional:vinculo-encerrar',
            kwargs={'setor_pk': self.setor.pk, 'pk': self.vinculo.pk},
        )

    def test_admin_encerra_vinculo_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(SetorVinculo.objects.filter(pk=self.vinculo.pk).exists())

    def test_usuario_comum_nao_pode_encerrar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vinculo_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'organizacional:vinculo-encerrar',
            kwargs={'setor_pk': self.setor.pk, 'pk': 99999},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_bloqueado_se_unico_responsavel(self):
        self.vinculo.responsavel = True
        self.vinculo.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_encerra_responsavel_quando_ha_outro_responsavel(self):
        outra_funcao = criar_funcao(sigla='ADM', descricao='Administrador')
        outro_vinculo = criar_vinculo(self.admin, self.setor, outra_funcao, responsavel=True)
        self.vinculo.responsavel = True
        self.vinculo.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_vinculo_de_outro_setor_retorna_404(self):
        outro_setor = criar_setor(sigla='RH', nome='Recursos Humanos')
        url = reverse(
            'organizacional:vinculo-encerrar',
            kwargs={'setor_pk': outro_setor.pk, 'pk': self.vinculo.pk},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class DefinirResponsavelViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.funcao = criar_funcao()
        self.vinculo = criar_vinculo(self.comum, self.setor, self.funcao, responsavel=False)
        self.url = reverse(
            'organizacional:vinculo-definir-responsavel',
            kwargs={'setor_pk': self.setor.pk, 'pk': self.vinculo.pk},
        )

    def test_admin_define_responsavel_com_sucesso(self):
        cargo = Cargo.objects.create(nome='Professor')
        Servidor.objects.create(usuario=self.comum, cargo=cargo, categoria=1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.vinculo.refresh_from_db()
        self.assertTrue(self.vinculo.responsavel)

    def test_usuario_comum_nao_pode_definir_responsavel(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_setor_inativo_retorna_400(self):
        self.setor.ativo = False
        self.setor.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'organizacional:vinculo-definir-responsavel',
            kwargs={'setor_pk': self.setor.pk, 'pk': 99999},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_vinculo_de_outro_setor_retorna_404(self):
        outro_setor = criar_setor(sigla='RH', nome='Recursos Humanos')
        url = reverse(
            'organizacional:vinculo-definir-responsavel',
            kwargs={'setor_pk': outro_setor.pk, 'pk': self.vinculo.pk},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class RemoverResponsavelViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.funcao = criar_funcao()
        # Criar dois vínculos responsáveis para que a remoção seja permitida
        outra_funcao = criar_funcao(sigla='ADM', descricao='Administrador')
        self.vinculo = criar_vinculo(self.comum, self.setor, self.funcao, responsavel=True)
        self.outro_vinculo = criar_vinculo(self.admin, self.setor, outra_funcao, responsavel=True)
        self.url = reverse(
            'organizacional:vinculo-remover-responsavel',
            kwargs={'setor_pk': self.setor.pk, 'pk': self.vinculo.pk},
        )

    def test_admin_remove_responsavel_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.vinculo.refresh_from_db()
        self.assertFalse(self.vinculo.responsavel)

    def test_usuario_comum_nao_pode_remover_responsavel(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bloqueado_se_unico_responsavel(self):
        # Remover o segundo responsável para que o primeiro seja o único
        self.outro_vinculo.responsavel = False
        self.outro_vinculo.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'organizacional:vinculo-remover-responsavel',
            kwargs={'setor_pk': self.setor.pk, 'pk': 99999},
        )
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_vinculo_de_outro_setor_retorna_404(self):
        outro_setor = criar_setor(sigla='RH', nome='Recursos Humanos')
        url = reverse(
            'organizacional:vinculo-remover-responsavel',
            kwargs={'setor_pk': outro_setor.pk, 'pk': self.vinculo.pk},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


class AtualizarVinculoFuncaoViewTest(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.comum = criar_usuario_comum()
        self.token_admin = obter_tokens(self.admin)
        self.token_comum = obter_tokens(self.comum)
        self.setor = criar_setor()
        self.funcao = criar_funcao(sigla='AUX', descricao='Auxiliar')
        self.nova_funcao = criar_funcao(sigla='ADM', descricao='Administrador')
        self.vinculo = criar_vinculo(self.comum, self.setor, self.funcao)
        self.url = reverse(
            'organizacional:vinculo-atualizar-funcao',
            kwargs={'setor_pk': self.setor.pk, 'pk': self.vinculo.pk},
        )

    def test_admin_atualiza_funcao_com_sucesso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.vinculo.refresh_from_db()
        self.assertEqual(self.vinculo.funcao_id, self.nova_funcao.pk)

    def test_usuario_comum_nao_pode_atualizar(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_comum}')
        resposta = self.client.patch(self.url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.patch(self.url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funcao_inativa_retorna_400(self):
        funcao_inativa = criar_funcao(sigla='IN', descricao='Inativa', ativo=False)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'funcao': funcao_inativa.pk})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_duplicado_retorna_400(self):
        # Criar outro vínculo com a nova_funcao para causar duplicata
        criar_vinculo(self.comum, self.setor, self.nova_funcao)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_inexistente_retorna_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        url = reverse(
            'organizacional:vinculo-atualizar-funcao',
            kwargs={'setor_pk': self.setor.pk, 'pk': 99999},
        )
        resposta = self.client.patch(url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_funcao_obrigatoria_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(self.url, {})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vinculo_de_outro_setor_retorna_404(self):
        outro_setor = criar_setor(sigla='RH', nome='Recursos Humanos')
        url = reverse(
            'organizacional:vinculo-atualizar-funcao',
            kwargs={'setor_pk': outro_setor.pk, 'pk': self.vinculo.pk},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin}')
        resposta = self.client.patch(url, {'funcao': self.nova_funcao.pk})
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
