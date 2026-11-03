from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS
from AcessoCampus.tipos.models import TipoAutorizacaoAcesso
from Identidade.usuarios.models import Usuario


def token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


class TiposAutorizacaoTest(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            cpf='30000000001',
            password='Senha@123',
            nome='Usuário comum',
        )
        self.url_lista = reverse('acesso_campus:tipo-autorizacao-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(self.usuario)}')

    def test_catalogo_semeado_contem_entrada_e_saida(self):
        nomes = set(TipoAutorizacaoAcesso.objects.filter(eh_base=True).values_list('nome', flat=True))
        self.assertEqual(nomes, {NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS})
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        nomes_api = {item['nome'] for item in resposta.data['dados']}
        self.assertIn(NOME_TIPO_ENTRADA_CAMPUS, nomes_api)
        self.assertIn(NOME_TIPO_SAIDA_CAMPUS, nomes_api)

    def test_usuario_comum_pode_listar_e_detalhar(self):
        entrada = TipoAutorizacaoAcesso.objects.get(nome=NOME_TIPO_ENTRADA_CAMPUS)
        lista = self.client.get(self.url_lista)
        self.assertEqual(lista.status_code, status.HTTP_200_OK)

        detalhe = self.client.get(
            reverse('acesso_campus:tipo-autorizacao-detail', kwargs={'pk': entrada.pk}),
        )
        self.assertEqual(detalhe.status_code, status.HTTP_200_OK)
        self.assertEqual(detalhe.data['dados']['nome'], NOME_TIPO_ENTRADA_CAMPUS)
        self.assertTrue(detalhe.data['dados']['eh_base'])

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url_lista).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_ativo_true_retorna_somente_ativos(self):
        TipoAutorizacaoAcesso.objects.create(nome='Tipo Ativo', ativo=True)
        TipoAutorizacaoAcesso.objects.create(nome='Tipo Inativo', ativo=False)
        resposta = self.client.get(self.url_lista, {'ativo': 'true'})
        nomes = {item['nome'] for item in resposta.data['dados']}
        self.assertIn('Tipo Ativo', nomes)
        self.assertNotIn('Tipo Inativo', nomes)

    def test_post_tipos_nao_existe(self):
        resposta = self.client.post(self.url_lista, {'nome': 'Prova externa'}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_desativar_tipo_base_falha(self):
        entrada = TipoAutorizacaoAcesso.objects.get(nome=NOME_TIPO_ENTRADA_CAMPUS)
        with self.assertRaises(BusinessRuleException):
            entrada.business.desativar()
        entrada.refresh_from_db()
        self.assertTrue(entrada.ativo)

    def test_tipo_extra_aparece_no_catalogo(self):
        extra = TipoAutorizacaoAcesso.objects.create(nome='Prova externa')
        resposta = self.client.get(self.url_lista)
        nomes = {item['nome'] for item in resposta.data['dados']}
        self.assertIn('Prova externa', nomes)
        self.assertFalse(extra.eh_base)
