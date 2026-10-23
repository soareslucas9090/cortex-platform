import datetime

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Identidade.usuarios.models import TipoContaColetiva, Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.emprestimos.models import Emprestimo, ItemEmprestimo
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura, PermissaoUsuarioInfraestrutura
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
        self.chave = Recurso.objects.create(codigo='CHV-API', tipo=TipoRecurso.CHAVE, sala=self.sala)
        self.url_lista = reverse('infraestrutura:emprestimos-list')
        self.url_solicitantes = reverse('infraestrutura:emprestimos-solicitantes-elegiveis')
        self.outro_solicitante = criar_usuario('33333333333', nome='Outro Solicitante')
        SetorVinculo.objects.create(usuario=self.outro_solicitante, setor=setor, funcao=None)

    def test_l1_nao_lista_elegiveis_sem_emprestimo_aberto_proprio(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_lista_solicitantes_elegiveis_por_recurso(self):
        self.solicitante.foto = 'https://sistema-externo.example/fotos/solicitante.jpg'
        self.solicitante.foto_secundaria = f'Cortex/usuarios/fotos/{self.solicitante.pk}/avatar.jpg'
        self.solicitante.save(update_fields=['foto', 'foto_secundaria'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.solicitante.pk, ids)
        item = next(item for item in resposta.data['dados'] if item['id'] == self.solicitante.pk)
        url_foto_secundaria = reverse('identidade:usuario-foto-secundaria', kwargs={'pk': self.solicitante.pk})
        self.assertEqual(item['foto'], self.solicitante.foto)
        self.assertEqual(item['foto_secundaria'], f'http://testserver{url_foto_secundaria}?v=avatar')

    def test_solicitantes_elegiveis_exclui_usuario_sem_acesso(self):
        sem_acesso = criar_usuario('25252525252', nome='Sem Acesso')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(self.url_solicitantes, {'recurso_id': self.chave.pk})
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertNotIn(sem_acesso.pk, ids)

    def test_operador_lista_solicitantes_elegiveis_para_varios_recursos(self):
        midia = Recurso.objects.create(codigo='MID-API', tipo=TipoRecurso.MIDIA)
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
        resposta = self.client.get(self.url_solicitantes, {'recurso_ids': f'{self.chave.pk},{midia.pk}'})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(self.solicitante.pk, ids)
        self.assertNotIn(apenas_chave.pk, ids)

    def test_l1_nao_pode_realizar_emprestimo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.post(
            self.url_lista, {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk]}
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_realiza_devolve_e_lista(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')

        resposta = self.client.post(
            self.url_lista,
            {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk], 'observacao': 'Retirada teste'},
        )
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

    def test_l1_ativo_true_lista_somente_emprestimos_proprios_ativos(self):
        concluido_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(concluido_id)
        ativo_id = self._criar_emprestimo_ativo()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista, {'ativo': 'true'})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(ativo_id, ids)
        self.assertNotIn(concluido_id, ids)

    def test_l1_ativo_false_lista_somente_emprestimos_proprios_concluidos(self):
        concluido_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(concluido_id)
        ativo_id = self._criar_emprestimo_ativo()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista, {'ativo': 'false'})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(concluido_id, ids)
        self.assertNotIn(ativo_id, ids)

    def test_l1_sem_ativo_lista_emprestimos_proprios_ativos_e_concluidos(self):
        concluido_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(concluido_id)
        ativo_id = self._criar_emprestimo_ativo()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertIn(ativo_id, ids)
        self.assertIn(concluido_id, ids)

    def test_l1_nao_lista_emprestimo_de_outro_solicitante(self):
        emprestimo_id = self._criar_emprestimo_ativo(solicitante=self.outro_solicitante)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(self.url_lista)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resposta.data['dados']]
        self.assertNotIn(emprestimo_id, ids)

    def test_l1_paginacao_e_count_respeitam_filtro_ativo(self):
        concluido_um_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(concluido_um_id)
        concluido_dois_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(concluido_dois_id)
        ativo_id = self._criar_emprestimo_ativo()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta_concluidos = self.client.get(self.url_lista, {'ativo': 'false', 'paginacao': 1})
        resposta_ativos = self.client.get(self.url_lista, {'ativo': 'true', 'paginacao': 1})

        self.assertEqual(resposta_concluidos.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_concluidos.data['count'], 2)
        self.assertEqual(len(resposta_concluidos.data['dados']), 1)
        self.assertIn(resposta_concluidos.data['dados'][0]['id'], {concluido_um_id, concluido_dois_id})
        self.assertEqual(resposta_ativos.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_ativos.data['count'], 1)
        self.assertEqual(resposta_ativos.data['dados'][0]['id'], ativo_id)

    def _criar_emprestimo_ativo(self, solicitante=None):
        solicitante = solicitante or self.solicitante
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.post(self.url_lista, {'solicitante_id': solicitante.pk, 'recurso_ids': [self.chave.pk]})
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        return resposta.data['dados']['id']

    def _encerrar_emprestimo(self, emprestimo_id):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        item_id = Emprestimo.objects.get(pk=emprestimo_id).itens.first().pk
        url_devolver = reverse('infraestrutura:emprestimo-devolver', kwargs={'pk': emprestimo_id})
        resposta = self.client.post(url_devolver, {'item_ids': [item_id]})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_operador_filtra_atrasados_antes_da_paginacao(self):
        emprestimo_id = self._criar_emprestimo_ativo()
        Emprestimo.objects.filter(pk=emprestimo_id).update(retirada_em=timezone.now() - datetime.timedelta(hours=25))

        resposta = self.client.get(self.url_lista, {'ativo': 'true', 'atrasado': 'true', 'paginacao': 1})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['count'], 1)
        self.assertEqual(resposta.data['dados'][0]['id'], emprestimo_id)

        Emprestimo.objects.filter(pk=emprestimo_id).update(retirada_em=timezone.now())
        resposta = self.client.get(self.url_lista, {'ativo': 'true', 'atrasado': 'true', 'paginacao': 1})
        self.assertEqual(resposta.data['count'], 0)

        resposta = self.client.get(self.url_lista, {'ativo': 'true', 'atrasado': 'false', 'paginacao': 1})
        self.assertEqual(resposta.data['count'], 1)
        self.assertEqual(resposta.data['dados'][0]['id'], emprestimo_id)

    def test_l1_detalhe_emprestimo_ativo_proprio(self):
        emprestimo_id = self._criar_emprestimo_ativo()
        url_detalhe = reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_id})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], emprestimo_id)

    def test_l1_detalhe_emprestimo_encerrado_proprio_retorna_200(self):
        emprestimo_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(emprestimo_id)
        url_detalhe = reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_id})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], emprestimo_id)

    def test_l1_detalhe_emprestimo_ativo_de_outro_retorna_403(self):
        emprestimo_id = self._criar_emprestimo_ativo(solicitante=self.outro_solicitante)
        url_detalhe = reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_id})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_l1}')
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_detalhe_emprestimo_ativo_retorna_200(self):
        emprestimo_id = self._criar_emprestimo_ativo()
        url_detalhe = reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_id})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], emprestimo_id)

    def test_operador_detalhe_emprestimo_encerrado_retorna_200(self):
        emprestimo_id = self._criar_emprestimo_ativo()
        self._encerrar_emprestimo(emprestimo_id)
        url_detalhe = reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_id})

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.get(url_detalhe)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados']['id'], emprestimo_id)

    def test_operador_rejeita_recurso_ids_duplicados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.post(
            self.url_lista, {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk, self.chave.pk]}
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duplicados', str(resposta.data).lower())

    def test_operador_rejeita_segundo_emprestimo_no_mesmo_recurso(self):
        self._criar_emprestimo_ativo()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_operador}')
        resposta = self.client.post(
            self.url_lista, {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk]}
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empréstimo em aberto', str(resposta.data).lower())


