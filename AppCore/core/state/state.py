from django.core.exceptions import ImproperlyConfigured

from AppCore.core.exceptions.exceptions import BusinessRuleException


class ModelInstanceState:
    transicoes_permitidas = frozenset()
    status_choices_class = None

    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def atualizar_status(self, novo_status):
        if self.status_choices_class is None:
            raise ImproperlyConfigured(
                'status_choices_class não foi definido na classe de estado',
            )
        if novo_status not in self.status_choices_class.values:
            raise BusinessRuleException('Status inválido.')
        if novo_status not in self.transicoes_permitidas:
            raise BusinessRuleException(
                f'{self.object_instance._meta.verbose_name} não pode ser atualizado de '
                f'{self.object_instance.get_status_display()} para '
                f'{self.status_choices_class(novo_status).label}.'
            )
        self.object_instance.status = novo_status
        self.object_instance.save()
        self.object_instance._domain_state_instance = (
            self.object_instance.get_model_state_class()
        )
        return self.object_instance

    def pode_editar(self):
        raise NotImplementedError('O método pode_editar deve ser implementado na classe de estado')
    
    def pode_excluir(self):
        raise NotImplementedError('O método pode_excluir deve ser implementado na classe de estado')
