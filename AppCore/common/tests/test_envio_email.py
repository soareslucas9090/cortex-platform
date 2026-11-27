from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from AppCore.core.exceptions.exceptions import SystemErrorException, ValidationException


class EnviarEmailSimplesTests(SimpleTestCase):
    @override_settings(RESEND_API_KEY='re_test')
    @patch('AppCore.common.util.util.resend.Emails.send')
    def test_envia_html_via_resend(self, mock_send):
        import resend

        from AppCore.common.util.util import enviar_email_simples

        enviar_email_simples(
            'Assunto',
            'texto plano',
            'de@x.com',
            ['para@x.com'],
            '<p>oi</p>',
        )

        mock_send.assert_called_once_with({
            'from': 'de@x.com',
            'to': ['para@x.com'],
            'subject': 'Assunto',
            'html': '<p>oi</p>',
        })
        self.assertEqual(resend.api_key, 're_test')

    @override_settings(RESEND_API_KEY='re_test')
    @patch('AppCore.common.util.util.resend.Emails.send', side_effect=RuntimeError('falha api'))
    def test_falha_resend_levanta_system_error_generico(self, mock_send):
        from AppCore.common.util.util import enviar_email_simples

        with self.assertRaises(SystemErrorException) as ctx:
            enviar_email_simples('A', 't', 'de@x.com', ['p@x.com'], '<p>x</p>')

        self.assertEqual(str(ctx.exception), 'Erro ao enviar email.')
        mock_send.assert_called_once()


class SendSimpleEmailTaskTests(SimpleTestCase):
    def test_atributos_de_retry(self):
        from AppCore.common.tasks import send_simple_email_task

        self.assertEqual(send_simple_email_task.max_retries, 4)
        self.assertEqual(send_simple_email_task.default_retry_delay, 30)

    @patch('AppCore.common.tasks.enviar_email_simples', side_effect=Exception('falha'))
    def test_task_chama_retry_com_countdown(self, mock_enviar):
        from AppCore.common.tasks import send_simple_email_task

        sentinel = RuntimeError('retry disparado')
        with patch.object(send_simple_email_task, 'retry', side_effect=sentinel) as mock_retry:
            with self.assertRaises(RuntimeError) as ctx:
                send_simple_email_task.run(
                    'assunto',
                    'texto',
                    'de@x.com',
                    ['para@x.com'],
                    '<p>oi</p>',
                )

        self.assertIs(ctx.exception, sentinel)
        mock_enviar.assert_called_once_with(
            'assunto',
            'texto',
            'de@x.com',
            ['para@x.com'],
            '<p>oi</p>',
        )
        mock_retry.assert_called_once()
        kwargs = mock_retry.call_args.kwargs
        self.assertEqual(kwargs['countdown'], 30)
        self.assertIsInstance(kwargs['exc'], Exception)
        self.assertEqual(str(kwargs['exc']), 'falha')


class EnviarEmailFacadeTests(SimpleTestCase):
    @override_settings(FROM_EMAIL_NOREPLY='noreply@cortex.test')
    @patch('AppCore.common.envio_email.send_simple_email_task.delay')
    def test_enfileira_com_destinatario_string(self, mock_delay):
        from AppCore.common.envio_email import enviar_email

        enviar_email('user@test.com', 'Olá', '<p>oi</p>', texto='plain')

        mock_delay.assert_called_once_with(
            'Olá',
            'plain',
            'noreply@cortex.test',
            ['user@test.com'],
            '<p>oi</p>',
        )

    @override_settings(FROM_EMAIL_NOREPLY='noreply@cortex.test')
    @patch('AppCore.common.envio_email.send_simple_email_task.delay')
    def test_remetente_explicito_sobrescreve_padrao(self, mock_delay):
        from AppCore.common.envio_email import enviar_email

        enviar_email(['a@b.com'], 'S', '<p>h</p>', remetente=' custom@x.com ')

        mock_delay.assert_called_once_with(
            'S',
            '',
            'custom@x.com',
            ['a@b.com'],
            '<p>h</p>',
        )

    @override_settings(FROM_EMAIL_NOREPLY='noreply@cortex.test')
    @patch('AppCore.common.envio_email.send_simple_email_task.delay')
    def test_destinatario_vazio_levanta_validacao(self, mock_delay):
        from AppCore.common.envio_email import enviar_email

        with self.assertRaises(ValidationException):
            enviar_email('', 'S', '<p>h</p>')
        with self.assertRaises(ValidationException):
            enviar_email([], 'S', '<p>h</p>')
        mock_delay.assert_not_called()

    @override_settings(FROM_EMAIL_NOREPLY='')
    @patch('AppCore.common.envio_email.send_simple_email_task.delay')
    def test_remetente_padrao_vazio_levanta_validacao(self, mock_delay):
        from AppCore.common.envio_email import enviar_email

        with self.assertRaises(ValidationException):
            enviar_email('u@t.com', 'S', '<p>h</p>')
        mock_delay.assert_not_called()

    @override_settings(FROM_EMAIL_NOREPLY='noreply@cortex.test')
    @patch(
        'AppCore.common.envio_email.send_simple_email_task.delay',
        side_effect=ConnectionError('redis'),
    )
    def test_falha_ao_enfileirar_levanta_system_error(self, mock_delay):
        from AppCore.common.envio_email import enviar_email

        with self.assertRaises(SystemErrorException) as ctx:
            enviar_email('u@t.com', 'S', '<p>h</p>')

        self.assertEqual(str(ctx.exception), 'Não foi possível enfileirar o e-mail.')
