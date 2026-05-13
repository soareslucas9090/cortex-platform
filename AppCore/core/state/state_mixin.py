class ModelStateMixin:
    _state = None
    state_class_builder = None

    @property
    def state(self):
        if not self._state:
            self._state = self.get_model_state_class()

        return self._state

    def get_model_state_class(self):
        if not self.state_class_builder:
            raise ValueError('state_class_builder não foi definido no model')

        return self.state_class_builder.get(self.status)(object_instance=self)
    
    def set_state(self, new_state):
        if not self.state_class_builder:
            raise ValueError('state_class_builder não foi definido no model')
        
        self.status = new_state
        self.save()
        self._state = self.get_model_state_class()
