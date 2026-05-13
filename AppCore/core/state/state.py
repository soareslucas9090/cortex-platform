class ModelInstanceState:
    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def pode_editar(self):
        raise NotImplementedError('O método pode_editar deve ser implementado na classe de estado')
    
    def pode_excluir(self):
        raise NotImplementedError('O método pode_excluir deve ser implementado na classe de estado')
