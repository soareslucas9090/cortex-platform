class ModelStateMixin:
    _domain_state_instance = None
    state_class_builder = None

    @property
    def state(self):
        if not self._domain_state_instance:
            self._domain_state_instance = self.get_model_state_class()

        return self._domain_state_instance

    def get_model_state_class(self):
        if not self.state_class_builder:
            raise ValueError('state_class_builder não foi definido no model')

        return self.state_class_builder.get(self.status)(object_instance=self)
    
    def set_state(self, new_state):
        if not self.state_class_builder:
            raise ValueError('state_class_builder não foi definido no model')
        
        self.status = new_state
        self.save()
        self._domain_state_instance = self.get_model_state_class()
