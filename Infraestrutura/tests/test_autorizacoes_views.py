import datetime

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Infraestrutura.autorizacoes.models import Autorizacao
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.salas.models import Sala
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_autorizar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'AUT_{usuario.cpf}', descricao='Autorizador')
    setor = Setor.objects.create(sigla=f'A{usuario.cpf[-3:]}', nome='Setor Autorizador')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, autorizar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class AutorizacoesViewsTest(APITestCase):

    def setUp(self):
        self.usuario_l1 = criar_usuario('12121212121', nome='Aluno')
        self.autorizador = conceder_capacidade_autorizar(
            criar_usuario('13131313131', nome='Autorizador API'),
        )
        self.beneficiario = criar_usuario('14141414141', nome='Beneficiário API')
        self.token_l1 = obter_tokens(self.usuario_l1)
        self.token_autorizador = obter_tokens(self.autorizador)
        self.bloco = Bloco.objects.create(nome='Bloco API')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala API')
        self.url_lista = reverse('infraestrutura:autorizacoes-list')
        self.hoje = datetime.date.today().isoformat()

    def test_l1_nao_pode_conceder_autorizacao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.post(self.url_lista, {
            'beneficiario_id': self.beneficiario.pk,
            'sala_id': self.sala.pk,
            'data_inicio': self.hoje,
        })
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_autorizador_concede_lista_e_revoga(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_autorizador}')

        resposta = self.client.post(self.url_lista, {
            'beneficiario_id': self.beneficiario.pk,
            'sala_id': self.sala.pk,
            'data_inicio': self.hoje,
            'observacao': 'Acesso temporário',
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        autorizacao_id = resposta.data['dados']['id']
        self.assertEqual(resposta.data['dados']['beneficiario']['id'], self.beneficiario.pk)
        self.assertTrue(resposta.data['dados']['vigente'])

        resposta = self.client.get(self.url_lista, {'beneficiario_id': self.beneficiario.pk})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resposta.data['dados']), 1)

        url_revogar = reverse('infraestrutura:autorizacao-revogar', kwargs={'pk': autorizacao_id})
        resposta = self.client.post(url_revogar)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(resposta.data['dados']['vigente'])
        self.assertIsNotNone(Autorizacao.objects.get(pk=autorizacao_id).revogado_em)

    def test_xor_sala_e_recurso_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_autorizador}')
        resposta = self.client.post(self.url_lista, {
            'beneficiario_id': self.beneficiario.pk,
            'sala_id': self.sala.pk,
            'recurso_id': 1,
            'data_inicio': self.hoje,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicata_mesmo_beneficiario_recurso_periodo_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_autorizador}')
        from Infraestrutura.recursos.choices import TipoRecurso
        from Infraestrutura.recursos.models import Recurso

        recurso = Recurso.objects.create(
            codigo='CHV-DUP',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        payload = {
            'beneficiario_id': self.beneficiario.pk,
            'recurso_id': recurso.pk,
            'data_inicio': self.hoje,
        }
        resposta = self.client.post(self.url_lista, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

        resposta = self.client.post(self.url_lista, payload)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reativar_autorizacao_revogada(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_autorizador}')
        from Infraestrutura.recursos.choices import TipoRecurso
        from Infraestrutura.recursos.models import Recurso

        recurso = Recurso.objects.create(
            codigo='CHV-REAT',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        resposta = self.client.post(self.url_lista, {
            'beneficiario_id': self.beneficiario.pk,
            'recurso_id': recurso.pk,
            'data_inicio': self.hoje,
        })
        autorizacao_id = resposta.data['dados']['id']

        url_revogar = reverse('infraestrutura:autorizacao-revogar', kwargs={'pk': autorizacao_id})
        self.client.post(url_revogar)

        url_reativar = reverse('infraestrutura:autorizacao-reativar', kwargs={'pk': autorizacao_id})
        resposta = self.client.post(url_reativar)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertTrue(resposta.data['dados']['vigente'])
        self.assertIsNone(resposta.data['dados']['revogado_em'])

    def test_reativar_com_sobreposicao_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_autorizador}')
        from Infraestrutura.recursos.choices import TipoRecurso
        from Infraestrutura.recursos.models import Recurso

        recurso = Recurso.objects.create(
            codigo='CHV-REAT2',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        payload = {
            'beneficiario_id': self.beneficiario.pk,
            'recurso_id': recurso.pk,
            'data_inicio': self.hoje,
        }
        resposta = self.client.post(self.url_lista, payload)
        autorizacao_id = resposta.data['dados']['id']

        url_revogar = reverse('infraestrutura:autorizacao-revogar', kwargs={'pk': autorizacao_id})
        self.client.post(url_revogar)

        resposta = self.client.post(self.url_lista, payload)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

        url_reativar = reverse('infraestrutura:autorizacao-reativar', kwargs={'pk': autorizacao_id})
        resposta = self.client.post(url_reativar)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
