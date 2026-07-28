import datetime

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.emprestimos.models import Emprestimo
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala, SalaSetor
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def obter_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


def criar_usuario(cpf, nome='Usuário Teste'):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


def conceder_capacidade_operar(usuario):
    funcao = Funcao.objects.create(papel_funcao=f'OP_{usuario.cpf}', descricao='Operador')
    setor = Setor.objects.create(sigla=f'O{usuario.cpf[-3:]}', nome='Setor Operador')
    PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao.pk, operar=True)
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    return usuario


class EmprestimosViewsTest(APITestCase):

    def setUp(self):
        self.solicitante = criar_usuario('23232323232', nome='Solicitante API')
        self.usuario_l1 = self.solicitante
        self.operador = conceder_capacidade_operar(criar_usuario('24242424242', nome='Operador API'))
        self.token_l1 = obter_tokens(self.usuario_l1)
        self.token_operador = obter_tokens(self.operador)

        self.bloco = Bloco.objects.create(nome='Bloco API Emp')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala API Emp')
        setor = Setor.objects.create(sigla='SAP', nome='Setor API')
        SalaSetor.objects.create(sala=self.sala, setor=setor)
        SetorVinculo.objects.create(usuario=self.solicitante, setor=setor, funcao=None)
        self.chave = Recurso.objects.create(
            codigo='CHV-API',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )
        self.url_lista = reverse('infraestrutura:emprestimos-list')
        self.url_solicitantes = reverse('infraestrutura:emprestimos-solicitantes-elegiveis')

    def test_l1_nao_pode_listar_solicitantes_elegiveis(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_lista_solicitantes_elegiveis_por_recurso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.solicitante.pk, ids)

    def test_solicitantes_elegiveis_exclui_usuario_sem_acesso(self):
        sem_acesso = criar_usuario('25252525252', nome='Sem Acesso')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertNotIn(sem_acesso.pk, ids)

    def test_operador_lista_solicitantes_elegiveis_para_varios_recursos(self):
        midia = Recurso.objects.create(
            codigo='MID-API',
            tipo=TipoRecurso.MIDIA,
        )
        autorizador = conceder_capacidade_operar(criar_usuario('26262626262', nome='Autorizador API'))
        funcao_aut = Funcao.objects.create(papel_funcao='AUT_API', descricao='Aut API')
        setor_aut = Setor.objects.create(sigla='AUT', nome='Setor Aut API')
        PermissaoFuncaoInfraestrutura().business.criar_permissao(funcao_id=funcao_aut.pk, autorizar=True)
        SetorVinculo.objects.create(usuario=autorizador, setor=setor_aut, funcao=funcao_aut)

        from Infraestrutura.autorizacoes.models import Autorizacao

        Autorizacao().business.conceder_autorizacao(
            beneficiario_id=self.solicitante.pk,
            concedente=autorizador,
            recurso_id=midia.pk,
            data_inicio=datetime.date.today(),
        )

        apenas_chave = criar_usuario('27272727272', nome='Apenas Chave API')
        setor = Setor.objects.get(sigla='SAP')
        SetorVinculo.objects.create(usuario=apenas_chave, setor=setor, funcao=None)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(
            self.url_solicitantes,
            {'recurso_ids': f'{self.chave.pk},{midia.pk}'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.solicitante.pk, ids)
        self.assertNotIn(apenas_chave.pk, ids)

    def test_l1_nao_pode_realizar_emprestimo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
        })
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_realiza_devolve_e_lista(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')

        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
            'observacao': 'Retirada teste',
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        emprestimo_id = resposta.data['dados']['id']
        item_id = resposta.data['dados']['itens'][0]['id']
        self.assertTrue(resposta.data['dados']['ativo'])

        url_devolver = reverse('infraestrutura:emprestimo-devolver', kwargs={'pk': emprestimo_id})
        resposta = self.client.post(url_devolver, {'item_ids': [item_id]})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(resposta.data['dados']['ativo'])

        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_l1_ve_apenas_emprestimos_ativos_proprios(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
        })
        emprestimo_id = resposta.data['dados']['id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(emprestimo_id, ids)

        url_devolver = reverse('infraestrutura:emprestimo-devolver', kwargs={'pk': emprestimo_id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        item_id = Emprestimo.objects.get(pk=emprestimo_id).itens.first().pk
        self.client.post(url_devolver, {'item_ids': [item_id]})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertNotIn(emprestimo_id, ids)


class EmprestimoUsuarioColetivoViewsTest(APITestCase):

    def setUp(self):
        self.solicitante = criar_usuario('28282828282', nome='Professor Jão')
        self.guardinha = criar_usuario('29292929292', nome='Seu Zé')
        self.conta_coletiva = criar_usuario('30303030303', nome='Guarita')
        self.conta_coletiva.usuario_coletivo = True
        self.conta_coletiva.save()
        conceder_capacidade_operar(self.conta_coletiva)

        setor = Setor.objects.create(sigla='GUA', nome='Guarita')
        self.conta_coletiva.setores_coletivo.add(setor)
        SetorVinculo.objects.create(usuario=self.guardinha, setor=setor, funcao=None)

        self.bloco = Bloco.objects.create(nome='Bloco Coletivo')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Lab 1')
        SalaSetor.objects.create(sala=self.sala, setor=setor)
        SetorVinculo.objects.create(usuario=self.solicitante, setor=setor, funcao=None)
        self.chave = Recurso.objects.create(
            codigo='CHV-COL',
            tipo=TipoRecurso.CHAVE,
            sala=self.sala,
        )

        self.token_coletivo = obter_tokens(self.conta_coletiva)
        self.token_guardinha = obter_tokens(self.guardinha)
        self.url_lista = reverse('infraestrutura:emprestimos-list')
        self.url_responsaveis = reverse('infraestrutura:emprestimos-responsaveis-elegiveis')

    def test_conta_coletiva_lista_responsaveis_do_pool(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.get(self.url_responsaveis)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.guardinha.pk, ids)
        self.assertNotIn(self.conta_coletiva.pk, ids)

    def test_conta_nao_coletiva_lista_apenas_si_mesma(self):
        conceder_capacidade_operar(self.guardinha)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_guardinha}')
        resposta = self.client.get(self.url_responsaveis)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)
        self.assertEqual(resposta.data['dados'][0]['id'], self.guardinha.pk)

    def test_conta_coletiva_exige_responsavel_id(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conta_coletiva_realiza_emprestimo_com_responsavel(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
            'responsavel_id': self.guardinha.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data['dados']['responsavel']['id'], self.guardinha.pk)
        self.assertEqual(resposta.data['dados']['responsavel']['nome'], 'Seu Zé')

    def test_conta_coletiva_rejeita_responsavel_fora_do_pool(self):
        fora = criar_usuario('31313131313', nome='Fora do Pool')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
            'responsavel_id': fora.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_normal_rejeita_responsavel_id_alheio(self):
        conceder_capacidade_operar(self.guardinha)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_guardinha}')
        resposta = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
            'responsavel_id': self.solicitante.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conta_coletiva_troca_titular_exige_e_grava_responsavel(self):
        novo_solicitante = criar_usuario('32323232324', nome='Novo Titular')
        SetorVinculo.objects.create(
            usuario=novo_solicitante,
            setor=Setor.objects.get(sigla='GUA'),
            funcao=None,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        criado = self.client.post(self.url_lista, {
            'solicitante_id': self.solicitante.pk,
            'recurso_ids': [self.chave.pk],
            'responsavel_id': self.guardinha.pk,
        })
        emprestimo_id = criado.data['dados']['id']
        url_trocar = reverse('infraestrutura:emprestimo-trocar-titular', kwargs={'pk': emprestimo_id})

        sem_responsavel = self.client.post(url_trocar, {
            'novo_solicitante_id': novo_solicitante.pk,
        })
        self.assertEqual(sem_responsavel.status_code, status.HTTP_400_BAD_REQUEST)

        com_responsavel = self.client.post(url_trocar, {
            'novo_solicitante_id': novo_solicitante.pk,
            'responsavel_id': self.guardinha.pk,
        })
        self.assertEqual(com_responsavel.status_code, status.HTTP_201_CREATED)
        self.assertEqual(com_responsavel.data['dados']['solicitante']['id'], novo_solicitante.pk)
        self.assertEqual(com_responsavel.data['dados']['responsavel']['id'], self.guardinha.pk)