class EmprestimoUsuarioColetivoViewsTest(APITestCase):

    def setUp(self):
        self.solicitante = criar_usuario('28282828282', nome='Professor Jão')
        self.guardinha = criar_usuario('29292929292', nome='Seu Zé')
        self.conta_coletiva = criar_usuario('30303030303', nome='Guarita')
        self.conta_coletiva.usuario_coletivo = True
        self.conta_coletiva.tipo_conta_coletiva = TipoContaColetiva.GUARITA
        self.conta_coletiva.save(update_fields=['usuario_coletivo', 'tipo_conta_coletiva'])
        conceder_capacidade_operar(self.conta_coletiva)

        setor = Setor.objects.create(sigla='GUA', nome='Guarita')
        self.conta_coletiva.setores_coletivo.add(setor)
        SetorVinculo.objects.create(usuario=self.guardinha, setor=setor, funcao=None)

        self.bloco = Bloco.objects.create(nome='Bloco Coletivo')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Lab 1')
        SalaSetor.objects.create(sala=self.sala, setor=setor)
        SetorVinculo.objects.create(usuario=self.solicitante, setor=setor, funcao=None)
        self.chave = Recurso.objects.create(codigo='CHV-COL', tipo=TipoRecurso.CHAVE, sala=self.sala)

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
        resposta = self.client.post(
            self.url_lista, {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk]}
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conta_coletiva_realiza_emprestimo_com_responsavel(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.post(
            self.url_lista,
            {
                'solicitante_id': self.solicitante.pk,
                'recurso_ids': [self.chave.pk],
                'responsavel_id': self.guardinha.pk,
            },
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data['dados']['responsavel']['id'], self.guardinha.pk)
        self.assertEqual(resposta.data['dados']['responsavel']['nome'], 'Seu Zé')

    def test_conta_coletiva_rejeita_responsavel_fora_do_pool(self):
        fora = criar_usuario('31313131313', nome='Fora do Pool')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        resposta = self.client.post(
            self.url_lista,
            {'solicitante_id': self.solicitante.pk, 'recurso_ids': [self.chave.pk], 'responsavel_id': fora.pk},
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_normal_rejeita_responsavel_id_alheio(self):
        conceder_capacidade_operar(self.guardinha)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_guardinha}')
        resposta = self.client.post(
            self.url_lista,
            {
                'solicitante_id': self.solicitante.pk,
                'recurso_ids': [self.chave.pk],
                'responsavel_id': self.solicitante.pk,
            },
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conta_coletiva_troca_titular_exige_e_grava_responsavel(self):
        novo_solicitante = criar_usuario('32323232324', nome='Novo Titular')
        SetorVinculo.objects.create(usuario=novo_solicitante, setor=Setor.objects.get(sigla='GUA'), funcao=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_coletivo}')
        criado = self.client.post(
            self.url_lista,
            {
                'solicitante_id': self.solicitante.pk,
                'recurso_ids': [self.chave.pk],
                'responsavel_id': self.guardinha.pk,
            },
        )
        emprestimo_id = criado.data['dados']['id']
        url_trocar = reverse('infraestrutura:emprestimo-trocar-titular', kwargs={'pk': emprestimo_id})

        sem_responsavel = self.client.post(url_trocar, {'novo_solicitante_id': novo_solicitante.pk})
        self.assertEqual(sem_responsavel.status_code, status.HTTP_400_BAD_REQUEST)

        com_responsavel = self.client.post(
            url_trocar, {'novo_solicitante_id': novo_solicitante.pk, 'responsavel_id': self.guardinha.pk}
        )
        self.assertEqual(com_responsavel.status_code, status.HTTP_201_CREATED)
        self.assertEqual(com_responsavel.data['dados']['solicitante']['id'], novo_solicitante.pk)
        self.assertEqual(com_responsavel.data['dados']['responsavel']['id'], self.guardinha.pk)


class EmprestimoOrigemContaColetivaViewsTest(APITestCase):

    def setUp(self):
        self.solicitante = criar_usuario('41000000001', nome='Solicitante Origem')
        PermissaoUsuarioInfraestrutura.objects.create(usuario=self.solicitante, retirada_irrestrita=True)
        self.responsavel = criar_usuario('41000000002', nome='Responsável Coletivo')
        self.operador = criar_usuario('41000000003', nome='Operador Comum')
        PermissaoUsuarioInfraestrutura.objects.create(usuario=self.operador, operar=True)
        self.admin = Usuario.objects.create_user(
            cpf='41000000004', password='Senha@123', nome='Administrador Origem', is_admin=True, is_staff=True
        )
        self.guarita = self._criar_conta_coletiva('41000000005', 'Guarita Origem', TipoContaColetiva.GUARITA, 'GOR')
        self.codis = self._criar_conta_coletiva('41000000006', 'CODIS Origem', TipoContaColetiva.CODIS, 'COR')

        self.tokens = {
            self.guarita.pk: obter_tokens(self.guarita),
            self.codis.pk: obter_tokens(self.codis),
            self.operador.pk: obter_tokens(self.operador),
            self.admin.pk: obter_tokens(self.admin),
            self.solicitante.pk: obter_tokens(self.solicitante),
        }
        self.bloco = Bloco.objects.create(nome='Bloco Origem')
        self.sala = Sala.objects.create(bloco=self.bloco, nome='Sala Origem')
        self.url_lista = reverse('infraestrutura:emprestimos-list')
        self._contador_recurso = 0

    def _criar_conta_coletiva(self, cpf, nome, tipo, sigla_setor):
        conta = Usuario.objects.create_user(
            cpf=cpf, password='Senha@123', nome=nome, usuario_coletivo=True, tipo_conta_coletiva=tipo
        )
        PermissaoUsuarioInfraestrutura.objects.create(usuario=conta, operar=True)
        setor = Setor.objects.create(sigla=sigla_setor, nome=nome)
        conta.setores_coletivo.add(setor)
        SetorVinculo.objects.create(usuario=self.responsavel, setor=setor, funcao=None)
        return conta

    def _criar_recurso(self, tipo=TipoRecurso.CHAVE):
        self._contador_recurso += 1
        return Recurso.objects.create(
            codigo=f'ORI-{self._contador_recurso}', tipo=tipo, sala=self.sala if tipo == TipoRecurso.CHAVE else None
        )

    def _realizar(self, conta, *, tipo=TipoRecurso.CHAVE, origem_enviada=None):
        recurso = self._criar_recurso(tipo)
        payload = {'solicitante_id': self.solicitante.pk, 'recurso_ids': [recurso.pk]}
        if conta.usuario_coletivo:
            payload['responsavel_id'] = self.responsavel.pk
        if origem_enviada is not None:
            payload['origem_conta_coletiva'] = origem_enviada
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens[conta.pk]}')
        resposta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        return Emprestimo.objects.get(pk=resposta.data['dados']['id']), recurso

    def _ids_listados(self, usuario, **filtros):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens[usuario.pk]}')
        resposta = self.client.get(self.url_lista, filtros)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        return resposta, [item['id'] for item in resposta.data['dados']]

    def test_criacao_pela_guarita_registra_origem_guarita(self):
        emprestimo, _ = self._realizar(self.guarita)

        self.assertEqual(emprestimo.origem_conta_coletiva, TipoContaColetiva.GUARITA)

    def test_criacao_pela_codis_registra_origem_codis_inclusive_para_chave(self):
        emprestimo, recurso = self._realizar(self.codis, tipo=TipoRecurso.CHAVE)

        self.assertEqual(recurso.tipo, TipoRecurso.CHAVE)
        self.assertEqual(emprestimo.origem_conta_coletiva, TipoContaColetiva.CODIS)

    def test_origem_enviada_pelo_cliente_nao_altera_origem_real(self):
        emprestimo, _ = self._realizar(self.guarita, origem_enviada=TipoContaColetiva.CODIS)

        self.assertEqual(emprestimo.origem_conta_coletiva, TipoContaColetiva.GUARITA)

    def test_contas_coletivas_listam_apenas_a_propria_origem(self):
        emprestimo_guarita, _ = self._realizar(self.guarita)
        emprestimo_codis, _ = self._realizar(self.codis)

        _, ids_guarita = self._ids_listados(self.guarita)
        _, ids_codis = self._ids_listados(self.codis)

        self.assertIn(emprestimo_guarita.pk, ids_guarita)
        self.assertNotIn(emprestimo_codis.pk, ids_guarita)
        self.assertIn(emprestimo_codis.pk, ids_codis)
        self.assertNotIn(emprestimo_guarita.pk, ids_codis)

    def test_paginacao_e_total_respeitam_origem(self):
        emprestimo_guarita_1, _ = self._realizar(self.guarita)
        emprestimo_guarita_2, _ = self._realizar(self.guarita)
        self._realizar(self.codis)

        resposta, ids = self._ids_listados(self.guarita, paginacao=1)

        self.assertEqual(resposta.data['count'], 2)
        self.assertEqual(len(ids), 1)
        self.assertIn(ids[0], {emprestimo_guarita_1.pk, emprestimo_guarita_2.pk})

    def test_filtros_ativo_atrasado_e_tipo_recurso_respeitam_origem(self):
        atrasado, _ = self._realizar(self.guarita)
        Emprestimo.objects.filter(pk=atrasado.pk).update(retirada_em=timezone.now() - datetime.timedelta(hours=25))
        midia, _ = self._realizar(self.guarita, tipo=TipoRecurso.MIDIA)
        encerrado, _ = self._realizar(self.guarita)
        item_encerrado = encerrado.itens.get()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens[self.guarita.pk]}')
        self.client.post(
            reverse('infraestrutura:emprestimo-devolver', kwargs={'pk': encerrado.pk}),
            {'item_ids': [item_encerrado.pk]},
            format='json',
        )
        self._realizar(self.codis)

        _, ids_ativos = self._ids_listados(self.guarita, ativo='true')
        _, ids_encerrados = self._ids_listados(self.guarita, ativo='false')
        _, ids_atrasados = self._ids_listados(self.guarita, atrasado='true')
        _, ids_midia = self._ids_listados(self.guarita, tipo_recurso=TipoRecurso.MIDIA)

        self.assertEqual(set(ids_ativos), {atrasado.pk, midia.pk})
        self.assertEqual(ids_encerrados, [encerrado.pk])
        self.assertEqual(ids_atrasados, [atrasado.pk])
        self.assertEqual(ids_midia, [midia.pk])

    def test_detalhe_devolucao_e_troca_nao_atravessam_origem(self):
        emprestimo_codis, _ = self._realizar(self.codis)
        item = emprestimo_codis.itens.get()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens[self.guarita.pk]}')

        resposta_detalhe = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': emprestimo_codis.pk})
        )
        resposta_devolucao = self.client.post(
            reverse('infraestrutura:emprestimo-devolver', kwargs={'pk': emprestimo_codis.pk}),
            {'item_ids': [item.pk]},
            format='json',
        )
        resposta_troca = self.client.post(
            reverse('infraestrutura:emprestimo-trocar-titular', kwargs={'pk': emprestimo_codis.pk}),
            {'novo_solicitante_id': self.solicitante.pk, 'responsavel_id': self.responsavel.pk},
            format='json',
        )

        self.assertEqual(resposta_detalhe.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resposta_devolucao.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resposta_troca.status_code, status.HTTP_403_FORBIDDEN)
        item.refresh_from_db()
        self.assertIsNone(item.devolvido_em)

    def test_operador_comum_admin_e_solicitante_preservam_visibilidade(self):
        emprestimo_guarita, _ = self._realizar(self.guarita)
        emprestimo_codis, _ = self._realizar(self.codis)

        _, ids_operador = self._ids_listados(self.operador)
        _, ids_admin = self._ids_listados(self.admin)
        _, ids_solicitante = self._ids_listados(self.solicitante)
        esperados = {emprestimo_guarita.pk, emprestimo_codis.pk}

        self.assertTrue(esperados.issubset(set(ids_operador)))
        self.assertTrue(esperados.issubset(set(ids_admin)))
        self.assertTrue(esperados.issubset(set(ids_solicitante)))

    def test_registro_legado_sem_origem_fica_oculto_das_contas_coletivas(self):
        recurso = self._criar_recurso()
        legado = Emprestimo.objects.create(
            solicitante=self.solicitante,
            responsavel=self.operador,
            retirada_em=timezone.now(),
            origem_conta_coletiva=None,
        )
        ItemEmprestimo.objects.create(emprestimo=legado, recurso=recurso)

        _, ids_guarita = self._ids_listados(self.guarita)
        _, ids_codis = self._ids_listados(self.codis)
        _, ids_admin = self._ids_listados(self.admin)
        _, ids_operador = self._ids_listados(self.operador)
        _, ids_solicitante = self._ids_listados(self.solicitante)

        self.assertNotIn(legado.pk, ids_guarita)
        self.assertNotIn(legado.pk, ids_codis)
        self.assertIn(legado.pk, ids_admin)
        self.assertIn(legado.pk, ids_operador)
        self.assertIn(legado.pk, ids_solicitante)

    def test_origem_permanece_congelada_apos_alterar_tipo_da_conta(self):
        emprestimo, _ = self._realizar(self.guarita)
        self.guarita.tipo_conta_coletiva = TipoContaColetiva.CODIS
        self.guarita.save(update_fields=['tipo_conta_coletiva'])

        emprestimo.refresh_from_db()

        self.assertEqual(emprestimo.origem_conta_coletiva, TipoContaColetiva.GUARITA)
