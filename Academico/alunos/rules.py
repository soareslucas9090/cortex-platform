from AppCore.core.rules.rules import ModelInstanceRules


class AlunoRules(ModelInstanceRules):

    def can_create(self):
        return True

    def can_update(self):
        return True

    def can_delete(self):
        return True
