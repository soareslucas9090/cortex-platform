from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Notificacoes.notificacoes.choices import CanalSistema
from Notificacoes.notificacoes.models import Notificacao


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste', password='Senha@123'):
    return Usuario.objects.create_user(
        cpf=cpf,
        password=password,
        nome=nome,
    )


def disparar_inbox(usuario, tipo='teste.inbox', titulo='Título', corpo='Corpo', **kwargs):
    return Notificacao().business.disparar(
        destinatario_id=usuario.pk,
        tipo=tipo,
        titulo=titulo,
        corpo=corpo,
        canais=[CanalSistema],
        **kwargs,
    )


class NotificacoesInboxAPITest(APITestCase):

    def setUp(self):
        self.usuario = criar_usuario('80000000001', nome='Destinatário')
        self.outro = criar_usuario('80000000002', nome='Outro')
        self.token = obter_tokens(self.usuario)
        self.token_outro = obter_tokens(self.outro)
        self.url_lista = reverse('notificacoes:notificacao-list')
        self.url_contador = reverse('notificacoes:notificacao-nao-lidas-contador')
        self.url_marcar_todas = reverse('notificacoes:notificacao-marcar-todas-lidas')

    def test_nao_autenticado_retorna_401(self):
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)
        resposta = self.client.get(self.url_contador)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)
        notif = disparar_inbox(self.usuario)
        url_lida = reverse('notificacoes:notificacao-lida', kwargs={'pk': notif.pk})
        resposta = self.client.patch(url_lida)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)
        resposta = self.client.patch(self.url_marcar_todas)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lista_apenas_proprias_notificacoes(self):
        minha = disparar_inbox(self.usuario, titulo='Minha')
        disparar_inbox(self.outro, titulo='De outro')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertEqual(ids, [minha.pk])

    def test_servidor_l2_nao_ve_notificacao_de_outro(self):
        from PessoasInstitucionais.cargos.models import Cargo
        from PessoasInstitucionais.servidores.models import Servidor

        cargo = Cargo.objects.create(nome='Cargo L2 Notif')
        servidor_user = criar_usuario('80000000003', nome='Servidor L2 Notif')
        Servidor.objects.create(usuario=servidor_user, cargo=cargo, categoria=1, ativo=True)
        token_servidor = obter_tokens(servidor_user)

        notif_outro = disparar_inbox(self.outro, titulo='Privada')
        disparar_inbox(servidor_user, titulo='Do servidor')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_servidor}')
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        titulos = [item['titulo'] for item in resposta.data['dados']]
        self.assertNotIn('Privada', titulos)

        url_lida_outro = reverse('notificacoes:notificacao-lida', kwargs={'pk': notif_outro.pk})
        resposta = self.client.patch(url_lida_outro)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_l3_nao_ve_nem_marca_notificacao_de_outro(self):
        admin = Usuario.objects.create_superuser(
            cpf='80000000004',
            password='Senha@123',
            nome='Admin L3 Notif',
        )
        token_admin = obter_tokens(admin)
        notif_outro = disparar_inbox(self.outro, titulo='Privada L3')
        disparar_inbox(admin, titulo='Do admin')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        titulos = [item['titulo'] for item in resposta.data['dados']]
        self.assertNotIn('Privada L3', titulos)
        self.assertIn('Do admin', titulos)

        url_lida_outro = reverse('notificacoes:notificacao-lida', kwargs={'pk': notif_outro.pk})
        resposta = self.client.patch(url_lida_outro)
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_filtro_lida_invalido_e_ignorado(self):
        disparar_inbox(self.usuario, titulo='A')
        disparar_inbox(self.usuario, titulo='B')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url_lista, {'lida': 'invalido'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 2)

    def test_filtro_lida_e_tipo(self):
        n1 = disparar_inbox(self.usuario, tipo='tipo.a', titulo='N1')
        n2 = disparar_inbox(self.usuario, tipo='tipo.b', titulo='N2')
        n1.business.marcar_lida()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        resposta = self.client.get(self.url_lista, {'lida': 'true'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['id'], n1.pk)

        resposta = self.client.get(self.url_lista, {'lida': 'false'})
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['id'], n2.pk)

        resposta = self.client.get(self.url_lista, {'tipo': 'tipo.b'})
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['id'], n2.pk)

    def test_contador_nao_lidas(self):
        disparar_inbox(self.usuario)
        n2 = disparar_inbox(self.usuario, tipo='outro.tipo')
        n2.business.marcar_lida()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url_contador)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['quantidade'], 1)

    def test_marcar_uma_lida_idempotente(self):
        notif = disparar_inbox(self.usuario)
        url_lida = reverse('notificacoes:notificacao-lida', kwargs={'pk': notif.pk})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.patch(url_lida)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

        notif.refresh_from_db()
        self.assertIsNotNone(notif.lida_em)
        primeira_lida_em = notif.lida_em

        resposta = self.client.patch(url_lida)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertEqual(notif.lida_em, primeira_lida_em)

    def test_marcar_todas_lidas(self):
        disparar_inbox(self.usuario, titulo='A')
        disparar_inbox(self.usuario, titulo='B')
        notif_outro = disparar_inbox(self.outro, titulo='Outro')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.patch(self.url_marcar_todas)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['atualizadas'], 2)

        self.assertEqual(
            Notificacao.objects.filter(destinatario=self.usuario, lida_em__isnull=True).count(),
            0,
        )
        notif_outro.refresh_from_db()
        self.assertIsNone(notif_outro.lida_em)

    def test_lista_paginacao_count_e_dados(self):
        for i in range(3):
            disparar_inbox(self.usuario, titulo=f'N{i}', tipo=f't.{i}')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        resposta = self.client.get(self.url_lista, {'paginacao': 2})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn('count', resposta.data)
        self.assertIn('dados', resposta.data)
        self.assertEqual(resposta.data['count'], 3)
        self.assertEqual(len(resposta.data['dados']), 2)
