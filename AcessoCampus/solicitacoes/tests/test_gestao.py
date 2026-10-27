from datetime import time, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Academico.aluno_cursos.models import AlunoCurso
from Academico.alunos.models import Aluno
from Academico.cursos.choices import NivelEnsino
from Academico.cursos.models import Curso
from AcessoCampus.solicitacoes.choices import (
    OrigemSolicitacaoAcesso,
    StatusSolicitacaoAcesso,
    TipoSolicitacaoAcesso,
)
from AcessoCampus.solicitacoes.helpers import FUSO_FORTALEZA
from AcessoCampus.solicitacoes.models import SolicitacaoAcesso
from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


class GestaoAcessoCampusTest(APITestCase):

    def setUp(self):
        self.gestor = Usuario.objects.create_user(cpf='10000000001', password='Senha@123', nome='Gestor Ensino')
        self.alheio = Usuario.objects.create_user(cpf='10000000002', password='Senha@123', nome='Sem Papel')
        self.l3 = Usuario.objects.create_superuser(cpf='10000000003', password='Senha@123', nome='Admin')
        funcao = Funcao.objects.get(papel_funcao='Diretor(a) de Ensino')
        setor = Setor.objects.create(nome='Direção de Ensino Teste', sigla='DENST')
        SetorVinculo.objects.create(usuario=self.gestor, setor=setor, funcao=funcao, responsavel=True)

        self.curso = Curso.objects.create(
            nome='Ensino Médio',
            codigo_curso='EM-GEST',
            nivel_ensino=NivelEnsino.ENSINO_MEDIO,
        )
        self.outro_curso = Curso.objects.create(
            nome='Superior',
            codigo_curso='SUP-GEST',
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        self.vinculo_a = self._criar_vinculo('20000000001', 'Ana Silva', '3A', self.curso)
        self.vinculo_b = self._criar_vinculo('20000000002', 'Bruno Lima', '3A', self.curso)
        self.vinculo_c = self._criar_vinculo('20000000003', 'Carla Souza', '3B', self.curso)
        self.vinculo_superior = self._criar_vinculo('20000000004', 'Davi Rocha', '1A', self.outro_curso)
        self.hoje = timezone.now().astimezone(FUSO_FORTALEZA).date()
        self.amanha = self.hoje + timedelta(days=1)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(self.gestor)}')

    def _criar_vinculo(self, cpf, nome, turma, curso):
        usuario = Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)
        aluno = Aluno.objects.create(usuario=usuario)
        return AlunoCurso.objects.create(aluno=aluno, curso=curso, turma=turma, matricula=cpf)

    def test_busca_alunos_por_nome_e_cpf(self):
        url = reverse('acesso_campus:aluno-elegivel-list')
        por_nome = self.client.get(url, {'nome': 'ana'})
        self.assertEqual(por_nome.status_code, status.HTTP_200_OK)
        self.assertEqual(len(por_nome.data['dados']), 1)
        self.assertEqual(por_nome.data['dados'][0]['cpf'], '20000000001')

        por_cpf = self.client.get(url, {'cpf': '20000000002'})
        self.assertEqual(len(por_cpf.data['dados']), 1)
        self.assertEqual(por_cpf.data['dados'][0]['nome'], 'Bruno Lima')

        ambos = self.client.get(url, {'nome': 'ana', 'cpf': '20000000002'})
        self.assertEqual(ambos.data['dados'], [])
        self.assertFalse(
            any(item['cpf'] == '20000000004' for item in self.client.get(url).data['dados'])
        )

    def test_lista_turmas_do_escopo(self):
        url = reverse('acesso_campus:turma-list')
        resposta = self.client.get(url, {'curso_id': self.curso.pk})
        turmas = {item['turma'] for item in resposta.data['dados']}
        self.assertEqual(turmas, {'3A', '3B'})

    def test_autorizar_alunos_e_turma(self):
        url = reverse('acesso_campus:autorizacao-criar')
        resposta = self.client.post(
            url,
            {
                'tipo': TipoSolicitacaoAcesso.ENTRADA,
                'data_acesso': self.amanha.isoformat(),
                'hora_autorizada': '07:30',
                'motivo': 'Consulta',
                'aluno_curso_ids': [self.vinculo_a.pk],
            },
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        self.assertEqual(resposta.data['dados'][0]['status'], StatusSolicitacaoAcesso.ACEITA)
        self.assertIsNone(resposta.data['dados'][0]['hora_solicitada'] if 'hora_solicitada' in resposta.data['dados'][0] else None)

        detalhe = self.client.get(
            reverse('acesso_campus:solicitacao-detail', kwargs={'pk': resposta.data['dados'][0]['id']}),
        )
        self.assertEqual(detalhe.status_code, status.HTTP_200_OK)
        self.assertIn('Autorização registrada', detalhe.data['dados']['historico'][0]['texto'])
        self.assertIsNone(detalhe.data['dados']['liberado_por'])

        turma = self.client.post(
            url,
            {
                'tipo': TipoSolicitacaoAcesso.SAIDA,
                'data_acesso': (self.amanha + timedelta(days=1)).isoformat(),
                'hora_autorizada': '11:00',
                'motivo': 'Evento',
                'curso_id': self.curso.pk,
                'turma': '3A',
            },
            format='json',
        )
        self.assertEqual(turma.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(turma.data['dados']), 2)

    def test_aluno_fora_do_ensino_medio_retorna_400(self):
        url = reverse('acesso_campus:autorizacao-criar')
        resposta = self.client.post(
            url,
            {
                'tipo': TipoSolicitacaoAcesso.ENTRADA,
                'data_acesso': self.amanha.isoformat(),
                'hora_autorizada': '08:00',
                'motivo': 'Teste',
                'aluno_curso_ids': [self.vinculo_superior.pk],
            },
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sem_papel_retorna_403_e_l3_autoriza(self):
        url = reverse('acesso_campus:autorizacao-criar')
        payload = {
            'tipo': TipoSolicitacaoAcesso.ENTRADA,
            'data_acesso': self.amanha.isoformat(),
            'hora_autorizada': '08:00',
            'motivo': 'Teste',
            'aluno_curso_ids': [self.vinculo_c.pk],
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(self.alheio)}')
        self.assertEqual(self.client.post(url, payload, format='json').status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(self.l3)}')
        self.assertEqual(self.client.post(url, payload, format='json').status_code, status.HTTP_201_CREATED)

    def test_aceitar_usa_oito_horas_e_recusar_nao_preenche_horario(self):
        pendente = SolicitacaoAcesso.objects.create(
            aluno=self.vinculo_a.aluno,
            aluno_curso=self.vinculo_a,
            origem=OrigemSolicitacaoAcesso.ALUNO,
            tipo=TipoSolicitacaoAcesso.ENTRADA,
            status=StatusSolicitacaoAcesso.PENDENTE,
            data_acesso=self.amanha,
            hora_solicitada=time(7, 0),
            motivo='Atraso',
            justificativa='Consulta médica marcada.',
            aluno_nome='Ana Silva',
            curso_nome='Ensino Médio',
            matricula='20000000001',
        )
        aceitar = self.client.post(
            reverse('acesso_campus:solicitacao-aceitar', kwargs={'pk': pendente.pk}),
            {},
            format='json',
        )
        self.assertEqual(aceitar.status_code, status.HTTP_200_OK)
        self.assertEqual(aceitar.data['dados']['hora_autorizada'], '08:00:00')
        self.assertEqual(aceitar.data['dados']['resultado_avaliacao'], 'Aprovada')
        textos = [item['texto'] for item in aceitar.data['dados']['historico']]
        self.assertTrue(any(texto.startswith('Solicitação enviada') for texto in textos))
        self.assertTrue(any(texto.startswith('Solicitação aceita') for texto in textos))

        outra = SolicitacaoAcesso.objects.create(
            aluno=self.vinculo_b.aluno,
            aluno_curso=self.vinculo_b,
            origem=OrigemSolicitacaoAcesso.ALUNO,
            tipo=TipoSolicitacaoAcesso.SAIDA,
            status=StatusSolicitacaoAcesso.PENDENTE,
            data_acesso=self.amanha,
            hora_solicitada=time(10, 0),
            motivo='Saída',
            justificativa='Compromisso.',
            aluno_nome='Bruno Lima',
            curso_nome='Ensino Médio',
            matricula='20000000002',
        )
        recusar = self.client.post(
            reverse('acesso_campus:solicitacao-recusar', kwargs={'pk': outra.pk}),
            {'observacao': 'Sem documento.'},
            format='json',
        )
        self.assertEqual(recusar.status_code, status.HTTP_200_OK)
        self.assertIsNone(recusar.data['dados']['hora_autorizada'])
        self.assertEqual(recusar.data['dados']['resultado_avaliacao'], 'Recusada')
        self.assertEqual(recusar.data['dados']['status_display'], 'Recusado')

        de_novo = self.client.post(
            reverse('acesso_campus:solicitacao-aceitar', kwargs={'pk': outra.pk}),
            {},
            format='json',
        )
        self.assertEqual(de_novo.status_code, status.HTTP_400_BAD_REQUEST)

    def _payload(self, **extra):
        dados = {
            'tipo': TipoSolicitacaoAcesso.ENTRADA,
            'data_acesso': self.amanha.isoformat(),
            'hora_autorizada': '08:00',
            'motivo': 'Consulta',
        }
        dados.update(extra)
        return dados

    def _pendente(self, vinculo, tipo, data_acesso):
        return SolicitacaoAcesso.objects.create(
            aluno=vinculo.aluno,
            aluno_curso=vinculo,
            origem=OrigemSolicitacaoAcesso.ALUNO,
            tipo=tipo,
            status=StatusSolicitacaoAcesso.PENDENTE,
            data_acesso=data_acesso,
            hora_solicitada=time(7, 0),
            motivo='Atraso',
            justificativa='Consulta.',
            aluno_nome=vinculo.aluno.usuario.nome,
            curso_nome=vinculo.curso.nome,
            matricula=vinculo.matricula or '',
        )

    def test_recusa_data_passada_e_segunda_autorizacao_aceita(self):
        url = reverse('acesso_campus:autorizacao-criar')
        ontem = self.client.post(
            url,
            self._payload(
                data_acesso=(self.hoje - timedelta(days=1)).isoformat(),
                aluno_curso_ids=[self.vinculo_a.pk],
            ),
            format='json',
        )
        self.assertEqual(ontem.status_code, status.HTTP_400_BAD_REQUEST)

        primeira = self.client.post(
            url,
            self._payload(aluno_curso_ids=[self.vinculo_a.pk]),
            format='json',
        )
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)

        segunda = self.client.post(
            url,
            self._payload(aluno_curso_ids=[self.vinculo_a.pk]),
            format='json',
        )
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            SolicitacaoAcesso.objects.filter(
                aluno=self.vinculo_a.aluno,
                tipo=TipoSolicitacaoAcesso.ENTRADA,
                status=StatusSolicitacaoAcesso.ACEITA,
            ).count(),
            1,
        )

        saida = self.client.post(
            url,
            self._payload(tipo=TipoSolicitacaoAcesso.SAIDA, aluno_curso_ids=[self.vinculo_a.pk]),
            format='json',
        )
        self.assertEqual(saida.status_code, status.HTTP_201_CREATED)

        pendente = self._pendente(self.vinculo_a, TipoSolicitacaoAcesso.ENTRADA, self.amanha)
        aceitar = self.client.post(
            reverse('acesso_campus:solicitacao-aceitar', kwargs={'pk': pendente.pk}),
            {},
            format='json',
        )
        self.assertEqual(aceitar.status_code, status.HTTP_400_BAD_REQUEST)

        lista = self.client.get(reverse('acesso_campus:solicitacao-list'))
        origens = {item['origem'] for item in lista.data['dados']}
        self.assertIn(OrigemSolicitacaoAcesso.GESTAO, origens)
        self.assertIn(OrigemSolicitacaoAcesso.ALUNO, origens)

        atrasada = self._pendente(
            self.vinculo_b,
            TipoSolicitacaoAcesso.ENTRADA,
            self.hoje - timedelta(days=1),
        )
        self.assertEqual(
            self.client.post(
                reverse('acesso_campus:solicitacao-aceitar', kwargs={'pk': atrasada.pk}),
                {},
                format='json',
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(
                reverse('acesso_campus:solicitacao-recusar', kwargs={'pk': atrasada.pk}),
                {},
                format='json',
            ).status_code,
            status.HTTP_200_OK,
        )

        outro_curso = Curso.objects.create(
            nome='Ensino Médio 2',
            codigo_curso='EM-GEST-2',
            nivel_ensino=NivelEnsino.ENSINO_MEDIO,
        )
        outro_vinculo = AlunoCurso.objects.create(
            aluno=self.vinculo_a.aluno,
            curso=outro_curso,
            turma='3A',
            matricula='20000000099',
        )
        depois = self.amanha + timedelta(days=3)
        lote = self.client.post(
            url,
            self._payload(
                data_acesso=depois.isoformat(),
                aluno_curso_ids=[self.vinculo_a.pk, outro_vinculo.pk],
            ),
            format='json',
        )
        self.assertEqual(lote.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(SolicitacaoAcesso.objects.filter(data_acesso=depois).exists())

    def test_cinco_papeis_sem_ser_responsavel_nao_analisa(self):
        funcao = Funcao.objects.get(papel_funcao='Diretor(a) de Ensino')
        setor = Setor.objects.create(nome='Direção sem responsável', sigla='DENSR')
        diretor = Usuario.objects.create_user(cpf='10000000005', password='Senha@123', nome='Diretor sem marca')
        SetorVinculo.objects.create(usuario=diretor, setor=setor, funcao=funcao, responsavel=False)
        self.curso.setor = setor
        self.curso.save(update_fields=['setor'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(diretor)}')
        self.assertEqual(
            self.client.get(reverse('acesso_campus:aluno-elegivel-list')).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(
                reverse('acesso_campus:autorizacao-criar'),
                self._payload(aluno_curso_ids=[self.vinculo_a.pk]),
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_vinculo_no_setor_do_curso_autoriza_so_esse_curso(self):
        setor = Setor.objects.create(nome='Coordenação EM', sigla='COEM')
        outro_setor = Setor.objects.create(nome='Outra Coordenação', sigla='COOU')
        self.curso.setor = setor
        self.curso.save(update_fields=['setor'])
        outro_curso = Curso.objects.create(
            nome='Outro Ensino Médio',
            codigo_curso='EM-OUTRO',
            nivel_ensino=NivelEnsino.ENSINO_MEDIO,
            setor=outro_setor,
        )
        outro_vinculo = self._criar_vinculo('20000000005', 'Eva Nunes', '1A', outro_curso)
        funcao = Funcao.objects.create(papel_funcao='Apoio da coordenação teste', descricao='Apoio')
        coordenador = Usuario.objects.create_user(cpf='10000000004', password='Senha@123', nome='Coordenação')
        vinculo = SetorVinculo.objects.create(usuario=coordenador, setor=setor, funcao=funcao, responsavel=False)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token(coordenador)}')
        self.assertEqual(
            self.client.get(reverse('acesso_campus:aluno-elegivel-list')).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        vinculo.responsavel = True
        vinculo.save(update_fields=['responsavel'])
        nomes = {item['nome'] for item in self.client.get(reverse('acesso_campus:aluno-elegivel-list')).data['dados']}
        self.assertIn('Ana Silva', nomes)
        self.assertNotIn('Eva Nunes', nomes)

        url = reverse('acesso_campus:autorizacao-criar')
        propria = self.client.post(url, self._payload(aluno_curso_ids=[self.vinculo_a.pk]), format='json')
        self.assertEqual(propria.status_code, status.HTTP_201_CREATED)
        alheia = self.client.post(url, self._payload(aluno_curso_ids=[outro_vinculo.pk]), format='json')
        self.assertEqual(alheia.status_code, status.HTTP_400_BAD_REQUEST)
