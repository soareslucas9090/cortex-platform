from datetime import timedelta
from types import SimpleNamespace

from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from Identidade.usuarios.models import Usuario
from Infraestrutura.blocos.models import Bloco
from Infraestrutura.emprestimos.choices import StatusSolicitacaoTrocaTitular
from Infraestrutura.emprestimos.models import (
    Emprestimo,
    ItemEmprestimo,
    SolicitacaoTrocaTitular,
)
from Infraestrutura.emprestimos.serializers import EmprestimoSerializer
from Infraestrutura.recursos.choices import TipoRecurso
from Infraestrutura.recursos.models import Recurso
from Infraestrutura.salas.models import Sala
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.choices import CategoriaServidor
from PessoasInstitucionais.servidores.models import Servidor


def criar_usuario(cpf, nome):
    return Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)


class SolicitacaoTrocaTitularTest(APITestCase):

    def setUp(self):
        self.cargo = Cargo.objects.create(nome='Técnico de laboratório', ativo=True)
        self.titular = self._criar_servidor('41000000001', 'Titular')
        self.destinatario = self._criar_servidor('41000000002', 'Destinatário')
        self.terceiro = self._criar_servidor('41000000003', 'Terceiro')
        bloco = Bloco.objects.create(nome='Bloco Trocas')
        sala = Sala.objects.create(bloco=bloco, nome='Sala Trocas')
        self.recurso = Recurso.objects.create(
            codigo='CH-TROCA-01',
            tipo=TipoRecurso.CHAVE,
            sala=sala,
        )
        self.emprestimo = Emprestimo.objects.create(
            solicitante=self.titular,
            responsavel=self.titular,
            retirada_em=timezone.now(),
            observacao='Empréstimo original',
        )
        self.item = ItemEmprestimo.objects.create(
            emprestimo=self.emprestimo,
            recurso=self.recurso,
        )
        self.url_criar = reverse(
            'infraestrutura:emprestimo-solicitacao-troca-criar',
            kwargs={'emprestimo_id': self.emprestimo.pk},
        )
        self.url_listar = reverse('infraestrutura:solicitacao-troca-list')
        self.url_emprestimos = reverse('infraestrutura:emprestimos-list')
        self.url_destinatarios = reverse(
            'infraestrutura:emprestimos-solicitantes-elegiveis',
        )

    def _criar_servidor(self, cpf, nome):
        usuario = criar_usuario(cpf, nome)
        Servidor.objects.create(
            usuario=usuario,
            cargo=self.cargo,
            categoria=CategoriaServidor.TECNICO_ADMINISTRATIVO,
        )
        return usuario

    def _criar_solicitacao(self):
        return SolicitacaoTrocaTitular().business.criar_solicitacao(
            emprestimo_id=self.emprestimo.pk,
            solicitante=self.titular,
            destinatario_id=self.destinatario.pk,
            observacao='Assuma este empréstimo',
        )

    def _criar_emprestimo(self, solicitante, codigo):
        recurso = Recurso.objects.create(
            codigo=codigo,
            tipo=TipoRecurso.CHAVE,
            sala=self.recurso.sala,
        )
        emprestimo = Emprestimo.objects.create(
            solicitante=solicitante,
            responsavel=solicitante,
            retirada_em=timezone.now(),
        )
        ItemEmprestimo.objects.create(emprestimo=emprestimo, recurso=recurso)
        return emprestimo

    def test_titular_lista_servidores_elegiveis_para_o_proprio_emprestimo(self):
        usuario_comum = criar_usuario('41000000004', 'Usuário comum')
        self.client.force_authenticate(self.titular)

        resposta = self.client.get(
            self.url_destinatarios,
            {'recurso_id': self.recurso.pk},
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in resposta.data['dados']}
        self.assertIn(self.destinatario.pk, ids)
        self.assertIn(self.terceiro.pk, ids)
        self.assertNotIn(self.titular.pk, ids)
        self.assertNotIn(usuario_comum.pk, ids)

    def test_usuario_nao_relacionado_nao_lista_destinatarios_do_emprestimo(self):
        self.client.force_authenticate(self.terceiro)

        resposta = self.client.get(
            self.url_destinatarios,
            {'recurso_id': self.recurso.pk},
        )

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_titular_cria_solicitacao_valida(self):
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.destinatario.pk,
            'observacao': 'Assuma este empréstimo',
        })

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data['dados']['status'], StatusSolicitacaoTrocaTitular.PENDENTE)
        self.assertIsInstance(resposta.data['dados']['status'], int)
        self.assertEqual(resposta.data['dados']['direcao'], 'ENVIADA')
        self.assertTrue(resposta.data['dados']['pode_cancelar'])

    def test_usuario_que_nao_e_titular_nao_cria(self):
        self.client.force_authenticate(self.terceiro)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.destinatario.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_conta_coletiva_nao_cria(self):
        self.titular.usuario_coletivo = True
        self.titular.save(update_fields=['usuario_coletivo'])
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.destinatario.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nao_permite_destinatario_igual_ao_titular(self):
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.titular.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('si mesmo', str(resposta.data))

    def test_nao_permite_emprestimo_encerrado(self):
        self.item.devolvido_em = timezone.now()
        self.item.save(update_fields=['devolvido_em'])
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.destinatario.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_destinatario_precisa_ser_servidor_ativo(self):
        usuario_comum = criar_usuario('41000000004', 'Usuário comum')
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': usuario_comum.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('servidor ativo', str(resposta.data))

    def test_business_rejeita_segunda_solicitacao_pendente(self):
        self._criar_solicitacao()
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(self.url_criar, {
            'destinatario_id': self.terceiro.pk,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pendente', str(resposta.data).lower())

    def test_constraint_impede_duas_solicitacoes_pendentes(self):
        self._criar_solicitacao()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SolicitacaoTrocaTitular.objects.create(
                    emprestimo=self.emprestimo,
                    solicitante=self.titular,
                    destinatario=self.terceiro,
                )

    def test_listagem_respeita_relacao_e_direcao(self):
        solicitacao = self._criar_solicitacao()

        self.client.force_authenticate(self.destinatario)
        recebidas = self.client.get(self.url_listar, {'direcao': 'recebidas'})
        self.assertEqual(recebidas.status_code, status.HTTP_200_OK)
        self.assertEqual(recebidas.data['dados'][0]['id'], solicitacao.pk)
        self.assertEqual(recebidas.data['dados'][0]['direcao'], 'RECEBIDA')
        self.assertTrue(recebidas.data['dados'][0]['pode_aceitar'])

        self.client.force_authenticate(self.titular)
        enviadas = self.client.get(self.url_listar, {'direcao': 'enviadas'})
        self.assertEqual(enviadas.data['dados'][0]['direcao'], 'ENVIADA')

        self.client.force_authenticate(self.terceiro)
        nao_relacionadas = self.client.get(self.url_listar)
        self.assertEqual(nao_relacionadas.data['dados'], [])

    def test_listagem_filtra_por_status_numerico(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.titular)

        pendentes = self.client.get(
            self.url_listar,
            {'status': StatusSolicitacaoTrocaTitular.PENDENTE},
        )
        aceitas = self.client.get(
            self.url_listar,
            {'status': StatusSolicitacaoTrocaTitular.ACEITA},
        )

        self.assertEqual(pendentes.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in pendentes.data['dados']], [solicitacao.pk])
        self.assertEqual(aceitas.status_code, status.HTTP_200_OK)
        self.assertEqual(aceitas.data['dados'], [])

    def test_listagem_aceita_status_textual_legado(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.titular)

        resposta = self.client.get(self.url_listar, {'status': 'PENDENTE'})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['id'] for item in resposta.data['dados']],
            [solicitacao.pk],
        )

    def test_destinatario_aceita_e_cria_um_novo_emprestimo(self):
        solicitacao = self._criar_solicitacao()
        url = reverse(
            'infraestrutura:solicitacao-troca-aceitar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        resposta = self.client.post(url, {})

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resposta.data['dados']['solicitacao']['pode_aceitar'])
        self.assertFalse(resposta.data['dados']['solicitacao']['pode_recusar'])
        self.assertFalse(resposta.data['dados']['solicitacao']['pode_cancelar'])
        solicitacao.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(solicitacao.status, StatusSolicitacaoTrocaTitular.ACEITA)
        self.assertIsNotNone(solicitacao.respondido_em)
        self.assertIsNotNone(solicitacao.novo_emprestimo_id)
        self.assertIsNotNone(self.item.devolvido_em)
        novo = solicitacao.novo_emprestimo
        self.assertEqual(novo.solicitante, self.destinatario)
        self.assertEqual(novo.responsavel, self.destinatario)
        self.assertEqual(novo.observacao, 'Assuma este empréstimo')
        self.assertEqual(list(novo.itens.values_list('recurso_id', flat=True)), [self.recurso.pk])

    def test_aceite_revalida_servidor_ativo(self):
        solicitacao = self._criar_solicitacao()
        servidor = Servidor.objects.get(usuario=self.destinatario)
        servidor.ativo = False
        servidor.save(update_fields=['ativo'])
        url = reverse(
            'infraestrutura:solicitacao-troca-aceitar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        resposta = self.client.post(url, {})
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, StatusSolicitacaoTrocaTitular.PENDENTE)

    def test_aceite_transfere_somente_itens_abertos(self):
        outro_recurso = Recurso.objects.create(
            codigo='CH-TROCA-02',
            tipo=TipoRecurso.CHAVE,
            sala=self.recurso.sala,
        )
        item_devolvido = ItemEmprestimo.objects.create(
            emprestimo=self.emprestimo,
            recurso=outro_recurso,
            devolvido_em=timezone.now(),
        )
        solicitacao = self._criar_solicitacao()
        url = reverse(
            'infraestrutura:solicitacao-troca-aceitar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_201_CREATED)
        solicitacao.refresh_from_db()
        recursos_novos = set(
            solicitacao.novo_emprestimo.itens.values_list('recurso_id', flat=True),
        )
        self.assertEqual(recursos_novos, {self.recurso.pk})
        item_devolvido.refresh_from_db()
        self.assertIsNotNone(item_devolvido.devolvido_em)

    def test_listagem_de_emprestimos_expoe_solicitacao_pendente(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.titular)
        resposta = self.client.get(self.url_emprestimos)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resposta.data['dados'][0]['solicitacao_troca']['id'],
            solicitacao.pk,
        )
        self.assertEqual(
            resposta.data['dados'][0]['solicitacao_troca']['direcao'],
            'ENVIADA',
        )

    def test_destinatario_l1_visualiza_emprestimo_recebido_na_lista_e_no_detalhe(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.destinatario)

        listagem = self.client.get(self.url_emprestimos)
        detalhe = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': self.emprestimo.pk})
        )

        self.assertEqual(listagem.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in listagem.data['dados']], [self.emprestimo.pk])
        self.assertEqual(listagem.data['dados'][0]['solicitacao_troca']['id'], solicitacao.pk)
        self.assertEqual(listagem.data['dados'][0]['solicitacao_troca']['direcao'], 'RECEBIDA')
        self.assertEqual(detalhe.status_code, status.HTTP_200_OK)
        self.assertEqual(detalhe.data['dados']['id'], self.emprestimo.pk)
        self.assertEqual(detalhe.data['dados']['solicitacao_troca']['id'], solicitacao.pk)

    def test_usuario_nao_relacionado_nao_visualiza_emprestimo_recebido(self):
        self._criar_solicitacao()
        self.client.force_authenticate(self.terceiro)

        listagem = self.client.get(self.url_emprestimos)
        listagem_filtrada = self.client.get(
            self.url_emprestimos,
            {'ativo': 'true', 'recurso_id': self.recurso.pk, 'tipo_recurso': TipoRecurso.CHAVE},
        )
        detalhe = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': self.emprestimo.pk})
        )

        self.assertEqual(listagem.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.emprestimo.pk, [item['id'] for item in listagem.data['dados']])
        self.assertNotIn(self.emprestimo.pk, [item['id'] for item in listagem_filtrada.data['dados']])
        self.assertEqual(detalhe.status_code, status.HTTP_403_FORBIDDEN)

    def test_solicitacao_pendente_e_priorizada_antes_da_paginacao(self):
        proprio = self._criar_emprestimo(self.destinatario, 'CH-TROCA-PRIORIDADE')
        Emprestimo.objects.filter(pk=self.emprestimo.pk).update(
            retirada_em=timezone.now() - timedelta(days=1)
        )
        self._criar_solicitacao()
        self.client.force_authenticate(self.destinatario)

        primeira_pagina = self.client.get(self.url_emprestimos, {'paginacao': 1, 'page': 1})
        segunda_pagina = self.client.get(self.url_emprestimos, {'paginacao': 1, 'page': 2})

        self.assertEqual(primeira_pagina.status_code, status.HTTP_200_OK)
        self.assertEqual(primeira_pagina.data['count'], 2)
        self.assertEqual(primeira_pagina.data['dados'][0]['id'], self.emprestimo.pk)
        self.assertIsNotNone(primeira_pagina.data['next'])
        self.assertIsNone(primeira_pagina.data['previous'])
        self.assertEqual(segunda_pagina.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda_pagina.data['count'], 2)
        self.assertEqual(segunda_pagina.data['dados'][0]['id'], proprio.pk)
        self.assertIsNone(segunda_pagina.data['next'])
        self.assertIsNotNone(segunda_pagina.data['previous'])

    def test_recusa_remove_visibilidade_adicional_do_destinatario(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.destinatario)
        antes = self.client.get(self.url_emprestimos)

        resposta = self.client.post(
            reverse('infraestrutura:solicitacao-troca-recusar', kwargs={'pk': solicitacao.pk}), {}
        )
        depois = self.client.get(self.url_emprestimos)
        detalhe = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': self.emprestimo.pk})
        )

        self.assertIn(self.emprestimo.pk, [item['id'] for item in antes.data['dados']])
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.emprestimo.pk, [item['id'] for item in depois.data['dados']])
        self.assertEqual(detalhe.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancelamento_remove_visibilidade_adicional_do_destinatario(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.titular)
        resposta = self.client.post(
            reverse('infraestrutura:solicitacao-troca-cancelar', kwargs={'pk': solicitacao.pk}), {}
        )

        self.client.force_authenticate(self.destinatario)
        depois = self.client.get(self.url_emprestimos)
        detalhe = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': self.emprestimo.pk})
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.emprestimo.pk, [item['id'] for item in depois.data['dados']])
        self.assertEqual(detalhe.status_code, status.HTTP_403_FORBIDDEN)

    def test_aceite_substitui_original_pelo_novo_emprestimo_na_listagem(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.destinatario)
        resposta = self.client.post(
            reverse('infraestrutura:solicitacao-troca-aceitar', kwargs={'pk': solicitacao.pk}), {}
        )
        solicitacao.refresh_from_db()

        listagem = self.client.get(self.url_emprestimos)
        ids = [item['id'] for item in listagem.data['dados']]
        detalhe_original = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': self.emprestimo.pk})
        )
        detalhe_novo = self.client.get(
            reverse('infraestrutura:emprestimo-detail', kwargs={'pk': solicitacao.novo_emprestimo_id})
        )

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertNotIn(self.emprestimo.pk, ids)
        self.assertIn(solicitacao.novo_emprestimo_id, ids)
        self.assertEqual(detalhe_original.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detalhe_novo.status_code, status.HTTP_200_OK)

    def test_serializer_de_emprestimos_nao_cresce_queries_por_registro(self):
        self._criar_solicitacao()
        contexto = {'request': SimpleNamespace(user=self.titular)}
        queryset_um = Emprestimo().business.listar_para_usuario(self.titular)
        with CaptureQueriesContext(connection) as queries_um:
            list(EmprestimoSerializer(queryset_um, many=True, context=contexto).data)

        recurso_dois = Recurso.objects.create(
            codigo='CH-TROCA-03',
            tipo=TipoRecurso.CHAVE,
            sala=self.recurso.sala,
        )
        emprestimo_dois = Emprestimo.objects.create(
            solicitante=self.titular,
            responsavel=self.titular,
            retirada_em=timezone.now(),
        )
        ItemEmprestimo.objects.create(emprestimo=emprestimo_dois, recurso=recurso_dois)
        SolicitacaoTrocaTitular().business.criar_solicitacao(
            emprestimo_id=emprestimo_dois.pk,
            solicitante=self.titular,
            destinatario_id=self.terceiro.pk,
        )
        queryset_dois = Emprestimo().business.listar_para_usuario(self.titular)
        with CaptureQueriesContext(connection) as queries_dois:
            list(EmprestimoSerializer(queryset_dois, many=True, context=contexto).data)

        self.assertEqual(len(queries_um), len(queries_dois))

    def test_aceite_repetido_e_impedido(self):
        solicitacao = self._criar_solicitacao()
        url = reverse(
            'infraestrutura:solicitacao-troca-aceitar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Emprestimo.objects.filter(solicitante=self.destinatario).count(),
            1,
        )

    def test_somente_destinatario_aceita_ou_recusa(self):
        solicitacao = self._criar_solicitacao()
        self.client.force_authenticate(self.titular)
        aceitar = reverse(
            'infraestrutura:solicitacao-troca-aceitar',
            kwargs={'pk': solicitacao.pk},
        )
        recusar = reverse(
            'infraestrutura:solicitacao-troca-recusar',
            kwargs={'pk': solicitacao.pk},
        )
        self.assertEqual(self.client.post(aceitar, {}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(recusar, {}).status_code, status.HTTP_403_FORBIDDEN)

    def test_somente_solicitante_cancela(self):
        solicitacao = self._criar_solicitacao()
        url = reverse(
            'infraestrutura:solicitacao-troca-cancelar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.titular)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_200_OK)
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, StatusSolicitacaoTrocaTitular.CANCELADA)
        self.item.refresh_from_db()
        self.assertIsNone(self.item.devolvido_em)

    def test_recusa_nao_modifica_emprestimo(self):
        solicitacao = self._criar_solicitacao()
        url = reverse(
            'infraestrutura:solicitacao-troca-recusar',
            kwargs={'pk': solicitacao.pk},
        )
        self.client.force_authenticate(self.destinatario)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_200_OK)
        solicitacao.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(solicitacao.status, StatusSolicitacaoTrocaTitular.RECUSADA)
        self.assertIsNone(self.item.devolvido_em)
