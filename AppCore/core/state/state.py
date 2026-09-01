class ModelInstanceState:
    transicoes_permitidas = frozenset()
    status_choices_class = None

    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def atualizar_status(self, novo_status):
        if novo_status not in self.transicoes_permitidas:
            raise ValueError(
                f'{self.object_instance._meta.verbose_name} não pode ser atualizado de '
                f'{self.object_instance.get_status_display()} para '
                f'{self.status_choices_class(novo_status).label}.'
            )
        self.object_instance.status = novo_status
        self.object_instance.save()

    def pode_editar(self):
        raise NotImplementedError('O método pode_editar deve ser implementado na classe de estado')
    
    def pode_excluir(self):
        raise NotImplementedError('O método pode_excluir deve ser implementado na classe de estado')
