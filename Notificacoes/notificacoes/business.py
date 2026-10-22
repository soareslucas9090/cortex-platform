import logging

from django.db import IntegrityError, transaction

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


def _deduplicar_canais(canais):
    vistos = set()
    resultado = []
    for canal in canais:
        if canal not in vistos:
            vistos.add(canal)
            resultado.append(canal)
    return resultado


class NotificacaoBusiness(ModelInstanceBusiness):

    def disparar(
        self,
        destinatario_id,
        tipo,
        titulo,
        corpo,
        canais=None,
        contexto=None,
        chave_idempotencia=None,
    ):
        try:
            from .choices import CanalEnvio, CanalSistema, StatusEnvio
            from .models import Envio, Notificacao
            from .tasks import enviar_envio_task

            if canais is None:
                canais = [CanalSistema, CanalEnvio.EMAIL]
            canais = _deduplicar_canais(list(canais))

            self.object_instance.rules.validar_disparo(
                destinatario_id,
                tipo,
                titulo,
                corpo,
                canais,
            )

            from Identidade.usuarios.models import Usuario

            Usuario.objects.get(pk=destinatario_id)

            chave_normalizada = (chave_idempotencia or '').strip() or None

            if chave_normalizada:
                existente = Notificacao.objects.filter(
                    destinatario_id=destinatario_id,
                    tipo=tipo,
                    chave_idempotencia=chave_normalizada,
                ).first()
                if existente is not None:
                    return existente

            contexto_final = contexto if contexto is not None else {}

            try:
                notificacao = Notificacao.objects.create(
                    destinatario_id=destinatario_id,
                    tipo=tipo,
                    titulo=titulo,
                    corpo=corpo,
                    contexto=contexto_final,
                    chave_idempotencia=chave_normalizada,
                )
            except IntegrityError:
                if chave_normalizada:
                    return Notificacao.objects.get(
                        destinatario_id=destinatario_id,
                        tipo=tipo,
                        chave_idempotencia=chave_normalizada,
                    )
                raise

            for canal in canais:
                if canal == CanalSistema:
                    continue
                if canal == CanalEnvio.EMAIL:
                    envio = Envio.objects.create(
                        notificacao=notificacao,
                        canal=CanalEnvio.EMAIL,
                        status=StatusEnvio.PENDENTE,
                    )
                    transaction.on_commit(
                        lambda eid=envio.pk: enviar_envio_task.delay(eid)
                    )
                elif canal in (CanalEnvio.SMS, CanalEnvio.WHATSAPP):
                    Envio.objects.create(
                        notificacao=notificacao,
                        canal=canal,
                        status=StatusEnvio.IGNORADO,
                        ultimo_erro='Canal ainda não configurado.',
                    )

            return notificacao
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível disparar a notificação.',
                logger,
            )

    def processar_envio(self, envio_id):
        try:
            from .canais import obter_canal
            from .choices import StatusEnvio
            from .models import Envio

            envio = Envio.objects.select_related(
                'notificacao',
                'notificacao__destinatario',
            ).get(pk=envio_id)

            if envio.status in (StatusEnvio.ENVIADO, StatusEnvio.IGNORADO):
                return

            envio.tentativas += 1
            envio.save(update_fields=['tentativas', 'updated_at'])

            adaptador = obter_canal(envio.canal)
            adaptador.enviar(envio)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível processar o envio da notificação.',
                logger,
            )
