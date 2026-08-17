import logging

from django.apps import apps
from django.conf import settings
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class EmprestimoBusiness(ModelInstanceBusiness):

    def verificar_consulta(self, usuario):
        """Valida se o usuário autenticado pode consultar o empréstimo."""
        try:
            self.object_instance.rules.pode_consultar(usuario)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível consultar o empréstimo.', logger)

    def realizar_emprestimo(
        self,
        solicitante_id: int,
        conta_autenticada,
        recurso_ids: list,
        observacao: str = '',
        retirada_em=None,
        responsavel_id=None,
        responsavel=None,
        **kwargs,
    ):
        """Registra empréstimo multi-item com validação de elegibilidade e disponibilidade."""
        try:
            from .models import Emprestimo, ItemEmprestimo
            Recurso = apps.get_model('recursos', 'Recurso')
            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            self.object_instance.rules.pode_operar(conta_autenticada)
            if responsavel is None:
                responsavel = self.object_instance.rules.resolver_responsavel(
                    conta_autenticada,
                    responsavel_id=responsavel_id,
                )
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
            self.relancar_ou_erro_sistema(e, 'Não foi possível realizar o empréstimo.', logger)

    def devolver_itens(self, conta_autenticada, item_ids: list):
        """Devolve parcialmente itens do empréstimo."""
        try:
            self.object_instance.rules.pode_operar(conta_autenticada)
            self.object_instance.rules.pode_devolver_itens()
            itens = list(
                self.object_instance.itens.filter(pk__in=item_ids).select_related('recurso'),
            )
            self.object_instance.rules.validar_itens_para_devolucao(itens, item_ids)
            agora = timezone.now()
            for item in itens:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])
            return self.object_instance
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível devolver os itens do empréstimo.', logger)

    def trocar_titular(
        self,
        conta_autenticada,
        novo_solicitante_id: int,
        observacao: str = '',
        responsavel_id=None,
    ):
        """Devolve itens em aberto e abre novo empréstimo para outro solicitante."""
        try:
            self.object_instance.rules.pode_operar(conta_autenticada)
            self.object_instance.rules.pode_trocar_titular()
            responsavel = self.object_instance.rules.resolver_responsavel(
                conta_autenticada,
                responsavel_id=responsavel_id,
            )
            itens_abertos = list(
                self.object_instance.itens.filter(
                    devolvido_em__isnull=True,
                ).select_related('recurso'),
            )
            recurso_ids = [item.recurso_id for item in itens_abertos]
            agora = timezone.now()
            for item in itens_abertos:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])
            from .models import Emprestimo
            return Emprestimo().business.realizar_emprestimo(
                solicitante_id=novo_solicitante_id,
                conta_autenticada=conta_autenticada,
                responsavel=responsavel,
                recurso_ids=recurso_ids,
                observacao=observacao,
                retirada_em=agora,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível trocar o titular do empréstimo.', logger)
