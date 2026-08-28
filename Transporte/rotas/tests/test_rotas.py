from datetime import time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor
from Transporte.percursos.models import Percurso
from Transporte.rotas.choices import DiaSemana
from Transporte.rotas.models import Rota


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin TI'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


def criar_usuario_comum(cpf='00000000002', nome='Comum'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def criar_servidor(cpf='00000000003', nome='Servidor'):
    usuario = Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)
    cargo = Cargo.objects.create(nome=f'Cargo {cpf}')
    Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1, ativo=True)
    return usuario


def criar_percurso(apelido='Rota R.SÃ', descricao='IFPI – Posto R.Sã – FM', ativo=True):
    return Percurso.objects.create(apelido=apelido, descricao=descricao, ativo=ativo)


def criar_rota(percurso, horario_saida=None, dia_semana=DiaSemana.SEGUNDA, quantidade_vagas=40):
    return Rota.objects.create(
        percurso=percurso,
        horario_saida=horario_saida or time(7, 0),
        dia_semana=dia_semana,
        quantidade_vagas=quantidade_vagas,
    )


class RotaBusinessTestCase(APITestCase):

    def setUp(self):
        self.percurso = criar_percurso()

    def test_criar_rota_sucesso(self):
        rota = Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 30),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        self.assertEqual(rota.percurso_id, self.percurso.pk)
        self.assertEqual(rota.quantidade_vagas, 40)
        self.assertTrue(rota.ativo)

    def test_criar_rota_percurso_inativo(self):
        percurso = criar_percurso(apelido='Inativo', ativo=False)
        with self.assertRaises(BusinessRuleException):
            Rota().business.criar_rota(
                percurso_id=percurso.pk,
                horario_saida=time(7, 0),
                dia_semana=DiaSemana.SEGUNDA,
                quantidade_vagas=20,
            )

    def test_criar_rota_duplicada(self):
        Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        with self.assertRaises(BusinessRuleException) as ctx:
            Rota().business.criar_rota(
                percurso_id=self.percurso.pk,
                horario_saida=time(7, 0),
                dia_semana=DiaSemana.SEGUNDA,
                quantidade_vagas=10,
            )
        self.assertIn('Já existe uma rota', str(ctx.exception))

    def test_criar_rota_vagas_invalidas(self):
        with self.assertRaises(BusinessRuleException):
            Rota().business.criar_rota(
                percurso_id=self.percurso.pk,
                horario_saida=time(7, 0),
                dia_semana=DiaSemana.SEGUNDA,
                quantidade_vagas=0,
            )

    def test_atualizar_dados_sucesso(self):
        rota = Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        rota.business.atualizar_dados({'quantidade_vagas': 30})
        rota.refresh_from_db()
        self.assertEqual(rota.quantidade_vagas, 30)

    def test_desativar_e_reativar(self):
        rota = Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        rota.business.desativar()
        rota.refresh_from_db()
        self.assertFalse(rota.ativo)
        rota.business.reativar()
        rota.refresh_from_db()
        self.assertTrue(rota.ativo)

    def test_desativar_ja_inativa(self):
        rota = Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        rota.business.desativar()
        with self.assertRaises(BusinessRuleException):
            rota.business.desativar()

    def test_reativar_com_percurso_inativo(self):
        rota = Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        rota.business.desativar()
        self.percurso.ativo = False
        self.percurso.save(update_fields=['ativo'])
        with self.assertRaises(BusinessRuleException):
            rota.business.reativar()

    def test_nao_desativa_percurso_com_rota_ativa(self):
        Rota().business.criar_rota(
            percurso_id=self.percurso.pk,
            horario_saida=time(7, 0),
            dia_semana=DiaSemana.SEGUNDA,
            quantidade_vagas=40,
        )
        with self.assertRaises(BusinessRuleException) as ctx:
            self.percurso.business.desativar()
        self.assertIn('rotas ativas', str(ctx.exception))


class RotasAPITestCase(APITestCase):

    def setUp(self):
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.percurso = criar_percurso()
        self.rota = criar_rota(self.percurso)
        self.url_list = reverse('transporte:rotas')

    def test_listar_rotas(self):
        resposta = self.client.get(self.url_list)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listar_filtrar_ativo_e_percurso(self):
        resposta = self.client.get(self.url_list, {
            'ativo': 'true',
            'percurso_id': str(self.percurso.pk),
            'dia_semana': DiaSemana.SEGUNDA,
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_listar_busca_por_apelido_do_percurso(self):
        outro = criar_percurso(apelido='Rota Pontões', descricao='Outro')
        criar_rota(outro, horario_saida=time(8, 0))
        resposta = self.client.get(self.url_list, {'busca': 'Pontões'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        apelidos = [item['percurso']['apelido'] for item in resposta.data['dados']]
        self.assertEqual(apelidos, ['Rota Pontões'])

    def test_criar_rota(self):
        payload = {
            'percurso_id': self.percurso.pk,
            'horario_saida': '12:00:00',
            'dia_semana': DiaSemana.TERCA,
            'quantidade_vagas': 35,
        }
        resposta = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data['dados']['quantidade_vagas'], 35)

    def test_criar_rota_duplicada(self):
        payload = {
            'percurso_id': self.percurso.pk,
            'horario_saida': '07:00:00',
            'dia_semana': DiaSemana.SEGUNDA,
            'quantidade_vagas': 10,
        }
        resposta = self.client.post(self.url_list, payload, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhar_rota(self):
        url = reverse('transporte:rota-detalhe', kwargs={'pk': self.rota.pk})
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['dia_semana'], DiaSemana.SEGUNDA)

    def test_atualizar_rota(self):
        url = reverse('transporte:rota-detalhe', kwargs={'pk': self.rota.pk})
        resposta = self.client.patch(url, {'quantidade_vagas': 25}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.rota.refresh_from_db()
        self.assertEqual(self.rota.quantidade_vagas, 25)

    def test_desativar_rota(self):
        url = reverse('transporte:rota-desativar', kwargs={'pk': self.rota.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.rota.refresh_from_db()
        self.assertFalse(self.rota.ativo)

    def test_reativar_rota(self):
        self.rota.business.desativar()
        url = reverse('transporte:rota-reativar', kwargs={'pk': self.rota.pk})
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.rota.refresh_from_db()
        self.assertTrue(self.rota.ativo)

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        resposta = self.client.get(self.url_list)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_l1_nao_pode_listar_nem_criar(self):
        usuario = criar_usuario_comum()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        self.assertEqual(self.client.get(self.url_list).status_code, status.HTTP_403_FORBIDDEN)
        resposta = self.client.post(self.url_list, {
            'percurso_id': self.percurso.pk,
            'horario_saida': '09:00:00',
            'dia_semana': DiaSemana.QUARTA,
            'quantidade_vagas': 10,
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_l2_nao_pode_listar_nem_criar(self):
        servidor = criar_servidor()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(servidor)}')
        self.assertEqual(self.client.get(self.url_list).status_code, status.HTTP_403_FORBIDDEN)
        resposta = self.client.post(self.url_list, {
            'percurso_id': self.percurso.pk,
            'horario_saida': '09:00:00',
            'dia_semana': DiaSemana.QUARTA,
            'quantidade_vagas': 10,
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
