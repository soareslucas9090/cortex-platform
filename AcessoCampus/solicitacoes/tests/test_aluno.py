from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Academico.aluno_cursos.models import AlunoCurso
from Academico.alunos.choices import SituacaoAluno
from Academico.alunos.models import Aluno
from Academico.cursos.choices import NivelEnsino
from Academico.cursos.models import Curso
from AcessoCampus.solicitacoes.choices import (
    OrigemSolicitacaoAcesso,
    StatusSolicitacaoAcesso,
)
from AcessoCampus.solicitacoes.models import SolicitacaoAcesso
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS
from AcessoCampus.tipos.models import TipoAutorizacaoAcesso
from Identidade.usuarios.models import Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo

# 2030-03-11 é uma segunda-feira; horários interpretados em America/Fortaleza.
HOJE = date(2030, 3, 11)
ANTES_DAS_SETE = timezone.make_aware(datetime(2030, 3, 11, 6, 30))
AS_SETE = timezone.make_aware(datetime(2030, 3, 11, 7, 0))
DEPOIS_DAS_SETE = timezone.make_aware(datetime(2030, 3, 11, 9, 15))

PDF_MINIMO = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\n%%EOF'


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_curso(codigo, nivel_ensino=NivelEnsino.ENSINO_MEDIO):
    return Curso.objects.create(nome=f'Curso {codigo}', codigo_curso=codigo, nivel_ensino=nivel_ensino)


def criar_aluno(cpf, curso, nome='Aluno Teste', **kwargs_aluno):
    usuario = Usuario.objects.create_user(cpf=cpf, password='Senha@123', nome=nome)
    aluno = Aluno.objects.create(usuario=usuario, **kwargs_aluno)
    vinculo = AlunoCurso.objects.create(aluno=aluno, curso=curso, matricula=f'M{cpf}', ativo=True)
    return aluno, vinculo


class SolicitacaoAlunoBaseTestCase(APITestCase):

    def setUp(self):
        self.curso_em = criar_curso('14IINF-T')
        self.curso_superior = criar_curso('SUP-T', nivel_ensino=NivelEnsino.SUPERIOR)
        self.aluno, self.vinculo = criar_aluno('51111111111', self.curso_em, nome='Maria EM')
        self.url_lista = reverse('acesso_campus:minha-solicitacao-list')
        self.tipo_entrada = TipoAutorizacaoAcesso.objects.get(nome=NOME_TIPO_ENTRADA_CAMPUS)
        self.tipo_saida = TipoAutorizacaoAcesso.objects.get(nome=NOME_TIPO_SAIDA_CAMPUS)

        patcher = patch('django.utils.timezone.now', return_value=ANTES_DAS_SETE)
        self.mock_agora = patcher.start()
        self.addCleanup(patcher.stop)

        patcher_s3 = patch('AppCore.common.storage.s3.enviar_arquivo_s3')
        self.mock_enviar = patcher_s3.start()
        self.mock_enviar.side_effect = lambda prefixo, objeto_id, arquivo, **kwargs: (
            f'{prefixo}/{objeto_id}/abc123.{kwargs["extensao"]}'
        )
        self.addCleanup(patcher_s3.stop)

    def autenticar(self, usuario):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario)}')

    def payload(self, vinculo=None, **extras):
        dados = {
            'aluno_curso': (vinculo or self.vinculo).pk,
            'tipo': self.tipo_entrada.pk,
            'data_acesso': HOJE.isoformat(),
            'hora_solicitada': '08:00',
            'motivo': 'Exame de sangue',
            'justificativa': 'Exame em jejum no início da manhã.',
            'anexo': SimpleUploadedFile('exame.pdf', PDF_MINIMO, content_type='application/pdf'),
        }
        dados.update(extras)
        return dados

    def solicitar(self, **kwargs):
        return self.client.post(self.url_lista, self.payload(**kwargs), format='multipart')

    def criar_autorizacao_aceita(self, tipo, data_acesso, origem=OrigemSolicitacaoAcesso.GESTAO):
        return SolicitacaoAcesso.objects.create(
            aluno=self.aluno,
            aluno_curso=self.vinculo,
            origem=origem,
            tipo=tipo,
            status=StatusSolicitacaoAcesso.ACEITA,
            data_acesso=data_acesso,
            hora_autorizada=time(8, 0),
            motivo='Evento externo',
            aluno_nome='Maria EM',
            curso_nome=self.curso_em.nome,
        )


