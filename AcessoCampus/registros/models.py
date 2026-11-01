from django.conf import settings
from django.db import models
from django.utils import timezone

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import ResultadoRegistroAcesso


class RegistroAcesso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import RegistroAcessoBusiness
    from .helpers import RegistroAcessoHelpers
    from .rules import RegistroAcessoRules

    business_class = RegistroAcessoBusiness
    helper_class = RegistroAcessoHelpers
    rules_class = RegistroAcessoRules

    evento = models.OneToOneField(
        "acesso_campus_eventos.EventoAcesso",
        on_delete=models.PROTECT,
        related_name="registro",
        verbose_name="Evento",
    )
    resultado = models.IntegerField(
        "Resultado",
        choices=ResultadoRegistroAcesso.choices,
        default=ResultadoRegistroAcesso.REALIZADO,
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="registros_acesso_como_responsavel",
        verbose_name="Responsável físico",
    )
    operado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="registros_acesso_operados",
        verbose_name="Conta operadora",
    )
    registrado_em = models.DateTimeField("Registrado em", default=timezone.now)
    observacao = models.TextField("Observação", blank=True)

    class Meta:
        verbose_name = "Registro de acesso"
        verbose_name_plural = "Registros de acesso"
        ordering = ["-registrado_em"]

    def __str__(self):
        return f"{self.evento} — {self.get_resultado_display()}"
