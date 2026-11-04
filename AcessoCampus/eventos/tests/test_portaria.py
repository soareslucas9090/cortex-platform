import uuid
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from Academico.aluno_cursos.models import AlunoCurso
from Academico.alunos.models import Aluno
from Academico.cursos.choices import NivelEnsino
from Academico.cursos.models import Curso
from AcessoCampus.eventos.models import EventoAcesso
from AcessoCampus.permissoes.models import PermissaoUsuarioAcessoCampus
from AcessoCampus.registros.models import RegistroAcesso
from AcessoCampus.solicitacoes.choices import OrigemSolicitacaoAcesso, StatusSolicitacaoAcesso
from AcessoCampus.solicitacoes.models import SolicitacaoAcesso
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS
from AcessoCampus.tipos.models import TipoAutorizacaoAcesso
from Identidade.usuarios.models import TipoContaColetiva, Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo


def token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


class PortariaAcessoCampusTest(APITestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(cpf="30000000001", password="Senha@123", nome="Admin Portaria")
        self.sem_permissao = Usuario.objects.create_user(cpf="30000000002", password="Senha@123", nome="Sem Permissão")
        self.curso = Curso.objects.create(
            nome="Ensino Médio Portaria", codigo_curso="EM-PORTARIA", nivel_ensino=NivelEnsino.ENSINO_MEDIO
        )
        self.vinculo_a = self._criar_vinculo("31000000001", "Ana Portaria")
        self.vinculo_b = self._criar_vinculo("31000000002", "Bruno Portaria")
        self.tipo_entrada = TipoAutorizacaoAcesso.objects.get(nome=NOME_TIPO_ENTRADA_CAMPUS)
        self.hoje = timezone.localdate()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(self.admin)}")

    def _criar_vinculo(self, cpf, nome):
        usuario = Usuario.objects.create_user(cpf=cpf, password="Senha@123", nome=nome)
        aluno = Aluno.objects.create(usuario=usuario)
        return AlunoCurso.objects.create(aluno=aluno, curso=self.curso, turma="3A", matricula=cpf)

    def _criar_evento(self, vinculo, *, grupo=None, turma_origem="", data_acesso=None, hora_autorizada=None):
        horario_valido = timezone.localtime() + timedelta(minutes=5)
        solicitacao = SolicitacaoAcesso.objects.create(
            aluno=vinculo.aluno,
            aluno_curso=vinculo,
            origem=OrigemSolicitacaoAcesso.GESTAO,
            tipo=self.tipo_entrada,
            status=StatusSolicitacaoAcesso.ACEITA,
            data_acesso=data_acesso or horario_valido.date(),
            hora_autorizada=hora_autorizada or horario_valido.time().replace(tzinfo=None),
            motivo="Teste da portaria",
            avaliada_por=self.admin,
            avaliada_em=timezone.now(),
            lote_id=uuid.uuid4(),
            turma_origem=turma_origem,
            aluno_nome=vinculo.aluno.usuario.nome,
            curso_nome=self.curso.nome,
            matricula=vinculo.matricula,
        )
        return EventoAcesso().business.materializar_para_solicitacao(solicitacao, grupo_portaria_id=grupo)

    def test_admin_registra_individual_e_replay_e_idempotente(self):
        evento = self._criar_evento(self.vinculo_a)
        url = reverse("acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": evento.grupo_portaria_id})

        primeira = self.client.post(url, {}, format="json")
        self.assertEqual(primeira.status_code, status.HTTP_200_OK, primeira.data)
        self.assertEqual(primeira.data["dados"]["autorizacao"]["status"], "CONCLUIDA")
        self.assertEqual(primeira.data["dados"]["registro"]["confirmados_agora"], 1)

        repetida = self.client.post(url, {}, format="json")
        self.assertEqual(repetida.status_code, status.HTTP_200_OK, repetida.data)
        self.assertEqual(repetida.data["dados"]["registro"]["ja_confirmados"], 1)
        self.assertEqual(RegistroAcesso.objects.filter(evento=evento).count(), 1)

    def test_turma_aceita_conferencia_parcial_em_entrada(self):
        grupo = uuid.uuid4()
        evento_a = self._criar_evento(self.vinculo_a, grupo=grupo, turma_origem="3A")
        evento_b = self._criar_evento(self.vinculo_b, grupo=grupo, turma_origem="3A")
        url = reverse("acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": grupo})

        parcial = self.client.post(url, {"aluno_ids": [evento_a.aluno_id]}, format="json")
        self.assertEqual(parcial.status_code, status.HTTP_200_OK, parcial.data)
        self.assertEqual(parcial.data["dados"]["autorizacao"]["status"], "PENDENTE")
        self.assertEqual(parcial.data["dados"]["autorizacao"]["progresso"]["liberados"], 1)

        final = self.client.post(url, {"aluno_ids": [evento_b.aluno_id]}, format="json")
        self.assertEqual(final.status_code, status.HTTP_200_OK, final.data)
        self.assertEqual(final.data["dados"]["autorizacao"]["status"], "CONCLUIDA")
        self.assertEqual(final.data["dados"]["autorizacao"]["progresso"]["pendentes"], 0)

    def test_evento_expirado_nao_pode_ser_registrado(self):
        evento = self._criar_evento(self.vinculo_a, data_acesso=self.hoje - timedelta(days=1))
        resposta = self.client.post(
            reverse("acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": evento.grupo_portaria_id}),
            {},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(RegistroAcesso.objects.filter(evento=evento).exists())

    def test_horario_autorizado_permite_antes_e_expira_depois_do_horario(self):
        agora = timezone.localtime()
        horario_futuro = agora + timedelta(minutes=30)
        evento_futuro = self._criar_evento(
            self.vinculo_a,
            data_acesso=horario_futuro.date(),
            hora_autorizada=horario_futuro.time().replace(tzinfo=None),
        )
        resposta_antes = self.client.post(
            reverse(
                "acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": evento_futuro.grupo_portaria_id}
            ),
            {},
            format="json",
        )
        self.assertEqual(resposta_antes.status_code, status.HTTP_200_OK, resposta_antes.data)
        self.assertTrue(RegistroAcesso.objects.filter(evento=evento_futuro).exists())

        horario_expirado = agora - timedelta(minutes=1)
        evento_expirado = self._criar_evento(
            self.vinculo_b,
            data_acesso=horario_expirado.date(),
            hora_autorizada=horario_expirado.time().replace(tzinfo=None),
        )
        EventoAcesso().business.expirar_pendentes()
        evento_expirado.refresh_from_db()
        self.assertIsNotNone(evento_expirado.expirado_em)

        resposta_depois = self.client.post(
            reverse(
                "acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": evento_expirado.grupo_portaria_id}
            ),
            {},
            format="json",
        )
        self.assertEqual(resposta_depois.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(RegistroAcesso.objects.filter(evento=evento_expirado).exists())

    def test_acoes_ficam_disponiveis_antes_do_horario_autorizado(self):
        agora = timezone.localtime()
        futuro = agora + timedelta(minutes=30)
        evento = self._criar_evento(
            self.vinculo_a, data_acesso=futuro.date(), hora_autorizada=futuro.time().replace(tzinfo=None)
        )

        listagem = self.client.get(reverse("acesso_campus:evento-acesso-list"))
        self.assertEqual(listagem.status_code, status.HTTP_200_OK, listagem.data)
        autorizacao = next(item for item in listagem.data["dados"] if item["id"] == str(evento.grupo_portaria_id))
        self.assertTrue(autorizacao["acoes"]["pode_registrar"])

        alunos = self.client.get(
            reverse("acesso_campus:evento-acesso-alunos", kwargs={"grupo_portaria_id": evento.grupo_portaria_id})
        )
        self.assertEqual(alunos.status_code, status.HTTP_200_OK, alunos.data)
        self.assertTrue(alunos.data["dados"][0]["pode_liberar"])

    def test_usuario_sem_permissao_recebe_403(self):
        self._criar_evento(self.vinculo_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(self.sem_permissao)}")
        resposta = self.client.get(reverse("acesso_campus:evento-acesso-list"))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_guarita_exige_responsavel_do_pool(self):
        evento = self._criar_evento(self.vinculo_a)
        guarita = Usuario.objects.create_user(
            cpf="30000000003",
            password="Senha@123",
            nome="Guarita",
            usuario_coletivo=True,
            tipo_conta_coletiva=TipoContaColetiva.GUARITA,
        )
        vigilante = Usuario.objects.create_user(cpf="30000000004", password="Senha@123", nome="Vigilante Elegível")
        funcao = Funcao.objects.create(papel_funcao="Vigilante teste", descricao="Vigilante")
        setor = Setor.objects.create(nome="Segurança teste", sigla="SEGTEST")
        SetorVinculo.objects.create(usuario=vigilante, setor=setor, funcao=funcao)
        guarita.funcoes_coletivo.add(funcao)
        PermissaoUsuarioAcessoCampus.objects.create(usuario=guarita, operar_portaria=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(guarita)}")
        url = reverse("acesso_campus:evento-acesso-registrar", kwargs={"grupo_portaria_id": evento.grupo_portaria_id})

        sem_responsavel = self.client.post(url, {}, format="json")
        self.assertEqual(sem_responsavel.status_code, status.HTTP_400_BAD_REQUEST)
        fora_pool = self.client.post(url, {"responsavel_liberacao_id": self.sem_permissao.pk}, format="json")
        self.assertEqual(fora_pool.status_code, status.HTTP_400_BAD_REQUEST)

        sucesso = self.client.post(url, {"responsavel_liberacao_id": vigilante.pk}, format="json")
        self.assertEqual(sucesso.status_code, status.HTTP_200_OK, sucesso.data)
        registro = RegistroAcesso.objects.get(evento=evento)
        self.assertEqual(registro.registrado_por, vigilante)
        self.assertEqual(registro.operado_por, guarita)

    def test_listagem_filtra_status_e_nao_expoe_cpf(self):
        evento = self._criar_evento(self.vinculo_a)
        resposta = self.client.get(reverse("acesso_campus:evento-acesso-list"), {"status": "PENDENTE"})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        self.assertEqual(resposta.data["count"], 1)
        self.assertNotIn("cpf", str(resposta.data["dados"][0]).lower())

        alunos = self.client.get(
            reverse("acesso_campus:evento-acesso-alunos", kwargs={"grupo_portaria_id": evento.grupo_portaria_id})
        )
        self.assertEqual(alunos.data["dados"][0]["aluno"]["cpf"], "310.000.000-01")

        responsaveis = self.client.get(reverse("acesso_campus:evento-acesso-responsaveis"))
        self.assertEqual(responsaveis.data["dados"][0]["cpf"], "300.000.000-01")