class PermissaoSolicitarTestCase(SolicitacaoAlunoBaseTestCase):

    def test_aluno_ensino_medio_recebe_solicitar(self):
        capacidades = self.aluno.usuario.permissoes['acesso_campus']
        self.assertTrue(capacidades['solicitar'])
        self.assertFalse(capacidades['analisar_solicitacoes'])

    def test_aluno_superior_nao_recebe_solicitar(self):
        aluno, _ = criar_aluno('52222222222', self.curso_superior)
        self.assertFalse(aluno.usuario.permissoes['acesso_campus']['solicitar'])

    def test_aluno_trancado_nao_recebe_solicitar(self):
        aluno, _ = criar_aluno('53333333333', self.curso_em, situacao=SituacaoAluno.TRANCADO)
        self.assertFalse(aluno.usuario.permissoes['acesso_campus']['solicitar'])

    def test_vinculo_inativo_nao_concede_solicitar(self):
        self.vinculo.ativo = False
        self.vinculo.save()
        self.assertFalse(self.aluno.usuario.permissoes['acesso_campus']['solicitar'])

    def test_curso_sem_nivel_nao_concede_solicitar(self):
        aluno, _ = criar_aluno('54444444444', criar_curso('SEM-NIVEL', nivel_ensino=None))
        self.assertFalse(aluno.usuario.permissoes['acesso_campus']['solicitar'])


