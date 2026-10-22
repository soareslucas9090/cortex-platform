from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import CanalEnvio, StatusEnvio


class Notificacao(
    ModelHelperMixin,
    ModelBusinessMixin,
    ModelRulesMixin,
    BasicModel,
):
    from .business import NotificacaoBusiness
    from .helpers import NotificacaoHelpers
    from .rules import NotificacaoRules

    business_class = NotificacaoBusiness
    helper_class = NotificacaoHelpers
    rules_class = NotificacaoRules

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        verbose_name='Destinatário',
    )
    tipo = models.CharField('Tipo', max_length=100, db_index=True)
    titulo = models.CharField('Título', max_length=255)
    corpo = models.TextField('Corpo')
    contexto = models.JSONField('Contexto', default=dict, blank=True)
    lida_em = models.DateTimeField('Lida em', null=True, blank=True)
    chave_idempotencia = models.CharField(
        'Chave de idempotência',
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['destinatario', 'tipo', 'chave_idempotencia'],
                condition=models.Q(chave_idempotencia__isnull=False),
                name='notificacao_destinatario_tipo_chave_unica',
            ),
        ]
        indexes = [
            models.Index(fields=['destinatario', '-created_at']),
            models.Index(fields=['destinatario', 'tipo']),
        ]

    def __str__(self):
        return f'{self.titulo} → {self.destinatario_id} ({self.tipo})'


class Envio(BasicModel):
    notificacao = models.ForeignKey(
        Notificacao,
        on_delete=models.CASCADE,
        related_name='envios',
        verbose_name='Notificação',
    )
    canal = models.CharField('Canal', max_length=20, choices=CanalEnvio.choices)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusEnvio.choices,
        default=StatusEnvio.PENDENTE,
    )
    destino = models.CharField('Destino', max_length=255, blank=True, default='')
    tentativas = models.PositiveSmallIntegerField('Tentativas', default=0)
    ultimo_erro = models.TextField('Último erro', blank=True, default='')
    enviado_em = models.DateTimeField('Enviado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Envio'
        verbose_name_plural = 'Envios'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_canal_display()} — {self.get_status_display()} (#{self.pk})'
