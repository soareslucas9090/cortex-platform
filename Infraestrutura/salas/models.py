from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Sala(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import SalaBusiness
    from .helpers import SalaHelpers

    business_class = SalaBusiness
    helper_class = SalaHelpers

    bloco = models.ForeignKey(
        'blocos.Bloco',
        on_delete=models.PROTECT,
        related_name='salas',
        verbose_name='Bloco',
    )
    nome = models.CharField('Nome', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        ordering = ['bloco', 'nome']
        constraints = [
            models.UniqueConstraint(
                fields=['bloco', 'nome'],
                name='salas_sala_bloco_nome_unico',
            ),
        ]

    def __str__(self):
        return f'{self.bloco} — {self.nome}'


class SalaSetor(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import SalaSetorBusiness
    from .helpers import SalaSetorHelpers

    business_class = SalaSetorBusiness
    helper_class = SalaSetorHelpers

    sala = models.ForeignKey(
        'salas.Sala',
        on_delete=models.PROTECT,
        related_name='setores_vinculados',
        verbose_name='Sala',
    )
    setor = models.ForeignKey(
        'setores.Setor',
        on_delete=models.PROTECT,
        related_name='salas_vinculadas',
        verbose_name='Setor',
    )

    class Meta:
        verbose_name = 'Vínculo Sala–Setor'
        verbose_name_plural = 'Vínculos Sala–Setor'
        ordering = ['sala', 'setor']
        constraints = [
            models.UniqueConstraint(
                fields=['sala', 'setor'],
                name='salas_salasetor_sala_setor_unico',
            ),
        ]

    def __str__(self):
        return f'{self.sala} ↔ {self.setor}'