class SolicitarAcessoAlunoTestCase(SolicitacaoAlunoBaseTestCase):

    def setUp(self):
        super().setUp()
        self.autenticar(self.aluno.usuario)

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        self.assertEqual(self.solicitar().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sem_capacidade_retorna_403(self):
        aluno_superior, vinculo_superior = criar_aluno('57777777777', self.curso_superior)
        self.autenticar(aluno_superior.usuario)
        self.assertEqual(self.solicitar(vinculo=vinculo_superior).status_code, status.HTTP_403_FORBIDDEN)

    def test_aluno_solicita_entrada(self):
        resposta = self.solicitar()
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        dados = resposta.data['dados']
        self.assertEqual(dados['origem'], OrigemSolicitacaoAcesso.ALUNO)
        self.assertEqual(dados['status'], StatusSolicitacaoAcesso.PENDENTE)
        self.assertEqual(dados['tipo'], self.tipo_entrada.pk)
        self.assertEqual(dados['tipo_display'], NOME_TIPO_ENTRADA_CAMPUS)
        self.assertEqual(dados['data_acesso'], HOJE.isoformat())
        self.assertEqual(dados['hora_solicitada'], '08:00:00')
        self.assertIsNone(dados['hora_autorizada'])
        self.assertEqual(dados['aluno_nome'], 'Maria EM')
        self.assertEqual(dados['curso_nome'], self.curso_em.nome)
        self.assertEqual(dados['matricula'], self.vinculo.matricula)
        self.assertIn('/anexo/', dados['anexo'])
        self.assertEqual(self.mock_enviar.call_args.kwargs['content_type'], 'application/pdf')
        self.assertEqual([item['descricao'] for item in dados['historico']], ['Solicitação enviada'])

    def test_snapshot_nao_muda_quando_dados_do_aluno_mudam(self):
        resposta = self.solicitar()
        Usuario.objects.filter(pk=self.aluno.usuario.pk).update(nome='Nome Novo')
        self.assertEqual(SolicitacaoAcesso.objects.get(pk=resposta.data['dados']['id']).aluno_nome, 'Maria EM')

    def test_vinculo_superior_do_proprio_aluno_retorna_400(self):
        vinculo_superior = AlunoCurso.objects.create(
            aluno=self.aluno,
            curso=self.curso_superior,
            matricula='MSUP',
            ativo=True,
        )
        resposta = self.solicitar(vinculo=vinculo_superior)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ensino médio', resposta.data['detail'])

    def test_vinculo_de_outro_aluno_retorna_400(self):
        _, vinculo_outro = criar_aluno('58888888888', self.curso_em)
        self.assertEqual(self.solicitar(vinculo=vinculo_outro).status_code, status.HTTP_400_BAD_REQUEST)

    def test_tipo_criado_pela_gestao_retorna_400(self):
        tipo_gestao = TipoAutorizacaoAcesso.objects.create(nome='Aula de campo')
        resposta = self.solicitar(tipo=tipo_gestao.pk)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('entrada ou saída', resposta.data['detail'])
        self.mock_enviar.assert_not_called()

    def test_tipo_inexistente_retorna_400(self):
        self.assertEqual(self.solicitar(tipo=999999).status_code, status.HTTP_400_BAD_REQUEST)

    def test_data_passada_retorna_400(self):
        resposta = self.solicitar(data_acesso=(HOJE - timedelta(days=1)).isoformat())
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entrada_para_hoje_ate_as_sete(self):
        self.mock_agora.return_value = AS_SETE
        self.assertEqual(self.solicitar().status_code, status.HTTP_201_CREATED)

    def test_entrada_para_hoje_depois_das_sete_retorna_400(self):
        self.mock_agora.return_value = DEPOIS_DAS_SETE
        resposta = self.solicitar(hora_solicitada='10:00')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('07:00', resposta.data['detail'])

    def test_entrada_para_amanha_depois_das_sete(self):
        self.mock_agora.return_value = DEPOIS_DAS_SETE
        resposta = self.solicitar(data_acesso=(HOJE + timedelta(days=1)).isoformat())
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_saida_para_hoje_depois_das_sete(self):
        self.mock_agora.return_value = DEPOIS_DAS_SETE
        resposta = self.solicitar(tipo=self.tipo_saida.pk, hora_solicitada='14:00')
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)

    def test_horario_que_ja_passou_retorna_400(self):
        self.mock_agora.return_value = DEPOIS_DAS_SETE
        resposta = self.solicitar(tipo=self.tipo_saida.pk, hora_solicitada='09:00')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pedidos_pendentes_repetidos_sao_permitidos(self):
        self.assertEqual(self.solicitar().status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.solicitar().status_code, status.HTTP_201_CREATED)

    def test_autorizacao_aceita_da_gestao_bloqueia_mesmo_dia_e_tipo(self):
        self.criar_autorizacao_aceita(self.tipo_entrada, HOJE)
        resposta = self.solicitar()
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('autorização aceita', resposta.data['detail'])
        self.mock_enviar.assert_not_called()

    def test_pedido_aceito_do_aluno_bloqueia_mesmo_dia_e_tipo(self):
        self.criar_autorizacao_aceita(self.tipo_entrada, HOJE, origem=OrigemSolicitacaoAcesso.ALUNO)
        self.assertEqual(self.solicitar().status_code, status.HTTP_400_BAD_REQUEST)

    def test_autorizacao_aceita_de_outro_tipo_ou_dia_nao_bloqueia(self):
        self.criar_autorizacao_aceita(self.tipo_saida, HOJE)
        self.criar_autorizacao_aceita(self.tipo_entrada, HOJE + timedelta(days=1))
        self.assertEqual(self.solicitar().status_code, status.HTTP_201_CREATED)

    def test_pedido_recusado_nao_bloqueia(self):
        recusado = self.criar_autorizacao_aceita(self.tipo_entrada, HOJE, origem=OrigemSolicitacaoAcesso.ALUNO)
        SolicitacaoAcesso.objects.filter(pk=recusado.pk).update(status=StatusSolicitacaoAcesso.RECUSADA)
        self.assertEqual(self.solicitar().status_code, status.HTTP_201_CREATED)

    def test_campos_obrigatorios_e_limites(self):
        self.assertEqual(self.solicitar(motivo='').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.solicitar(justificativa='').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.solicitar(motivo='a' * 101).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.solicitar(justificativa='a' * 501).status_code, status.HTTP_400_BAD_REQUEST)
        sem_hora = self.payload()
        del sem_hora['hora_solicitada']
        self.assertEqual(
            self.client.post(self.url_lista, sem_hora, format='multipart').status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_sem_comprovante_retorna_400(self):
        sem_anexo = self.payload()
        del sem_anexo['anexo']
        resposta = self.client.post(self.url_lista, sem_anexo, format='multipart')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_enviar.assert_not_called()
        self.assertFalse(SolicitacaoAcesso.objects.exists())

    def test_comprovante_com_conteudo_invalido_retorna_400(self):
        anexo = SimpleUploadedFile('exame.pdf', b'texto qualquer', content_type='application/pdf')
        resposta = self.solicitar(anexo=anexo)
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_enviar.assert_not_called()
        self.assertFalse(SolicitacaoAcesso.objects.exists())

    @patch('AcessoCampus.solicitacoes.rules.TAMANHO_MAXIMO_ANEXO_BYTES', 10)
    def test_comprovante_acima_do_limite_retorna_400(self):
        self.assertEqual(self.solicitar().status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_enviar.assert_not_called()

    @patch('AppCore.common.storage.s3.remover_objeto_s3')
    def test_comprovante_removido_quando_o_pedido_falha_depois_do_upload(self, mock_remover):
        with patch(
            'AcessoCampus.solicitacoes.models.SolicitacaoAcesso.objects.create',
            side_effect=RuntimeError('falha simulada'),
        ):
            resposta = self.solicitar()
        self.assertGreaterEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_enviar.assert_called_once()
        mock_remover.assert_called_once()


class MinhasSolicitacoesTestCase(SolicitacaoAlunoBaseTestCase):

    def setUp(self):
        super().setUp()
        self.autenticar(self.aluno.usuario)
        self.entrada = self.solicitar().data['dados']
        self.saida = self.solicitar(
            tipo=self.tipo_saida.pk,
            hora_solicitada='14:00',
            motivo='Consulta odontológica',
        ).data['dados']

        self.outro_aluno, self.outro_vinculo = criar_aluno('59999999999', self.curso_em, nome='João EM')
        self.autenticar(self.outro_aluno.usuario)
        self.solicitacao_outro = self.solicitar(vinculo=self.outro_vinculo).data['dados']
        self.autenticar(self.aluno.usuario)

    def ids(self, resposta):
        return [item['id'] for item in resposta.data['dados']]

    def test_lista_apenas_as_proprias_mais_recentes_primeiro(self):
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids(resposta), [self.saida['id'], self.entrada['id']])

    def test_lista_inclui_autorizacao_registrada_pela_gestao(self):
        autorizacao = self.criar_autorizacao_aceita(self.tipo_saida, HOJE + timedelta(days=3))
        self.assertIn(autorizacao.pk, self.ids(self.client.get(self.url_lista)))

    def test_filtros_por_tipo_status_e_busca(self):
        resposta = self.client.get(self.url_lista, {'tipo': self.tipo_saida.pk})
        self.assertEqual(self.ids(resposta), [self.saida['id']])
        resposta = self.client.get(self.url_lista, {'busca': 'odontologica'})
        self.assertEqual(self.ids(resposta), [self.saida['id']])
        resposta = self.client.get(self.url_lista, {'status': StatusSolicitacaoAcesso.ACEITA})
        self.assertEqual(self.ids(resposta), [])

    def test_filtros_e_ordenacao_invalidos_sao_ignorados(self):
        resposta = self.client.get(
            self.url_lista,
            {'status': 'abc', 'tipo': 'x', 'ordenacao': 'aluno__usuario__password'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids(resposta), [self.saida['id'], self.entrada['id']])

    def test_ordenacao_pelas_colunas(self):
        futura = self.solicitar(
            data_acesso=(HOJE + timedelta(days=2)).isoformat(),
            motivo='Atendimento médico',
        ).data['dados']
        avaliador = Usuario.objects.create_user(cpf='50000000010', password='Senha@123', nome='Ana Gestora')
        SolicitacaoAcesso.objects.filter(pk=self.entrada['id']).update(avaliada_por=avaliador)
        entrada, saida, futura = self.entrada['id'], self.saida['id'], futura['id']

        esperado = {
            'data_liberacao': [entrada, saida, futura],
            '-data_liberacao': [futura, saida, entrada],
            'data_solicitacao': [entrada, saida, futura],
            '-data_solicitacao': [futura, saida, entrada],
            'tipo': [futura, entrada, saida],
            '-tipo': [saida, futura, entrada],
            'motivo': [futura, saida, entrada],
            '-motivo': [entrada, saida, futura],
            'avaliado_por': [entrada, futura, saida],
            '-avaliado_por': [entrada, futura, saida],
        }
        for ordenacao, ids in esperado.items():
            with self.subTest(ordenacao=ordenacao):
                resposta = self.client.get(self.url_lista, {'ordenacao': ordenacao})
                self.assertEqual(resposta.status_code, status.HTTP_200_OK)
                self.assertEqual(self.ids(resposta), ids)

    def test_detalhe_da_propria_e_404_de_outro_aluno(self):
        propria = reverse('acesso_campus:minha-solicitacao-detail', kwargs={'pk': self.entrada['id']})
        self.assertEqual(self.client.get(propria).status_code, status.HTTP_200_OK)
        alheia = reverse('acesso_campus:minha-solicitacao-detail', kwargs={'pk': self.solicitacao_outro['id']})
        self.assertEqual(self.client.get(alheia).status_code, status.HTTP_404_NOT_FOUND)

    def test_aluno_que_perdeu_elegibilidade_ainda_consulta(self):
        self.vinculo.ativo = False
        self.vinculo.save()
        self.assertFalse(self.aluno.usuario.permissoes['acesso_campus']['solicitar'])

        self.assertEqual(len(self.ids(self.client.get(self.url_lista))), 2)
        self.assertEqual(self.solicitar().status_code, status.HTTP_403_FORBIDDEN)

    def test_usuario_sem_perfil_de_aluno_lista_vazio(self):
        self.autenticar(Usuario.objects.create_user(cpf='50000000002', password='Senha@123', nome='Servidor'))
        resposta = self.client.get(self.url_lista)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['dados'], [])


class IntegracaoGestaoTestCase(SolicitacaoAlunoBaseTestCase):
    """O pedido do aluno chega à fila da gestão e o comprovante só abre para quem pode vê-lo."""

    def setUp(self):
        super().setUp()
        self.gestor = Usuario.objects.create_user(cpf='10000000001', password='Senha@123', nome='Gestor Ensino')
        setor = Setor.objects.create(nome='Direção de Ensino Teste', sigla='DENST')
        SetorVinculo.objects.create(
            usuario=self.gestor,
            setor=setor,
            funcao=Funcao.objects.get(papel_funcao='Diretor(a) de Ensino'),
            responsavel=True,
        )

        self.autenticar(self.aluno.usuario)
        self.pedido = self.solicitar().data['dados']
        self.url_anexo = reverse('acesso_campus:solicitacao-anexo', kwargs={'pk': self.pedido['id']})

    def test_gestor_ve_e_aceita_o_pedido_do_aluno(self):
        self.autenticar(self.gestor)
        lista = self.client.get(reverse('acesso_campus:solicitacao-list'))
        self.assertIn(self.pedido['id'], [item['id'] for item in lista.data['dados']])

        detalhe_gestao = self.client.get(
            reverse('acesso_campus:solicitacao-detail', kwargs={'pk': self.pedido['id']}),
        )
        self.assertIn('/anexo/', detalhe_gestao.data['dados']['anexo'])

        aceitar = self.client.post(
            reverse('acesso_campus:solicitacao-aceitar', kwargs={'pk': self.pedido['id']}),
            {'hora_autorizada': '08:30'},
            format='json',
        )
        self.assertEqual(aceitar.status_code, status.HTTP_200_OK, aceitar.data)
        self.assertEqual(aceitar.data['dados']['hora_autorizada'], '08:30:00')

        self.autenticar(self.aluno.usuario)
        detalhe = self.client.get(
            reverse('acesso_campus:minha-solicitacao-detail', kwargs={'pk': self.pedido['id']}),
        )
        self.assertEqual(detalhe.data['dados']['status'], StatusSolicitacaoAcesso.ACEITA)
        self.assertEqual(detalhe.data['dados']['avaliada_por']['nome'], 'Gestor Ensino')

    @patch('AppCore.common.storage.s3.iterar_objeto_s3')
    def test_dono_e_gestor_obtem_comprovante(self, mock_iterar):
        mock_iterar.side_effect = lambda *args, **kwargs: (iter([PDF_MINIMO]), 'application/pdf')
        resposta = self.client.get(self.url_anexo)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(b''.join(resposta.streaming_content), PDF_MINIMO)

        self.autenticar(self.gestor)
        self.assertEqual(self.client.get(self.url_anexo).status_code, status.HTTP_200_OK)

    def test_comprovante_exige_autenticacao(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url_anexo).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_outro_aluno_nao_obtem_comprovante(self):
        outro, _ = criar_aluno('50000000001', self.curso_em)
        self.autenticar(outro.usuario)
        self.assertEqual(self.client.get(self.url_anexo).status_code, status.HTTP_404_NOT_FOUND)

    def test_autorizacao_da_gestao_sem_comprovante_retorna_404(self):
        autorizacao = self.criar_autorizacao_aceita(self.tipo_saida, HOJE + timedelta(days=3))
        url = reverse('acesso_campus:solicitacao-anexo', kwargs={'pk': autorizacao.pk})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
