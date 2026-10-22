import smtplib
from unittest.mock import patch

from django.core.mail import EmailMultiAlternatives
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import (
    NotFoundException,
    SystemErrorException,
    ValidationException,
)
from Identidade.contatos.models import Contato
from Identidade.usuarios.models import Usuario

from Notificacoes.notificacoes.canais import obter_canal
from Notificacoes.notificacoes.choices import CanalEnvio, StatusEnvio
from Notificacoes.notificacoes.helpers import NotificacaoHelpers
from Notificacoes.notificacoes.models import Envio, Notificacao


def _criar_usuario(cpf, email=None, nome='Usuário teste'):
    kwargs = {'cpf': cpf, 'password': 'Senha@123', 'nome': nome}
    if email is not None:
        kwargs['email'] = email
    return Usuario.objects.create_user(**kwargs)


class DisparoNotificacaoTestCase(APITestCase):
    _cpf_seq = 70000000000

    def _proximo_cpf(self):
        DisparoNotificacaoTestCase._cpf_seq += 1
        return str(DisparoNotificacaoTestCase._cpf_seq)

    def test_disparar_cria_notificacao_e_envio_email_pendente_sem_envio_sistema(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay') as delay_mock:
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.disparo',
                    titulo='Título',
                    corpo='Corpo da mensagem',
                )

        self.assertIsNotNone(notificacao.pk)
        self.assertEqual(Notificacao.objects.count(), 1)
        envios = Envio.objects.filter(notificacao=notificacao)
        self.assertEqual(envios.count(), 1)
        envio = envios.get()
        self.assertEqual(envio.canal, CanalEnvio.EMAIL)
        self.assertEqual(envio.status, StatusEnvio.PENDENTE)
        delay_mock.assert_called_once_with(envio.pk)

    def test_idempotencia_retorna_mesma_notificacao_sem_duplicar_envio(self):
        usuario = _criar_usuario(self._proximo_cpf())
        chave = 'evento:1'
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                primeira = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.idempotencia',
                    titulo='Título',
                    corpo='Corpo',
                    chave_idempotencia=chave,
                )
                segunda = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.idempotencia',
                    titulo='Outro título',
                    corpo='Outro corpo',
                    chave_idempotencia=chave,
                )

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(Notificacao.objects.count(), 1)
        self.assertEqual(Envio.objects.filter(notificacao=primeira).count(), 1)

    def test_sem_chave_dois_disparos_criam_duas_notificacoes(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.sem_chave',
                    titulo='Título 1',
                    corpo='Corpo 1',
                )
                Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.sem_chave',
                    titulo='Título 2',
                    corpo='Corpo 2',
                )

        self.assertEqual(Notificacao.objects.filter(destinatario=usuario).count(), 2)

    def test_sem_email_envio_fica_ignorado_e_notificacao_permanece(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.sem_email',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        Notificacao().business.processar_envio(envio.pk)
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.IGNORADO)
        self.assertEqual(envio.ultimo_erro, 'Destinatário sem e-mail.')
        self.assertTrue(Notificacao.objects.filter(pk=notificacao.pk).exists())

    @patch('Notificacoes.notificacoes.canais.enviar_email_simples')
    def test_com_email_usuario_processar_envio_marca_enviado(self, enviar_mock):
        usuario = _criar_usuario(self._proximo_cpf(), email='usuario@teste.local')
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.com_email',
                    titulo='Assunto',
                    corpo='Mensagem',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        Notificacao().business.processar_envio(envio.pk)
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.ENVIADO)
        self.assertEqual(envio.destino, 'usuario@teste.local')
        enviar_mock.assert_called_once()

    @patch('Notificacoes.notificacoes.canais.enviar_email_simples')
    def test_email_academico_contato_quando_usuario_sem_email(self, enviar_mock):
        usuario = _criar_usuario(self._proximo_cpf())
        Contato.objects.create(
            usuario=usuario,
            email_academico='academico@teste.local',
        )
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.contato',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        Notificacao().business.processar_envio(envio.pk)
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.ENVIADO)
        self.assertEqual(envio.destino, 'academico@teste.local')
        enviar_mock.assert_called_once()

    def test_sms_whatsapp_criam_envio_ignorado_sem_enfileirar_task(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay') as delay_mock:
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.canais',
                    titulo='Título',
                    corpo='Corpo',
                    canais=['sistema', 'sms', 'whatsapp'],
                )

        envios = Envio.objects.filter(notificacao=notificacao).order_by('canal')
        self.assertEqual(envios.count(), 2)
        for envio in envios:
            self.assertEqual(envio.status, StatusEnvio.IGNORADO)
            self.assertIn(envio.canal, (CanalEnvio.SMS, CanalEnvio.WHATSAPP))
        delay_mock.assert_not_called()

    @patch('Notificacoes.notificacoes.canais.enviar_email_simples')
    def test_task_nao_reprocessa_envio_ja_enviado(self, enviar_mock):
        from Notificacoes.notificacoes.tasks import enviar_envio_task

        usuario = _criar_usuario(self._proximo_cpf(), email='enviado@teste.local')
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.noop',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        Notificacao().business.processar_envio(envio.pk)
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.ENVIADO)
        tentativas_antes = envio.tentativas

        enviar_envio_task(envio.pk)
        envio.refresh_from_db()
        self.assertEqual(envio.tentativas, tentativas_antes)
        self.assertEqual(enviar_mock.call_count, 1)

    @patch.object(
        EmailMultiAlternatives,
        'send',
        side_effect=smtplib.SMTPException('connection refused'),
    )
    def test_task_esgota_retries_e_marca_falhou(self, _send_mock):
        from Notificacoes.notificacoes.tasks import enviar_envio_task

        usuario = _criar_usuario(self._proximo_cpf(), email='falha@teste.local')
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.falha',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        enviar_envio_task.push_request(retries=3)
        try:
            enviar_envio_task.run(envio.pk)
        finally:
            enviar_envio_task.pop_request()
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.FALHOU)
        self.assertIn('SMTPException', envio.ultimo_erro)
        self.assertTrue(Notificacao.objects.filter(pk=notificacao.pk).exists())

    def test_canais_ou_tipo_invalidos_levantam_validation_exception(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with self.assertRaises(ValidationException):
            Notificacao().business.disparar(
                destinatario_id=usuario.pk,
                tipo='',
                titulo='Título',
                corpo='Corpo',
            )
        with self.assertRaises(ValidationException):
            Notificacao().business.disparar(
                destinatario_id=usuario.pk,
                tipo='teste.invalido',
                titulo='Título',
                corpo='Corpo',
                canais=['sistema', 'telegram'],
            )
        with self.assertRaises(ValidationException):
            obter_canal('telegram')

    def test_destinatario_inexistente_levanta_not_found(self):
        with self.assertRaises(NotFoundException):
            Notificacao().business.disparar(
                destinatario_id=999999999,
                tipo='teste.inexistente',
                titulo='Título',
                corpo='Corpo',
            )

    def test_corrida_de_idempotencia_recupera_existente_sem_erro_de_transacao(self):
        usuario = _criar_usuario(self._proximo_cpf())
        chave = 'corrida:1'
        tipo = 'teste.corrida'
        existente = Notificacao.objects.create(
            destinatario=usuario,
            tipo=tipo,
            titulo='Existente',
            corpo='Corpo',
            chave_idempotencia=chave,
        )
        original = NotificacaoHelpers.obter_por_chave_idempotencia
        chamadas = {'n': 0}

        def fake(self, *args, **kwargs):
            chamadas['n'] += 1
            if chamadas['n'] == 1:
                return None
            return original(self, *args, **kwargs)

        with patch.object(NotificacaoHelpers, 'obter_por_chave_idempotencia', fake):
            with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
                with self.captureOnCommitCallbacks(execute=True):
                    resultado = Notificacao().business.disparar(
                        destinatario_id=usuario.pk,
                        tipo=tipo,
                        titulo='Novo título',
                        corpo='Novo corpo',
                        chave_idempotencia=chave,
                    )

        self.assertEqual(resultado.pk, existente.pk)
        self.assertEqual(
            Notificacao.objects.filter(destinatario=usuario, tipo=tipo).count(),
            1,
        )

    def test_rollback_do_emissor_nao_enfileira_task(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay') as delay_mock:
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        Notificacao().business.disparar(
                            destinatario_id=usuario.pk,
                            tipo='teste.rollback',
                            titulo='Título',
                            corpo='Corpo',
                        )
                        raise RuntimeError('rollback emissor')
                except RuntimeError:
                    pass

        self.assertEqual(Notificacao.objects.count(), 0)
        delay_mock.assert_not_called()

    @patch.object(
        EmailMultiAlternatives,
        'send',
        side_effect=smtplib.SMTPException('connection refused'),
    )
    def test_falha_smtp_tentativa_intermediaria_mantem_pendente(self, _send_mock):
        usuario = _criar_usuario(self._proximo_cpf(), email='falha@teste.local')
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.smtp_intermediaria',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        with self.assertRaises(SystemErrorException):
            Notificacao().business.processar_envio(envio.pk, ultima_tentativa=False)
        envio.refresh_from_db()
        self.assertEqual(envio.status, StatusEnvio.PENDENTE)
        self.assertEqual(envio.tentativas, 1)
        self.assertIn('SMTPException', envio.ultimo_erro)

    def test_processar_envio_inexistente_retorna_sem_erro(self):
        Notificacao().business.processar_envio(999999999)

    def test_processar_envio_bloqueia_linha_com_for_update(self):
        usuario = _criar_usuario(self._proximo_cpf())
        with patch('Notificacoes.notificacoes.tasks.enviar_envio_task.delay'):
            with self.captureOnCommitCallbacks(execute=True):
                notificacao = Notificacao().business.disparar(
                    destinatario_id=usuario.pk,
                    tipo='teste.lock',
                    titulo='Título',
                    corpo='Corpo',
                )

        envio = Envio.objects.get(notificacao=notificacao)
        with CaptureQueriesContext(connection) as ctx:
            Notificacao().business.processar_envio(envio.pk)
        sqls = ' '.join(q['sql'] for q in ctx.captured_queries).upper()
        self.assertIn('FOR UPDATE', sqls)
