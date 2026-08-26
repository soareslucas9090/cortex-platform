from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class StatusImportacao(models.TextChoices):
    EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    ERRO = 'ERRO', 'Erro'


class ImportacaoLote(ModelRulesMixin, ModelBusinessMixin, BasicModel):
    from .business import ImportacaoLoteBusiness
    from .rules import ImportacaoLoteRules

    business_class = ImportacaoLoteBusiness
    rules_class = ImportacaoLoteRules

    arquivo = models.FileField(
        'Arquivo de Importação',
        upload_to='importacoes/infraestrutura/%Y/%m/%d/',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusImportacao.choices,
        default=StatusImportacao.EM_ANDAMENTO,
    )
    total_linhas = models.IntegerField('Total de Linhas', default=0)
    linhas_processadas = models.IntegerField('Linhas Processadas', default=0)
    resultado_json = models.JSONField('Resultado/Erros', null=True, blank=True)

    class Meta:
        verbose_name = 'Importação de Lote de Infraestrutura'
        verbose_name_plural = 'Importações de Lote de Infraestrutura'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['status'],
                condition=models.Q(status=StatusImportacao.EM_ANDAMENTO),
                name='importacoes_infraestrutura_lote_unico_em_andamento',
            ),
        ]

    def __str__(self):
        return (
            f'Importação {self.pk} - {self.get_status_display()} '
            f'({self.linhas_processadas}/{self.total_linhas})'
        )
