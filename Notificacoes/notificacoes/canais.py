import html

from django.conf import settings

from AppCore.common.util.util import enviar_email_simples
from AppCore.core.exceptions.exceptions import ValidationException

from .choices import CanalEnvio, StatusEnvio


class ResultadoEnvio:

    def __init__(self, status, destino='', mensagem=''):
        self.status = status
        self.destino = destino
        self.mensagem = mensagem


class CanalEmail:

    def enviar(self, envio):
        notificacao = envio.notificacao
        destino = notificacao.helper.resolver_email_destinatario(notificacao.destinatario)

        if not destino:
            return ResultadoEnvio(
                status=StatusEnvio.IGNORADO,
                mensagem='Destinatário sem e-mail.',
            )

        from_email = (
            getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            or getattr(settings, 'EMAIL_HOST_USER', None)
            or 'noreply@localhost'
        )
        html_content = f'<p>{html.escape(notificacao.corpo)}</p>'

        enviar_email_simples(
            notificacao.titulo,
            notificacao.corpo,
            from_email,
            [destino],
            html_content,
        )

        return ResultadoEnvio(status=StatusEnvio.ENVIADO, destino=destino)


class CanalSms:

    def enviar(self, envio):
        return ResultadoEnvio(
            status=StatusEnvio.IGNORADO,
            mensagem='Canal SMS ainda não configurado.',
        )


class CanalWhatsapp:

    def enviar(self, envio):
        return ResultadoEnvio(
            status=StatusEnvio.IGNORADO,
            mensagem='Canal WhatsApp ainda não configurado.',
        )


def obter_canal(canal):
    if canal == CanalEnvio.EMAIL:
        return CanalEmail()
    if canal == CanalEnvio.SMS:
        return CanalSms()
    if canal == CanalEnvio.WHATSAPP:
        return CanalWhatsapp()
    raise ValidationException(f'Canal de envio inválido: {canal}.')
