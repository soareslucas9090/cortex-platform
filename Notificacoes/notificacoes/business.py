import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

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
                existente = self.object_instance.helper.obter_por_chave_idempotencia(
                    destinatario_id,
                    tipo,
                    chave_normalizada,
                )
                if existente is not None:
                    return existente

            contexto_final = contexto if contexto is not None else {}

            try:
                with transaction.atomic():
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
                    existente = self.object_instance.helper.obter_por_chave_idempotencia(
                        destinatario_id,
                        tipo,
                        chave_normalizada,
                    )
                    if existente is not None:
                        return existente
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

    def processar_envio(self, envio_id, ultima_tentativa=False):
        try:
            from .canais import obter_canal
            from .choices import StatusEnvio

            erro_para_relancar = None
            with transaction.atomic():
                envio = self.object_instance.helper.obter_envio_bloqueado(envio_id)
                if envio is None:
                    logger.warning(
                        'Envio %s não encontrado para envio assíncrono.',
                        envio_id,
                    )
                    return
                if envio.status in (StatusEnvio.ENVIADO, StatusEnvio.IGNORADO):
                    return

                envio.tentativas += 1
                try:
                    resultado = obter_canal(envio.canal).enviar(envio)
                    envio.status = resultado.status
                    if resultado.destino:
                        envio.destino = resultado.destino
                    envio.ultimo_erro = resultado.mensagem
                    if resultado.status == StatusEnvio.ENVIADO:
                        envio.enviado_em = timezone.now()
                except Exception as e:
                    envio.ultimo_erro = self.object_instance.helper.resumir_erro(e)
                    if ultima_tentativa:
                        envio.status = StatusEnvio.FALHOU
                    else:
                        envio.status = StatusEnvio.PENDENTE
                    erro_para_relancar = e

                envio.save(
                    update_fields=[
                        'status',
                        'destino',
                        'tentativas',
                        'ultimo_erro',
                        'enviado_em',
                        'updated_at',
                    ]
                )

            if erro_para_relancar is not None:
                raise erro_para_relancar
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível processar o envio da notificação.',
                logger,
            )

    def listar_para_usuario(self, usuario, lida=None, tipo=None):
        try:
            queryset = self.object_instance.helper.listar_do_destinatario(usuario.pk)
            if lida is True:
                queryset = queryset.filter(lida_em__isnull=False)
            elif lida is False:
                queryset = queryset.filter(lida_em__isnull=True)
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            return queryset
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível listar as notificações do usuário.',
                logger,
            )

    def contar_nao_lidas(self, destinatario_id):
        try:
            return self.object_instance.helper.contar_nao_lidas(destinatario_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível contar as notificações não lidas.',
                logger,
            )

    def marcar_lida(self):
        try:
            if self.object_instance.lida_em is None:
                self.object_instance.lida_em = timezone.now()
                self.object_instance.save(update_fields=['lida_em', 'updated_at'])
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível marcar a notificação como lida.',
                logger,
            )

    def marcar_todas_lidas(self, destinatario_id):
        try:
            agora = timezone.now()
            queryset = self.object_instance.helper.listar_do_destinatario(destinatario_id).filter(
                lida_em__isnull=True,
            )
            return queryset.update(lida_em=agora, updated_at=agora)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível marcar todas as notificações como lidas.',
                logger,
            )
