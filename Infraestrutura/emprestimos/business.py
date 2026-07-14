import logging

from django.apps import apps
from django.conf import settings
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    BusinessRuleException,
    SystemErrorException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class EmprestimoBusiness(ModelInstanceBusiness):

    def realizar_emprestimo(
        self,
        solicitante_id: int,
        responsavel,
        recurso_ids: list,
        observacao: str = '',
        retirada_em=None,
        **kwargs,
    ):
        """Registra empréstimo multi-item com validação de elegibilidade e disponibilidade."""
        from .models import Emprestimo, ItemEmprestimo

        Recurso = apps.get_model('recursos', 'Recurso')
        Usuario = apps.get_model(settings.AUTH_USER_MODEL)

        self.object_instance.rules.pode_operar(responsavel)
        recursos = list(
            Recurso.objects.filter(pk__in=recurso_ids).select_related('sala'),
        )
        self.object_instance.rules.validar_recursos_informados(recurso_ids, recursos)
        self.object_instance.rules.validar_solicitante_ativo(solicitante_id)

        solicitante = Usuario.objects.get(pk=solicitante_id)
        for recurso in recursos:
            self.object_instance.rules.validar_recurso_disponivel(recurso)
            self.object_instance.rules.validar_elegibilidade_solicitante_para_recurso(
                solicitante,
                recurso,
            )

        momento_retirada = retirada_em or timezone.now()
        try:
            emprestimo = Emprestimo.objects.create(
                solicitante=solicitante,
                responsavel=responsavel,
                retirada_em=momento_retirada,
                observacao=observacao,
                **kwargs,
            )
            for recurso in recursos:
                ItemEmprestimo.objects.create(
                    emprestimo=emprestimo,
                    recurso=recurso,
                )
            return emprestimo
        except Exception as e:
            logger.exception('Erro ao realizar empréstimo: %s', e)
            raise SystemErrorException('Não foi possível realizar o empréstimo.')

    def devolver_itens(self, responsavel, item_ids: list):
        """Devolve parcialmente itens do empréstimo."""
        self.object_instance.rules.pode_operar(responsavel)
        self.object_instance.rules.pode_devolver_itens()
        itens = list(
            self.object_instance.itens.filter(pk__in=item_ids).select_related('recurso'),
        )
        self.object_instance.rules.validar_itens_para_devolucao(itens, item_ids)

        agora = timezone.now()
        try:
            for item in itens:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])
            return self.object_instance
        except Exception as e:
            logger.exception('Erro ao devolver itens do empréstimo: %s', e)
            raise SystemErrorException('Não foi possível devolver os itens do empréstimo.')

    def trocar_titular(self, responsavel, novo_solicitante_id: int, observacao: str = ''):
        """Devolve itens em aberto e abre novo empréstimo para outro solicitante."""
        self.object_instance.rules.pode_operar(responsavel)
        self.object_instance.rules.pode_trocar_titular()

        itens_abertos = list(
            self.object_instance.itens.filter(
                devolvido_em__isnull=True,
            ).select_related('recurso'),
        )
        recurso_ids = [item.recurso_id for item in itens_abertos]
        agora = timezone.now()

        try:
            for item in itens_abertos:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])

            from .models import Emprestimo

            return Emprestimo().business.realizar_emprestimo(
                solicitante_id=novo_solicitante_id,
                responsavel=responsavel,
                recurso_ids=recurso_ids,
                observacao=observacao,
                retirada_em=agora,
            )
        except (BusinessRuleException, ValidationException):
            raise
        except Exception as e:
            logger.exception('Erro ao trocar titular do empréstimo: %s', e)
            raise SystemErrorException('Não foi possível trocar o titular do empréstimo.')
