from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from Academico.aluno_cursos.models import AlunoCurso
from Academico.cursos.models import Curso
from Organizacional.funcoes.choices import CategoriaFuncao
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.servidores.models import Servidor
from Transporte.entradas_sem_ticket.models import EntradaSemTicket
from Transporte.permissoes.models import (
    PermissaoFuncaoTransporte,
    PermissaoUsuarioTransporte,
)
from Transporte.strikes.models import Strike
from Transporte.tests_utils import criar_aluno, criar_rota_e_execucao, criar_usuario, obter_token
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class RelatorioAlunosApiTestCase(APITestCase):

    def setUp(self):
        self.admin = criar_usuario('10000000001', nome='Admin', admin=True)
        self.aluno_presente = criar_aluno('20000000001', nome='Aluno Presente')
        self.aluno_ausente = criar_aluno('20000000002', nome='Aluno Ausente')
        self.aluno_sem_ticket = criar_aluno('20000000003', nome='Aluno Sem Ticket')
        self.aluno_sem_reserva = criar_aluno('20000000004', nome='Aluno Sem Reserva')
        self.aluno_espera = criar_aluno('20000000005', nome='Aluno Espera Contemplado')

        self.hoje = timezone.localdate()
        self.data_inicio = (self.hoje - timedelta(days=7)).isoformat()
        self.data_fim = self.hoje.isoformat()

        self.rota, self.execucao = criar_rota_e_execucao(vagas=5, dias_ate_execucao=0)
        self.execucao.data_execucao = self.hoje
        self.execucao.save(update_fields=['data_execucao'])

        instante_aberto = timezone.localtime(self.execucao.data_hora_saida).replace(
            hour=1, minute=0, second=0, microsecond=0,
        )
        self.patcher = patch('Transporte.tickets.rules.now', return_value=instante_aberto)
        self.patcher.start()

        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_presente,
            status=StatusTicket.EMBARCADO,
            embarcado_em=timezone.now(),
        )
        ticket_ausente = Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_ausente,
            status=StatusTicket.AUSENTE,
            ausente_em=timezone.now(),
        )
        Strike.objects.create(ticket=ticket_ausente)
        EntradaSemTicket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_sem_ticket,
            cpf=self.aluno_sem_ticket.usuario.cpf,
            data_hora_entrada=timezone.now(),
        )
        Ticket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_espera,
            status=StatusTicket.CONTEMPLADO,
        )
        EntradaSemTicket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_espera,
            cpf=self.aluno_espera.usuario.cpf,
            data_hora_entrada=timezone.now(),
        )
        EntradaSemTicket.objects.create(
            execucao_rota=self.execucao,
            aluno=self.aluno_ausente,
            cpf=self.aluno_ausente.usuario.cpf,
            data_hora_entrada=timezone.now(),
        )

        curso = Curso.objects.create(nome='TADS Mód. V', codigo_curso='TADS')
        AlunoCurso.objects.create(
            aluno=self.aluno_presente,
            curso=curso,
            matricula='2023114TADS',
        )

    def tearDown(self):
        self.patcher.stop()

    def _url_dashboard(self):
        return reverse('transporte:relatorio-alunos-dashboard')

    def _url_detalhes(self):
        return reverse('transporte:relatorio-alunos-detalhes')

    def _criar_gestor(
        self,
        cpf,
        categoria,
        papel_funcao,
        visualizar_relatorio_alunos=None,
    ):
        usuario = criar_usuario(cpf, nome=papel_funcao)
        cargo = Cargo.objects.create(nome=f'Cargo {cpf}')
        Servidor.objects.create(
            usuario=usuario,
            cargo=cargo,
            categoria=1,
            ativo=True,
        )
        funcao = Funcao.objects.create(
            papel_funcao=papel_funcao,
            categoria=categoria,
            descricao=papel_funcao,
        )
        if visualizar_relatorio_alunos is not None:
            PermissaoFuncaoTransporte().business.criar_permissao(
                funcao.pk,
                visualizar_relatorio_alunos=visualizar_relatorio_alunos,
            )
        setor = Setor.objects.create(
            nome=f'Setor {cpf}',
            sigla=f'S{cpf[-8:]}',
        )
        SetorVinculo.objects.create(
            usuario=usuario,
            setor=setor,
            funcao=funcao,
        )
        return usuario, funcao

    def test_l3_obtem_dashboard_com_resumo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        dados = resposta.data['dados']
        self.assertEqual(dados['resumo']['presentes'], 1)
        self.assertEqual(dados['resumo']['ausentes'], 1)
        self.assertEqual(dados['resumo']['sem_ticket'], 3)
        self.assertTrue(len(dados['por_horario']) >= 1)
        self.assertEqual(dados['por_horario'][0]['sem_ticket'], 3)

    def test_migration_concede_relatorio_a_todas_as_funcoes_gestoras(self):
        categorias_gestoras = (
            CategoriaFuncao.DIRETOR,
            CategoriaFuncao.COORDENADOR,
            CategoriaFuncao.CHEFE,
        )
        for categoria in categorias_gestoras:
            with self.subTest(categoria=categoria):
                funcoes = Funcao.objects.filter(categoria=categoria)
                self.assertTrue(funcoes.exists())
                self.assertFalse(
                    funcoes.exclude(
                        permissao_transporte__visualizar_relatorio_alunos=True,
                    ).exists(),
                )

        self.assertTrue(
            Funcao.objects.filter(
                papel_funcao='Chefe de Gabinete da Diretoria Geral',
                permissao_transporte__visualizar_relatorio_alunos=True,
            ).exists(),
        )
        self.assertFalse(
            PermissaoFuncaoTransporte.objects.filter(
                visualizar_relatorio_alunos=True,
                conferir=True,
            ).exists(),
        )

    def test_l1_recebe_403_no_dashboard(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {obter_token(self.aluno_presente.usuario)}',
        )
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_autenticado_recebe_401_no_dashboard(self):
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funcoes_gestoras_acessam_dashboard_e_detalhes_sem_receber_conferencia(self):
        perfis = (
            (CategoriaFuncao.DIRETOR, 'Diretor Geral'),
            (CategoriaFuncao.COORDENADOR, 'Coordenador de Curso'),
            (CategoriaFuncao.CHEFE, 'Chefe de Departamento'),
            (CategoriaFuncao.CHEFE, 'Chefe de Gabinete'),
        )

        for indice, (categoria, papel_funcao) in enumerate(perfis, start=1):
            with self.subTest(papel_funcao=papel_funcao):
                usuario, _ = self._criar_gestor(
                    f'3000000000{indice}',
                    categoria,
                    papel_funcao,
                )
                self.assertFalse(
                    PermissaoFuncaoTransporte.objects.filter(
                        funcao__papel_funcao=papel_funcao,
                    ).exists(),
                )
                transporte = usuario.permissoes['transporte']
                self.assertTrue(transporte['visualizar_relatorio_alunos'])
                self.assertFalse(transporte['conferir'])

                self.client.credentials(
                    HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}',
                )
                resposta_dashboard = self.client.get(self._url_dashboard(), {
                    'data_inicio': self.data_inicio,
                    'data_fim': self.data_fim,
                })
                resposta_detalhes = self.client.get(self._url_detalhes(), {
                    'data_inicio': self.data_inicio,
                    'data_fim': self.data_fim,
                    'categoria': 'presentes',
                })

                self.assertEqual(resposta_dashboard.status_code, status.HTTP_200_OK)
                self.assertEqual(resposta_detalhes.status_code, status.HTTP_200_OK)

    def test_funcao_gestora_acessa_mesmo_com_capacidade_persistida_falsa(self):
        usuario, funcao = self._criar_gestor(
            '30000000005',
            CategoriaFuncao.COORDENADOR,
            'Coordenador sem relatório',
            visualizar_relatorio_alunos=False,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertFalse(funcao.permissao_transporte.visualizar_relatorio_alunos)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_funcao_inativa_nao_concede_acesso_ao_relatorio(self):
        usuario, funcao = self._criar_gestor(
            '30000000006',
            CategoriaFuncao.DIRETOR,
            'Diretor inativo',
        )
        funcao.ativo = False
        funcao.save(update_fields=['ativo'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_setor_inativo_nao_concede_acesso_ao_relatorio(self):
        usuario, _ = self._criar_gestor(
            '30000000008',
            CategoriaFuncao.COORDENADOR,
            'Coordenador com setor inativo',
        )
        vinculo = SetorVinculo.objects.get(usuario=usuario)
        vinculo.setor.ativo = False
        vinculo.setor.save(update_fields=['ativo'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_perfil_colaborador_inativo_nao_concede_acesso_ao_relatorio(self):
        usuario, _ = self._criar_gestor(
            '30000000009',
            CategoriaFuncao.CHEFE,
            'Chefe com perfil inativo',
        )
        usuario.servidor.ativo = False
        usuario.servidor.save(update_fields=['ativo'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissao_direta_do_usuario_concede_acesso_ao_relatorio(self):
        usuario, _ = self._criar_gestor(
            '30000000007',
            CategoriaFuncao.COORDENADOR,
            'Coordenador com permissão individual',
            visualizar_relatorio_alunos=False,
        )
        SetorVinculo.objects.filter(usuario=usuario).delete()
        PermissaoUsuarioTransporte().business.criar_permissao(
            usuario.pk,
            visualizar_relatorio_alunos=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_intervalo_invalido_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': self.data_fim,
            'data_fim': self.data_inicio,
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_data_malformada_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_dashboard(), {
            'data_inicio': 'data-invalida',
            'data_fim': self.data_fim,
        })

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhes_presentes_com_busca(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'presentes',
            'busca': 'Presente',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['categoria'], 'presentes')
        self.assertEqual(resposta.data['count'], 1)
        aluno = resposta.data['dados'][0]
        self.assertEqual(aluno['nome'], 'Aluno Presente')
        self.assertEqual(aluno['turma'], 'TADS Mód. V')
        self.assertEqual(aluno['matricula'], '2023114TADS')
        self.assertFalse(aluno['pcd'])
        self.assertIsNotNone(aluno['primeiro_uso'])
        self.assertIsNotNone(aluno['ultimo_uso'])
        self.assertEqual(aluno['status'], 'Presente')
        self.assertEqual(aluno['bloqueios'], 0)

    def test_detalhes_ausencias_separa_bloqueios_historicos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'ausencias',
            'busca': 'Ausente',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['categoria'], 'ausencias')
        self.assertEqual(resposta.data['count'], 1)
        aluno = resposta.data['dados'][0]
        self.assertEqual(aluno['nome'], 'Aluno Ausente')
        self.assertGreaterEqual(aluno['ausencias'], 1)
        self.assertEqual(aluno['bloqueios'], 0)
        self.assertNotEqual(aluno['bloqueios'], aluno['ausencias'])
        self.assertEqual(aluno['status'], 'Ausente')

    def test_detalhes_sem_ticket(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'sem_ticket',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        nomes = [item['nome'] for item in resposta.data['dados']]
        self.assertEqual(resposta.data['count'], 3)
        self.assertIn('Aluno Sem Ticket', nomes)
        self.assertIn('Aluno Espera Contemplado', nomes)
        self.assertIn('Aluno Ausente', nomes)
        self.assertNotIn('Aluno Sem Reserva', nomes)
        self.assertNotIn('Aluno Presente', nomes)

    def test_detalhes_categoria_invalida_retorna_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'invalida',
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhes_paginacao(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'sem_ticket',
            'paginacao': 1,
            'page': 1,
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data['dados']), 1)

    def test_detalhes_ignora_paginacao_invalida(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'sem_ticket',
            'page': 'invalida',
            'paginacao': 'invalida',
        })

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['count'], 3)
        self.assertEqual(len(resposta.data['dados']), 3)

    def test_detalhes_exibe_bloqueios_historicos_persistidos(self):
        self.aluno_ausente.quantidade_bloqueios = 1
        self.aluno_ausente.faltas = 0
        self.aluno_ausente.is_bloqueado = False
        self.aluno_ausente.save(update_fields=[
            'quantidade_bloqueios',
            'faltas',
            'is_bloqueado',
        ])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        resposta = self.client.get(self._url_detalhes(), {
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'categoria': 'ausencias',
            'busca': 'Ausente',
        })
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        aluno = resposta.data['dados'][0]
        self.assertEqual(aluno['bloqueios'], 1)
        self.assertEqual(aluno['status'], 'Ausente')
