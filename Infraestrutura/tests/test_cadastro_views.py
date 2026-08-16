from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.salas.models import Sala
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_cadastrar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'CAD_{usuario.cpf}', descricao='Cadastrador')
    setor = Setor.objects.create(sigla=f'S{usuario.cpf[-3:]}', nome='Setor Teste')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, cadastrar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class CadastroInfraestruturaPermissoesTest(APITestCase):

    def setUp(self):
        self.usuario_l1 = criar_usuario('11111111111', nome='Aluno')
        self.usuario_cadastrador = conceder_capacidade_cadastrar(
            criar_usuario('22222222222', nome='Cadastrador'),
        )
        self.token_l1 = obter_tokens(self.usuario_l1)
        self.token_cadastrador = obter_tokens(self.usuario_cadastrador)
        self.url_blocos = reverse('infraestrutura:blocos-list')

    def test_l1_nao_pode_criar_bloco(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.post(self.url_blocos, {'nome': 'Bloco A'})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l1_pode_listar_blocos(self):
        Bloco.objects.create(nome='Bloco Existente')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_blocos)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_cadastrador_cria_edita_e_desativa_bloco(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_cadastrador}')

        resposta = self.client.post(self.url_blocos, {'nome': 'Bloco Novo'})
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        bloco_id = resposta.data['dados']['id']

        url_detalhe = reverse('infraestrutura:bloco-detail', kwargs={'pk': bloco_id})
        resposta = self.client.patch(url_detalhe, {'nome': 'Bloco Atualizado'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['nome'], 'Bloco Atualizado')

        url_desativar = reverse('infraestrutura:bloco-desativar', kwargs={'pk': bloco_id})
        resposta = self.client.post(url_desativar)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(Bloco.objects.get(pk=bloco_id).ativo)


class CadastroRecursosValidacaoTest(APITestCase):

    def setUp(self):
        self.usuario = conceder_capacidade_cadastrar(criar_usuario('33333333333', nome='Cad Recursos'))
        self.token = obter_tokens(self.usuario)
        self.bloco = Bloco.objects.create(nome='Bloco Teste')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala 101')
        self.url_recursos = reverse('infraestrutura:recursos-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_chave_sem_sala_retorna_400(self):
        resposta = self.client.post(self.url_recursos, {
            'codigo': 'CHV-001',
            'tipo': TipoRecurso.CHAVE,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chave_com_sala_cria_com_sucesso(self):
        resposta = self.client.post(self.url_recursos, {
            'codigo': 'CHV-002',
            'tipo': TipoRecurso.CHAVE,
            'sala_id': self.sala.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data['dados']['codigo'], 'CHV-002')
        self.assertEqual(resposta.data['dados']['sala']['id'], self.sala.pk)
        self.assertIsNone(resposta.data['dados']['foto'])

    def test_midia_sem_sala_cria_com_sucesso(self):
        resposta = self.client.post(self.url_recursos, {
            'codigo': 'MID-001',
            'tipo': TipoRecurso.MIDIA,
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resposta.data['dados']['sala'])
        self.assertIsNone(resposta.data['dados']['foto'])
