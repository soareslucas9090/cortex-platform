from AppCore.core.rules.rules import ModelInstanceRules


class AlunoRules(ModelInstanceRules):
    
    def can_create(self):
        # Additional checks can be added here if necessary
        return True

    def can_update(self):
        return True

    def can_delete(self):
        return True
