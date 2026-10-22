from unittest.mock import patch

from django.test import TestCase

from AppCore.core.exceptions.exceptions import ValidationException
from Identidade.contatos.models import Contato
from Identidade.usuarios.models import Usuario

from Notificacoes.notificacoes.choices import CanalEnvio, StatusEnvio
from Notificacoes.notificacoes.models import Envio, Notificacao


def _criar_usuario(cpf, email=None, nome='Usuário teste'):
    kwargs = {'cpf': cpf, 'password': 'Senha@123', 'nome': nome}
    if email is not None:
        kwargs['email'] = email
    return Usuario.objects.create_user(**kwargs)


class DisparoNotificacaoTestCase(TestCase):
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

    @patch(
        'Notificacoes.notificacoes.business.NotificacaoBusiness.processar_envio',
        side_effect=RuntimeError('falha smtp'),
    )
    def test_task_esgota_retries_e_marca_falhou(self, _processar_mock):
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
        self.assertEqual(envio.ultimo_erro, 'Falha ao enviar notificação.')
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
