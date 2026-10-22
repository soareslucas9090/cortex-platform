import html

from django.conf import settings
from django.utils import timezone

from AppCore.common.util.util import enviar_email_simples

from .choices import CanalEnvio, StatusEnvio


class CanalEmail:

    def enviar(self, envio):
        notificacao = envio.notificacao
        destino = notificacao.helper.resolver_email_destinatario(notificacao.destinatario)

        if not destino:
            envio.status = StatusEnvio.IGNORADO
            envio.ultimo_erro = 'Destinatário sem e-mail.'
            envio.save(update_fields=['status', 'ultimo_erro', 'updated_at'])
            return

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

        envio.status = StatusEnvio.ENVIADO
        envio.destino = destino
        envio.enviado_em = timezone.now()
        envio.ultimo_erro = ''
        envio.save(
            update_fields=[
                'status',
                'destino',
                'enviado_em',
                'ultimo_erro',
                'updated_at',
            ]
        )


class CanalSms:

    def enviar(self, envio):
        envio.status = StatusEnvio.IGNORADO
        envio.ultimo_erro = 'Canal SMS ainda não configurado.'
        envio.save(update_fields=['status', 'ultimo_erro', 'updated_at'])


class CanalWhatsapp:

    def enviar(self, envio):
        envio.status = StatusEnvio.IGNORADO
        envio.ultimo_erro = 'Canal WhatsApp ainda não configurado.'
        envio.save(update_fields=['status', 'ultimo_erro', 'updated_at'])


def obter_canal(canal):
    if canal == CanalEnvio.EMAIL:
        return CanalEmail()
    if canal == CanalEnvio.SMS:
        return CanalSms()
    if canal == CanalEnvio.WHATSAPP:
        return CanalWhatsapp()
    raise ValueError(f'Canal desconhecido: {canal}')
